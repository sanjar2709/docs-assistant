from enum import StrEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.common.models import TimeStampedMixin
from core import settings
from core.db import Base


class DocumentStatus(StrEnum):
    PROCESSING = 'processing'
    READY = 'ready'
    FAILED = 'failed'


class Document(TimeStampedMixin, Base):
    __tablename__ = 'documents'

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    title: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column(Integer)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e]),
        default=DocumentStatus.PROCESSING,
    )
    error: Mapped[str] = mapped_column(Text, default='')
    pages: Mapped[int | None] = mapped_column(Integer)
    chunks_count: Mapped[int] = mapped_column(Integer, default=0)

    chunks: Mapped[list['Chunk']] = relationship(
        back_populates='document',
        cascade='all, delete-orphan',
        order_by='Chunk.index',
    )

    def __repr__(self):
        return f'<Document {self.title}>'


class Chunk(Base):
    """A piece of a document small enough to search and to quote."""

    __tablename__ = 'chunks'
    __table_args__ = (
        # HNSW index for fast nearest-neighbour search by cosine distance
        Index(
            'ix_chunks_embedding',
            'embedding',
            postgresql_using='hnsw',
            postgresql_ops={'embedding': 'vector_cosine_ops'},
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('documents.id', ondelete='CASCADE'), index=True)
    index: Mapped[int] = mapped_column(Integer)
    # PDF page the chunk starts on; Word and text files have no pages
    page: Mapped[int | None] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.EMBEDDING_DIMENSIONS))

    document: Mapped[Document] = relationship(back_populates='chunks')
