import asyncio
import hashlib
import os
import re
import tempfile
from pathlib import Path

import asyncpg
import numpy as np
import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv

# Tests use their own database and media folder, process uploads inside the request (no Redis)
# and never download the real embedding model or call Claude.
# This has to happen before core.settings is imported anywhere.
load_dotenv('../.env')
os.environ['DB_NAME'] = f'{os.environ["DB_NAME"]}_test'
os.environ['REDIS_URL'] = ''
os.environ['MEDIA_DIR'] = tempfile.mkdtemp(prefix='docs-assistant-media-')

from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from apps.users.router import auth_limiter  # noqa: E402
from core import embeddings, settings  # noqa: E402
from core.db import engine  # noqa: E402
from core.llm import get_llm  # noqa: E402
from main import app  # noqa: E402


class FakeEmbedder:
    """Bag of words hashed into a vector: texts that share words end up close, which is enough to test ranking."""

    dimensions = settings.EMBEDDING_DIMENSIONS

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for value in texts:
            vector = np.zeros(self.dimensions)
            for word in re.findall(r'\w+', value.lower().removeprefix('query: ').removeprefix('passage: ')):
                vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % self.dimensions] += 1
            vector[0] += 0.01  # never a zero vector
            vectors.append((vector / np.linalg.norm(vector)).tolist())
        return vectors


embeddings.get_embedder = lambda: FakeEmbedder()


async def recreate_test_database():
    conn = await asyncpg.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database='postgres',
    )
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{settings.DB_NAME}" WITH (FORCE)')
        await conn.execute(f'CREATE DATABASE "{settings.DB_NAME}"')
    finally:
        await conn.close()


def pytest_sessionstart(session):
    asyncio.run(recreate_test_database())
    # Build the schema with the real migrations, so they get tested too
    command.upgrade(Config('alembic.ini'), 'head')


@pytest.fixture(autouse=True)
async def clean_db():
    yield
    async with engine.begin() as conn:
        await conn.execute(text('TRUNCATE users RESTART IDENTITY CASCADE'))


@pytest.fixture(autouse=True)
def reset_rate_limit():
    auth_limiter.reset()


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test/api/v1') as client:
        yield client


@pytest.fixture
def llm():
    """Replaces Claude for one test; the test sets `llm.events` to what the model should "say"."""
    from apps.common.tests.factories import FakeLLM

    fake = FakeLLM()
    app.dependency_overrides[get_llm] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_llm, None)


@pytest.fixture
def media_dir() -> Path:
    return settings.MEDIA_DIR
