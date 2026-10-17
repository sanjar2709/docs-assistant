from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .models import DocumentStatus


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content_type: str
    size: int
    status: DocumentStatus
    error: str
    pages: int | None
    chunks_count: int
    created_at: datetime


class SearchHit(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: int
    document_id: int
    document_title: str
    page: int | None
    text: str
    score: float
