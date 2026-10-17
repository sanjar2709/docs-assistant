import asyncio
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.users.models import User
from core import settings
from core.embeddings import embed_passages

from .chunking import chunk_pages
from .extract import SUPPORTED_TYPES, ExtractionError, extract_pages
from .models import Chunk, Document, DocumentStatus


class UploadError(Exception):
    pass


def guess_type(upload: UploadFile) -> str:
    # Browsers send text/markdown inconsistently, the extension is more reliable for .md
    if upload.filename and upload.filename.lower().endswith('.md'):
        return 'text/markdown'
    return upload.content_type or ''


def write_file(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


async def save_upload(db: AsyncSession, user: User, upload: UploadFile) -> Document:
    content_type = guess_type(upload)
    if content_type not in SUPPORTED_TYPES:
        raise UploadError('Only PDF, Word (.docx), .txt and .md files are supported')

    data = await upload.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise UploadError(f'The file is larger than {settings.MAX_UPLOAD_BYTES // 1024 // 1024} MB')
    if not data:
        raise UploadError('The file is empty')

    # Stored under a random name: the original one is kept as the title only, never used as a path
    path = settings.MEDIA_DIR / str(user.id) / f'{uuid.uuid4().hex}{SUPPORTED_TYPES[content_type]}'
    await asyncio.to_thread(write_file, path, data)

    document = Document(
        owner_id=user.id,
        title=Path(upload.filename or 'document').name[:255],
        file_path=str(path),
        content_type=content_type,
        size=len(data),
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


async def process_document(db: AsyncSession, document: Document) -> Document:
    """Extract text and cut it into chunks. Marks the document as ready or failed."""
    try:
        # pypdf is CPU-bound, keep it off the event loop
        pages = await asyncio.to_thread(extract_pages, Path(document.file_path), document.content_type)
    except ExtractionError as e:
        document.status = DocumentStatus.FAILED
        document.error = str(e)
        await db.commit()
        return document

    chunks = chunk_pages(pages)
    vectors = await embed_passages([c.text for c in chunks])
    # Processing again (e.g. after switching the embedding model) replaces the old chunks
    await db.execute(delete(Chunk).where(Chunk.document_id == document.id))
    # Added directly instead of through document.chunks: assigning the relationship would lazy-load it,
    # and lazy loading isn't allowed with an async session
    db.add_all(
        Chunk(document_id=document.id, index=i, page=c.page, text=c.text, embedding=vector)
        for i, (c, vector) in enumerate(zip(chunks, vectors, strict=True))
    )
    document.pages = max((p.number for p in pages if p.number), default=None)
    document.chunks_count = len(chunks)
    document.status = DocumentStatus.READY
    document.error = ''
    await db.commit()
    return document


async def list_documents(db: AsyncSession, user: User) -> list[Document]:
    query = select(Document).where(Document.owner_id == user.id).order_by(Document.created_at.desc())
    return list(await db.scalars(query))


async def delete_document(db: AsyncSession, document: Document):
    await asyncio.to_thread(Path(document.file_path).unlink, missing_ok=True)
    await db.delete(document)
    await db.commit()
