from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, HTTPException, UploadFile, status

from apps.users.dependencies import CurrentUser
from core import settings
from core.db import DBSession

from . import services
from .models import Document
from .schemas import DocumentRead

router = APIRouter(prefix='/documents', tags=['documents'])


async def enqueue_processing(db, document: Document) -> Document:
    if not settings.REDIS_URL:
        return await services.process_document(db, document)
    redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    try:
        await redis.enqueue_job('process_document_job', document.id)
    finally:
        await redis.aclose()
    return document


async def get_own_document(db, document_id: int, user) -> Document:
    document = await db.get(Document, document_id)
    if document is None or document.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Document not found')
    return document


@router.post('', response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload(file: UploadFile, db: DBSession, user: CurrentUser):
    try:
        document = await services.save_upload(db, user, file)
    except services.UploadError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None
    # Returns right away with status "processing"; the client polls until it's "ready"
    return await enqueue_processing(db, document)


@router.get('', response_model=list[DocumentRead])
async def list_documents(db: DBSession, user: CurrentUser):
    return await services.list_documents(db, user)


@router.get('/{document_id}', response_model=DocumentRead)
async def get_document(document_id: int, db: DBSession, user: CurrentUser):
    return await get_own_document(db, document_id, user)


@router.delete('/{document_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: int, db: DBSession, user: CurrentUser):
    await services.delete_document(db, await get_own_document(db, document_id, user))
