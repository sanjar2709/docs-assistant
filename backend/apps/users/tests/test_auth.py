from apps.common.tests.factories import PASSWORD, auth, create_user
from core.security import create_refresh_token


async def test_register_and_login(client):
    response = await client.post('/auth/register', json={'email': 'New@Example.com', 'password': PASSWORD})
    assert response.status_code == 201
    assert response.json()['email'] == 'new@example.com'

    response = await client.post('/auth/login', json={'email': 'new@example.com', 'password': PASSWORD})
    assert {'access', 'refresh'} <= response.json().keys()


async def test_register_duplicate_email(client):
    await create_user(email='taken@example.com')

    response = await client.post('/auth/register', json={'email': 'taken@example.com', 'password': PASSWORD})

    assert response.status_code == 400


async def test_login_wrong_password(client):
    await create_user(email='me@example.com')

    response = await client.post('/auth/login', json={'email': 'me@example.com', 'password': 'wrong-password'})

    assert response.status_code == 401


async def test_me(client):
    user = await create_user(email='me@example.com')

    response = await client.get('/auth/me', headers=auth(user))

    assert response.json()['email'] == 'me@example.com'


async def test_refresh_token_is_not_an_access_token(client):
    user = await create_user()

    response = await client.get('/auth/me', headers={'Authorization': f'Bearer {create_refresh_token(user.id)}'})

    assert response.status_code == 401


async def test_login_is_rate_limited(client):
    for _ in range(10):
        await client.post('/auth/login', json={'email': 'x@example.com', 'password': 'wrong-password'})

    response = await client.post('/auth/login', json={'email': 'x@example.com', 'password': 'wrong-password'})

    assert response.status_code == 429


async def test_refresh(client):
    user = await create_user()

    response = await client.post('/auth/refresh', json={'refresh': create_refresh_token(user.id)})

    assert {'access', 'refresh'} <= response.json().keys()
    assert (await client.post('/auth/refresh', json={'refresh': 'garbage'})).status_code == 401


async def test_update_me(client):
    user = await create_user()

    response = await client.patch('/auth/me', json={'full_name': 'Sanjar Samadov'}, headers=auth(user))

    assert response.json()['full_name'] == 'Sanjar Samadov'


async def test_validation_error_format(client):
    response = await client.post('/auth/register', json={'email': 'nope', 'password': 'short'})

    error = response.json()['error']
    assert error['code'] == 'unprocessable_entity'
    assert {d['field'] for d in error['details']} == {'email', 'password'}
