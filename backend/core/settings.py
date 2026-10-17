import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# One .env in the repository root is shared by the backend and docker compose
load_dotenv(BASE_DIR.parent / '.env')

PROJECT_NAME = 'Docs Assistant'
VERSION = '1.0.0'

DEBUG = os.getenv('DEBUG') == '1'

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError('SECRET_KEY environment variable is not set')

ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3001').split()

ACCESS_TOKEN_LIFETIME_MINUTES = int(os.getenv('ACCESS_TOKEN_LIFETIME_MINUTES', 30))
REFRESH_TOKEN_LIFETIME_DAYS = int(os.getenv('REFRESH_TOKEN_LIFETIME_DAYS', 7))

# Login and register attempts per minute from one IP
AUTH_RATE_LIMIT = int(os.getenv('AUTH_RATE_LIMIT', 10))

# Database

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

DATABASE_URL = f'postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
DB_ECHO = os.getenv('DB_ECHO') == '1'

# Uploads

MEDIA_DIR = Path(os.getenv('MEDIA_DIR', BASE_DIR / 'media'))
MAX_UPLOAD_BYTES = int(os.getenv('MAX_UPLOAD_MB', 10)) * 1024 * 1024

# Embeddings. Changing the model to one with another size needs a migration of chunks.embedding.

EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
EMBEDDING_DIMENSIONS = 768
EMBEDDING_CACHE_DIR = Path(os.getenv('EMBEDDING_CACHE_DIR', BASE_DIR / '.cache' / 'models'))

# Background jobs go through Redis. Empty means documents are processed inside the upload request.
REDIS_URL = os.getenv('REDIS_URL', '')
