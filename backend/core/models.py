# Every model has to be imported here, so Alembic can see it when generating migrations
from apps.documents.models import Chunk, Document
from apps.users.models import User

__all__ = ('Chunk', 'Document', 'User')
