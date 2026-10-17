"""ClaudeLLM against a stand-in Anthropic client: checks the request we send and how citations map back to chunks."""

from types import SimpleNamespace

from core.llm import ClaudeLLM, Source, build_user_content

SOURCES = [
    Source(chunk_id=1, document_id=10, document_title='company.pdf', page=1, text='Founded in 2015.'),
    Source(chunk_id=2, document_id=20, document_title='policy.docx', page=None, text='24 days of leave.'),
    Source(chunk_id=3, document_id=10, document_title='company.pdf', page=3, text='Refunds within 14 days.'),
]


def delta(**fields):
    return SimpleNamespace(type='content_block_delta', delta=SimpleNamespace(**fields))


class FakeStream:
    def __init__(self, events, stop_reason='end_turn'):
        self.events = events
        usage = SimpleNamespace(input_tokens=100, output_tokens=20)
        self.message = SimpleNamespace(stop_reason=stop_reason, usage=usage)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def __aiter__(self):
        return self._iterate()

    async def _iterate(self):
        for event in self.events:
            yield event

    async def get_final_message(self):
        return self.message


class FakeClient:
    def __init__(self, stream):
        self.requests = []
        self.stream_to_return = stream
        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=self._stream))

    def _stream(self, **request):
        self.requests.append(request)
        return self.stream_to_return


def make_llm(events, stop_reason='end_turn'):
    llm = ClaudeLLM.__new__(ClaudeLLM)
    llm.client = FakeClient(FakeStream(events, stop_reason))
    return llm


async def collect(llm, question='q', history=None, sources=SOURCES):
    return [event async for event in llm.answer(question, history or [], sources)]


def test_chunks_are_grouped_into_one_document_per_file():
    content, documents = build_user_content('When?', SOURCES)

    assert [d['title'] for d in content[:-1]] == ['company.pdf', 'policy.docx']
    assert [b['text'] for b in content[0]['source']['content']] == ['Founded in 2015.', 'Refunds within 14 days.']
    assert all(d['citations'] == {'enabled': True} for d in content[:-1])
    assert content[-1] == {'type': 'text', 'text': 'When?'}
    assert [[s.chunk_id for s in group] for group in documents] == [[1, 3], [2]]


async def test_request_shape():
    llm = make_llm([])

    await collect(llm, question='When?', history=[{'role': 'user', 'content': 'hi'}])

    request = llm.client.requests[0]
    assert request['model'] == 'claude-opus-5-5'
    assert request['fallbacks'] == 'default'
    assert request['messages'][0] == {'role': 'user', 'content': 'hi'}
    assert request['messages'][-1]['content'][-1]['text'] == 'When?'


async def test_citations_map_back_to_chunks():
    citation = SimpleNamespace(
        type='content_block_location', document_index=0, start_block_index=1, end_block_index=2, cited_text='Refunds'
    )
    other = SimpleNamespace(type='char_location')
    events = [
        SimpleNamespace(type='content_block_start'),
        delta(type='text_delta', text='Within 14 days.'),
        delta(type='citations_delta', citation=citation),
        delta(type='citations_delta', citation=other),
    ]

    result = await collect(make_llm(events))

    assert [e.type for e in result] == ['text', 'citation', 'done']
    assert result[1].source.chunk_id == 3
    assert result[1].cited_text == 'Refunds'
    assert result[2].usage == {'input_tokens': 100, 'output_tokens': 20}


async def test_refusal_is_reported():
    result = await collect(make_llm([], stop_reason='refusal'))

    assert [e.type for e in result] == ['refused', 'done']
