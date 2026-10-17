"""Background worker: python -m arq worker.WorkerSettings

Reading a PDF and computing embeddings can take a while for a big file, so the upload request
only saves the file and puts a job in Redis. This worker picks the job up.
"""

import logging

from arq.connections import RedisSettings

from apps.documents.models import Document
from apps.documents.services import process_document
from core import settings
from core.db import SessionLocal

logger = logging.getLogger(__name__)


async def process_document_job(ctx, document_id: int):
    async with SessionLocal() as db:
        document = await db.get(Document, document_id)
        if document is None:
            # Deleted before the worker got to it
            return
        document = await process_document(db, document)
        logger.info('Document %s: %s, %s chunks', document.id, document.status, document.chunks_count)


async def startup(ctx):
    # Load the embedding model before the first job instead of during it
    from core.embeddings import get_embedder

    get_embedder()


class WorkerSettings:
    functions = [process_document_job]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL or 'redis://localhost:6379')
    max_jobs = 2
    job_timeout = 600
