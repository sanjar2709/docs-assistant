import pytest

from apps.common.tests.factories import auth, create_user, make_pdf, parse_sse, upload
from core import settings

PAGES = [
    'The company was founded in 2015 in Tashkent.',
    'Support works all day.',
    'Refunds are possible within 14 days.',
]


@pytest.fixture
async def setup(client):
    user = await create_user()
    await upload(client, user, 'company.pdf', make_pdf(PAGES), 'application/pdf')
    conversation = (await client.post('/conversations', headers=auth(user))).json()
    return user, conversation


async def ask(client, user, conversation, question, **extra):
    response = await client.post(
        f'/conversations/{conversation["id"]}/messages', json={'question': question, **extra}, headers=auth(user)
    )
    return response, parse_sse(response.text)


async def test_answer_streams_citations_text_and_done(client, llm, setup, monkeypatch):
    monkeypatch.setattr(settings, 'MIN_RELEVANCE', 0.0)
    user, conversation = setup

    response, events = await ask(client, user, conversation, 'When are refunds possible?')

    assert response.headers['content-type'].startswith('text/event-stream')
    kinds = [kind for kind, _ in events]
    assert kinds[0] == 'citation' and kinds[-1] == 'done'
    assert kinds.count('citation') == 1  # the duplicate citation is dropped
    assert ''.join(data['text'] for kind, data in events if kind == 'text').strip() == llm.answer_text
    citation = events[0][1]
    assert (citation['document_title'], citation['page']) == ('company.pdf', 3)


async def test_answer_and_question_are_saved(client, llm, setup, monkeypatch):
    monkeypatch.setattr(settings, 'MIN_RELEVANCE', 0.0)
    user, conversation = setup

    await ask(client, user, conversation, 'When are refunds possible?')
    saved = (await client.get(f'/conversations/{conversation["id"]}', headers=auth(user))).json()

    assert saved['title'] == 'When are refunds possible?'
    assert [m['role'] for m in saved['messages']] == ['user', 'assistant']
    assert saved['messages'][1]['citations'][0]['page'] == 3


async def test_history_goes_to_the_model(client, llm, setup):
    user, conversation = setup

    await ask(client, user, conversation, 'First question?')
    await ask(client, user, conversation, 'And a follow up?')

    history = llm.calls[1]['history']
    assert [m['role'] for m in history] == ['user', 'assistant']
    assert history[0]['content'] == 'First question?'


async def test_irrelevant_chunks_are_not_sent(client, llm, setup, monkeypatch):
    monkeypatch.setattr(settings, 'MIN_RELEVANCE', 0.99)
    user, conversation = setup

    _, events = await ask(client, user, conversation, 'What is the capital of Mars?')

    # The model is still asked, with no sources, so it can say "not in your documents" in the user's language
    assert llm.calls[0]['sources'] == []
    assert 'citation' not in [kind for kind, _ in events]


async def test_refusal(client, llm, setup):
    llm.refuse = True
    user, conversation = setup

    _, events = await ask(client, user, conversation, 'Something the model declines')

    assert [data['text'] for kind, data in events if kind == 'text'] == ["Sorry, I can't answer this question."]


async def test_search_can_be_limited_to_documents(client, llm, setup, monkeypatch):
    monkeypatch.setattr(settings, 'MIN_RELEVANCE', 0.0)
    user, conversation = setup
    other = (await upload(client, user, 'other.txt', b'Refunds are never possible.', 'text/plain')).json()

    await ask(client, user, conversation, 'refunds', document_ids=[other['id']])

    assert {s.document_title for s in llm.calls[0]['sources']} == {'other.txt'}


async def test_conversations_are_private(client, llm, setup):
    user, conversation = setup
    stranger = await create_user()

    assert (await client.get(f'/conversations/{conversation["id"]}', headers=auth(stranger))).status_code == 404
    response = await client.post(
        f'/conversations/{conversation["id"]}/messages', json={'question': 'hi'}, headers=auth(stranger)
    )
    assert response.status_code == 404
    assert (await client.get('/conversations', headers=auth(stranger))).json() == []


async def test_list_and_delete(client, setup):
    user, conversation = setup

    assert len((await client.get('/conversations', headers=auth(user))).json()) == 1
    assert (await client.delete(f'/conversations/{conversation["id"]}', headers=auth(user))).status_code == 204
    assert (await client.get('/conversations', headers=auth(user))).json() == []
