"""switch embeddings to multilingual-e5-large

Revision ID: b10853594324
Revises: b0d0640e50cc
Create Date: 2026-10-17 17:59:00.514630

"""
from typing import Sequence, Union

from alembic import op
import pgvector.sqlalchemy
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b10853594324'
down_revision: Union[str, Sequence[str], None] = 'b0d0640e50cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Vectors from the old model can't be converted, documents have to be processed again
    op.drop_index('ix_chunks_embedding', table_name='chunks')
    op.alter_column(
        'chunks', 'embedding',
        type_=pgvector.sqlalchemy.vector.VECTOR(dim=1024),
        postgresql_using='NULL',
    )
    op.execute("UPDATE documents SET status = 'processing' WHERE status = 'ready'")
    op.create_index(
        'ix_chunks_embedding', 'chunks', ['embedding'],
        postgresql_using='hnsw', postgresql_ops={'embedding': 'vector_cosine_ops'},
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_chunks_embedding', table_name='chunks')
    op.alter_column(
        'chunks', 'embedding',
        type_=pgvector.sqlalchemy.vector.VECTOR(dim=768),
        postgresql_using='NULL',
    )
    op.create_index(
        'ix_chunks_embedding', 'chunks', ['embedding'],
        postgresql_using='hnsw', postgresql_ops={'embedding': 'vector_cosine_ops'},
    )
