from apps.common.tests.factories import auth, create_user, make_pdf, upload


async def search(client, user, q, **params):
    response = await client.get('/documents/search', params={'q': q, **params}, headers=auth(user))
    return response.json()


async def test_finds_the_relevant_page(client):
    user = await create_user()
    pages = ['The company was founded in 2015.', 'Support works all day.', 'Refunds are possible within 14 days.']
    await upload(client, user, 'company.pdf', make_pdf(pages), 'application/pdf')

    hits = await search(client, user, 'When are refunds possible?')

    assert hits[0]['page'] == 3
    assert hits[0]['document_title'] == 'company.pdf'
    assert hits[0]['score'] > hits[-1]['score']


async def test_only_own_documents_are_searched(client):
    owner, stranger = await create_user(), await create_user()
    await upload(client, owner, 'secret.txt', b'The salary of the director', 'text/plain')

    assert await search(client, stranger, 'salary director') == []


async def test_failed_documents_are_skipped(client):
    user = await create_user()
    await upload(client, user, 'fake.pdf', b'broken', 'application/pdf')

    assert await search(client, user, 'anything here') == []


async def test_limit_and_validation(client):
    user = await create_user()
    await upload(client, user, 'a.pdf', make_pdf(['one', 'two', 'three']), 'application/pdf')

    assert len(await search(client, user, 'one two three', limit=2)) == 2
    response = await client.get('/documents/search', params={'q': 'a'}, headers=auth(user))
    assert response.status_code == 422
