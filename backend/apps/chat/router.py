from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from apps.users.dependencies import CurrentUser
from core.db import DBSession
from core.llm import LLM, get_llm

from . import services
from .models import Conversation
from .schemas import ConversationListItem, ConversationRead, QuestionCreate

router = APIRouter(prefix='/conversations', tags=['chat'])


async def get_own_conversation(db, conversation_id: int, user) -> Conversation:
    conversation = await db.get(Conversation, conversation_id)
    if conversation is None or conversation.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Conversation not found')
    return conversation


@router.post('', response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(db: DBSession, user: CurrentUser):
    conversation = Conversation(owner_id=user.id, messages=[])
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.get('', response_model=list[ConversationListItem])
async def list_conversations(db: DBSession, user: CurrentUser):
    return await services.list_conversations(db, user)


@router.get('/{conversation_id}', response_model=ConversationRead)
async def get_conversation(conversation_id: int, db: DBSession, user: CurrentUser):
    return await get_own_conversation(db, conversation_id, user)


@router.delete('/{conversation_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: int, db: DBSession, user: CurrentUser):
    await db.delete(await get_own_conversation(db, conversation_id, user))
    await db.commit()


@router.post('/{conversation_id}/messages')
async def ask(
    conversation_id: int,
    data: QuestionCreate,
    db: DBSession,
    user: CurrentUser,
    llm: Annotated[LLM, Depends(get_llm)],
):
    """Answer as a stream of server-sent events: `citation`, `text` pieces, then `done`."""
    conversation = await get_own_conversation(db, conversation_id, user)
    events = services.ask(db, llm, user, conversation, data.question, data.document_ids)
    return StreamingResponse(events, media_type='text/event-stream', headers={'Cache-Control': 'no-cache'})
