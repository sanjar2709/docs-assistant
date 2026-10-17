"""Answering questions with Claude, grounded in the retrieved chunks.

Chunks go to Claude as documents with citations turned on: one document per source file,
one content block per chunk. Each citation Claude returns points at a document and a block,
which maps straight back to a chunk, so the UI can show the exact file, page and quote.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Protocol

import anthropic

from core import settings

SYSTEM_PROMPT = """You answer questions about the user's documents.

Use only the documents in the message. If there are none, or they don't contain the answer,
say that the answer isn't in the user's documents, and don't guess.
Answer in the language of the question, even if the documents are in another language.
Keep answers short and to the point; use a list only when the answer is naturally a list."""


@dataclass
class Source:
    """One retrieved chunk, as it is sent to the model."""

    chunk_id: int
    document_id: int
    document_title: str
    page: int | None
    text: str


@dataclass
class AnswerEvent:
    type: str  # "text", "citation", "done" or "refused"
    text: str = ''
    source: Source | None = None
    cited_text: str = ''
    usage: dict = field(default_factory=dict)


class LLM(Protocol):
    def answer(self, question: str, history: list[dict], sources: list[Source]) -> AsyncIterator[AnswerEvent]: ...


def group_by_document(sources: list[Source]) -> list[list[Source]]:
    groups: dict[int, list[Source]] = {}
    for source in sources:
        groups.setdefault(source.document_id, []).append(source)
    return list(groups.values())


def build_user_content(question: str, sources: list[Source]) -> tuple[list[dict], list[list[Source]]]:
    documents = group_by_document(sources)
    content = [
        {
            'type': 'document',
            'source': {'type': 'content', 'content': [{'type': 'text', 'text': s.text} for s in group]},
            'title': group[0].document_title,
            'citations': {'enabled': True},
        }
        for group in documents
    ]
    content.append({'type': 'text', 'text': question})
    return content, documents


class ClaudeLLM:
    def __init__(self, client: anthropic.AsyncAnthropic | None = None):
        self.client = client or anthropic.AsyncAnthropic()

    async def answer(self, question: str, history: list[dict], sources: list[Source]) -> AsyncIterator[AnswerEvent]:
        content, documents = build_user_content(question, sources)
        async with self.client.beta.messages.stream(
            model=settings.CLAUDE_MODEL,
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=[*history, {'role': 'user', 'content': content}],
            # A short grounded answer doesn't need deep reasoning; low effort keeps it fast and cheap
            output_config={'effort': 'low'},
            # If the model declines, the API retries on a fallback model inside the same request
            betas=['server-side-fallback-2026-07-01'],
            fallbacks='default',
        ) as stream:
            async for event in stream:
                if event.type != 'content_block_delta':
                    continue
                if event.delta.type == 'text_delta':
                    yield AnswerEvent(type='text', text=event.delta.text)
                elif event.delta.type == 'citations_delta':
                    citation = event.delta.citation
                    if citation.type != 'content_block_location':
                        continue
                    group = documents[citation.document_index]
                    for block in range(citation.start_block_index, citation.end_block_index):
                        if block < len(group):
                            yield AnswerEvent(type='citation', source=group[block], cited_text=citation.cited_text)

            message = await stream.get_final_message()
            if message.stop_reason == 'refusal':
                yield AnswerEvent(type='refused')
            usage = {'input_tokens': message.usage.input_tokens, 'output_tokens': message.usage.output_tokens}
            yield AnswerEvent(type='done', usage=usage)


def get_llm() -> LLM:
    return ClaudeLLM()
