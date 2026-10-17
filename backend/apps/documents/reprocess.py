"""Process every document again, e.g. after changing the embedding model: python -m apps.documents.reprocess"""

import asyncio

from sqlalchemy import select

from core.db import SessionLocal

from .models import Document
from .services import process_document


async def reprocess_all():
    async with SessionLocal() as db:
        documents = list(await db.scalars(select(Document).order_by(Document.id)))
        for document in documents:
            await process_document(db, document)
            print(f'{document.id} {document.title}: {document.status}, {document.chunks_count} chunks')


if __name__ == '__main__':
    asyncio.run(reprocess_all())
