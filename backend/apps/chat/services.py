import json
from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.documents.search import search
from apps.users.models import User
from core import settings
from core.llm import LLM, Source

from .models import Conversation, Message, Role

REFUSED = "Sorry, I can't answer this question."


def sse(event: str, data) -> str:
    return f'event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n'


async def list_conversations(db: AsyncSession, user: User) -> list[Conversation]:
    query = select(Conversation).where(Conversation.owner_id == user.id).order_by(Conversation.updated_at.desc())
    return list(await db.scalars(query))


def history_for_model(conversation: Conversation) -> list[dict]:
    # Earlier turns as plain text; the documents themselves are only sent with the new question
    messages = conversation.messages[-settings.HISTORY_MESSAGES:]
    return [{'role': m.role.value, 'content': m.content} for m in messages]


async def ask(
    db: AsyncSession, llm: LLM, user: User, conversation: Conversation, question: str, document_ids=None
) -> AsyncIterator[str]:
    """Streams the answer as server-sent events: citation*, text*, then done with the saved message."""
    history = history_for_model(conversation)
    db.add(Message(conversation_id=conversation.id, role=Role.USER, content=question, citations=[]))
    if conversation.title == 'New chat':
        conversation.title = question[:80]
    await db.commit()

    hits = await search(db, user, question, settings.RETRIEVAL_LIMIT, document_ids)
    sources = [
        Source(h.chunk_id, h.document_id, h.document_title, h.page, h.text)
        for h in hits
        if h.score >= settings.MIN_RELEVANCE
    ]

    # With no relevant chunks the model still gets the question: it then says "not in your documents"
    # in the language the user asked in, which a fixed message couldn't do
    answer, citations, seen = '', [], set()
    async for event in llm.answer(question, history, sources):
        if event.type == 'text':
            answer += event.text
            yield sse('text', {'text': event.text})
        elif event.type == 'citation' and event.source.chunk_id not in seen:
            seen.add(event.source.chunk_id)
            citation = {
                'chunk_id': event.source.chunk_id,
                'document_id': event.source.document_id,
                'document_title': event.source.document_title,
                'page': event.source.page,
                'cited_text': event.cited_text,
            }
            citations.append(citation)
            yield sse('citation', citation)
        elif event.type == 'refused':
            answer = answer or REFUSED
            yield sse('text', {'text': REFUSED})

    message = Message(conversation_id=conversation.id, role=Role.ASSISTANT, content=answer, citations=citations)
    db.add(message)
    await db.commit()
    yield sse('done', {'message_id': message.id, 'conversation_id': conversation.id})
