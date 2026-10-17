from enum import StrEnum

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.common.models import TimeStampedMixin
from core.db import Base


class Role(StrEnum):
    USER = 'user'
    ASSISTANT = 'assistant'


class Conversation(TimeStampedMixin, Base):
    __tablename__ = 'conversations'

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    title: Mapped[str] = mapped_column(String(200), default='New chat')

    messages: Mapped[list['Message']] = relationship(
        back_populates='conversation',
        cascade='all, delete-orphan',
        order_by='Message.id',
        lazy='selectin',
    )


class Message(TimeStampedMixin, Base):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey('conversations.id', ondelete='CASCADE'), index=True)
    role: Mapped[Role] = mapped_column(
        Enum(Role, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e])
    )
    content: Mapped[str] = mapped_column(Text)
    # For answers: which chunks were quoted, with file, page and the quote itself
    citations: Mapped[list[dict]] = mapped_column(JSONB, default=list)

    conversation: Mapped[Conversation] = relationship(back_populates='messages')
