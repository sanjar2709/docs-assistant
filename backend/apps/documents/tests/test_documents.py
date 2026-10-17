from pathlib import Path

import pytest
from sqlalchemy import func, select

from apps.common.tests.factories import DOCX, auth, create_user, make_docx, make_pdf, upload
from apps.documents.models import Chunk, Document
from core import settings
from core.db import SessionLocal


async def test_upload_pdf_is_processed(client):
    user = await create_user()

    pdf = make_pdf(['Founded in 2015.', 'Refunds within 14 days.'])

    response = await upload(client, user, 'company.pdf', pdf, 'application/pdf')

    assert response.status_code == 201
    data = response.json()
    assert (data['status'], data['pages'], data['chunks_count']) == ('ready', 2, 2)
    async with SessionLocal() as db:
        chunks = list(await db.scalars(select(Chunk).order_by(Chunk.index)))
    assert [c.page for c in chunks] == [1, 2]
    assert all(c.embedding is not None for c in chunks)


async def test_upload_docx_and_markdown(client):
    user = await create_user()

    word = await upload(client, user, 'policy.docx', make_docx(['24 days of leave.']), DOCX)
    markdown = await upload(client, user, 'notes.md', b'# Notes\n\nLunch at 13:00.', 'application/octet-stream')

    assert word.json()['status'] == 'ready'
    assert (markdown.json()['status'], markdown.json()['content_type']) == ('ready', 'text/markdown')


@pytest.mark.parametrize(('name', 'content', 'content_type', 'message'), (
    ('virus.exe', b'MZ', 'application/x-msdownload', 'Only PDF'),
    ('empty.txt', b'', 'text/plain', 'empty'),
))
async def test_rejected_uploads(client, name, content, content_type, message):
    user = await create_user()

    response = await upload(client, user, name, content, content_type)

    assert response.status_code == 400
    assert message in response.json()['error']['message']


async def test_too_big(client, monkeypatch):
    monkeypatch.setattr(settings, 'MAX_UPLOAD_BYTES', 10)
    user = await create_user()

    response = await upload(client, user, 'a.txt', b'x' * 11, 'text/plain')

    assert 'larger than' in response.json()['error']['message']


async def test_unreadable_file_is_marked_failed(client):
    user = await create_user()

    response = await upload(client, user, 'fake.pdf', b'not a pdf', 'application/pdf')

    assert response.json()['status'] == 'failed'
    assert 'Could not read the file' in response.json()['error']


async def test_file_is_stored_under_a_random_name(client):
    user = await create_user()

    await upload(client, user, '../../etc/passwd.txt', b'hello', 'text/plain')

    async with SessionLocal() as db:
        document = await db.scalar(select(Document))
    assert document.title == 'passwd.txt'
    assert Path(document.file_path).parent == settings.MEDIA_DIR / str(user.id)


async def test_only_owner_sees_and_deletes(client):
    owner, stranger = await create_user(), await create_user()
    document = (await upload(client, owner, 'a.txt', b'hello', 'text/plain')).json()

    assert len((await client.get('/documents', headers=auth(owner))).json()) == 1
    assert (await client.get('/documents', headers=auth(stranger))).json() == []
    assert (await client.get(f'/documents/{document["id"]}', headers=auth(stranger))).status_code == 404
    assert (await client.delete(f'/documents/{document["id"]}', headers=auth(stranger))).status_code == 404


async def test_delete_removes_file_and_chunks(client):
    user = await create_user()
    document = (await upload(client, user, 'a.txt', b'hello', 'text/plain')).json()
    async with SessionLocal() as db:
        path = Path((await db.get(Document, document['id'])).file_path)

    response = await client.delete(f'/documents/{document["id"]}', headers=auth(user))

    assert response.status_code == 204
    assert not path.exists()  # noqa: ASYNC240  (a test, blocking is fine)
    async with SessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(Chunk)) == 0


async def test_processing_again_replaces_chunks(client):
    from apps.documents.services import process_document

    user = await create_user()
    document = (await upload(client, user, 'a.txt', b'hello', 'text/plain')).json()

    async with SessionLocal() as db:
        await process_document(db, await db.get(Document, document['id']))
        assert await db.scalar(select(func.count()).select_from(Chunk)) == 1


async def test_worker_job(client):
    from worker import process_document_job

    user = await create_user()
    async with SessionLocal() as db:
        document = Document(
            owner_id=user.id, title='a.txt', file_path='/nonexistent', content_type='text/plain', size=1
        )
        db.add(document)
        await db.commit()

    await process_document_job({}, document.id)
    await process_document_job({}, 999)  # deleted meanwhile: nothing happens

    async with SessionLocal() as db:
        assert (await db.get(Document, document.id)).status == 'failed'
