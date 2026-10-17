from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import Role


class Citation(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    page: int | None
    cited_text: str


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: Role
    content: str
    citations: list[Citation]
    created_at: datetime


class ConversationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationRead(ConversationListItem):
    messages: list[MessageRead]


class QuestionCreate(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    document_ids: list[int] | None = Field(default=None, description='Search only these documents')
