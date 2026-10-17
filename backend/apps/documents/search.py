from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.users.models import User
from core.embeddings import embed_query

from .models import Chunk, Document, DocumentStatus


@dataclass
class Hit:
    chunk_id: int
    document_id: int
    document_title: str
    page: int | None
    text: str
    score: float  # cosine similarity, 1 is identical


async def search(
    db: AsyncSession, user: User, query: str, limit: int = 5, document_ids: list[int] | None = None
) -> list[Hit]:
    vector = await embed_query(query)
    distance = Chunk.embedding.cosine_distance(vector)
    stmt = (
        select(Chunk, Document.title, distance.label('distance'))
        .join(Document, Document.id == Chunk.document_id)
        # Only the user's own, fully processed documents
        .where(Document.owner_id == user.id, Document.status == DocumentStatus.READY)
        .order_by(distance)
        .limit(limit)
    )
    if document_ids:
        stmt = stmt.where(Document.id.in_(document_ids))

    return [
        Hit(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            document_title=title,
            page=chunk.page,
            text=chunk.text,
            score=round(1 - dist, 4),
        )
        for chunk, title, dist in await db.execute(stmt)
    ]
