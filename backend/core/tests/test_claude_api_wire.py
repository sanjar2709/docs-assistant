"""ClaudeLLM through the real Anthropic SDK, against a stand-in for the API.

The stand-in answers in the API's own streaming format (message_start, text_delta, citations_delta, ...),
so this checks what we send over the wire and that the SDK's parsing plus our mapping work together.
Only Claude's words are made up; everything between our code and the HTTP connection is real.
"""

import json

import anthropic
import httpx2

from core.llm import ClaudeLLM, Source

SOURCES = [
    Source(11, 1, 'company.pdf', 1, 'Founded in 2015 in Tashkent.'),
    Source(13, 1, 'company.pdf', 3, 'Refunds are possible within 14 days.'),
    Source(20, 2, 'policy.docx', None, '24 days of paid leave.'),
]


def sse(*events: dict) -> bytes:
    return ''.join(f'event: {e["type"]}\ndata: {json.dumps(e)}\n\n' for e in events).encode()


def answer_stream(stop_reason='end_turn') -> bytes:
    citation = {
        'type': 'content_block_location',
        'cited_text': 'Refunds are possible within 14 days.',
        'document_index': 0,
        'document_title': 'company.pdf',
        'start_block_index': 1,
        'end_block_index': 2,
    }
    message = {
        'id': 'msg_test', 'type': 'message', 'role': 'assistant', 'model': 'claude-opus-5-5', 'content': [],
        'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': 1250, 'output_tokens': 1},
    }
    return sse(
        {'type': 'message_start', 'message': message},
        # Adaptive thinking comes first; with the default display its text is empty
        {'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'thinking', 'thinking': '', 'signature': ''}},  # noqa: E501
        {'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'signature_delta', 'signature': 'c2ln'}},
        {'type': 'content_block_stop', 'index': 0},
        {'type': 'content_block_start', 'index': 1, 'content_block': {'type': 'text', 'text': '', 'citations': []}},
        {'type': 'content_block_delta', 'index': 1, 'delta': {'type': 'citations_delta', 'citation': citation}},
        {'type': 'content_block_delta', 'index': 1, 'delta': {'type': 'text_delta', 'text': 'Pul 14 kun ichida '}},
        {'type': 'content_block_delta', 'index': 1, 'delta': {'type': 'text_delta', 'text': 'qaytariladi.'}},
        {'type': 'content_block_stop', 'index': 1},
        {
            'type': 'message_delta',
            'delta': {'stop_reason': stop_reason, 'stop_sequence': None},
            'usage': {'output_tokens': 42},
        },
        {'type': 'message_stop'},
    )


class FakeAnthropicAPI:
    def __init__(self, body: bytes):
        self.body = body
        self.requests: list[httpx2.Request] = []

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        return httpx2.Response(200, headers={'content-type': 'text/event-stream'}, content=self.body)

    def client(self) -> anthropic.AsyncAnthropic:
        http_client = anthropic.DefaultAsyncHttpxClient(transport=httpx2.MockTransport(self))
        return anthropic.AsyncAnthropic(api_key='test-key', http_client=http_client, max_retries=0)


async def run(api: FakeAnthropicAPI, history=None):
    llm = ClaudeLLM(client=api.client())
    return [event async for event in llm.answer('Qachon pul qaytariladi?', history or [], SOURCES)]


async def test_request_on_the_wire():
    api = FakeAnthropicAPI(answer_stream())

    await run(api, history=[{'role': 'user', 'content': 'Salom'}, {'role': 'assistant', 'content': 'Salom!'}])

    request = api.requests[0]
    body = json.loads(request.content)
    assert request.url.path == '/v1/messages'
    assert 'server-side-fallback-2026-07-01' in request.headers['anthropic-beta']
    assert body['model'] == 'claude-opus-5-5'
    assert body['stream'] is True
    assert body['fallbacks'] == 'default'
    assert body['output_config'] == {'effort': 'low'}
    assert 'thinking' not in body  # adaptive by default on this model; "disabled" would be rejected
    assert [m['role'] for m in body['messages']] == ['user', 'assistant', 'user']

    documents = [block for block in body['messages'][-1]['content'] if block['type'] == 'document']
    assert [d['title'] for d in documents] == ['company.pdf', 'policy.docx']
    assert documents[0]['source']['type'] == 'content'
    assert [b['text'] for b in documents[0]['source']['content']] == [SOURCES[0].text, SOURCES[1].text]
    assert all(d['citations'] == {'enabled': True} for d in documents)
    assert body['messages'][-1]['content'][-1] == {'type': 'text', 'text': 'Qachon pul qaytariladi?'}


async def test_streamed_answer_and_citation_mapping():
    events = await run(FakeAnthropicAPI(answer_stream()))

    assert [e.type for e in events] == ['citation', 'text', 'text', 'done']
    citation = events[0]
    # document 0, block 1 is the second company.pdf chunk: page 3
    assert (citation.source.chunk_id, citation.source.page) == (13, 3)
    assert citation.cited_text == 'Refunds are possible within 14 days.'
    assert ''.join(e.text for e in events if e.type == 'text') == 'Pul 14 kun ichida qaytariladi.'
    assert events[-1].usage == {'input_tokens': 1250, 'output_tokens': 42}


async def test_refusal_from_the_api():
    events = await run(FakeAnthropicAPI(answer_stream(stop_reason='refusal')))

    assert [e.type for e in events][-2:] == ['refused', 'done']
