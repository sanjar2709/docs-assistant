from pathlib import Path

import pytest

from apps.common.tests.factories import make_docx, make_pdf
from apps.documents.chunking import chunk_pages, split_long
from apps.documents.extract import ExtractionError, Page, clean, extract_pages


def test_clean_joins_hyphenated_words_and_spaces():
    assert clean('docu-\nment   with\n\n\n\ngaps') == 'document with\n\ngaps'


def test_pdf_pages_keep_their_numbers(tmp_path: Path):
    path = tmp_path / 'a.pdf'
    path.write_bytes(make_pdf(['First page', 'Second page']))

    pages = extract_pages(path, 'application/pdf')

    assert [(p.number, p.text) for p in pages] == [(1, 'First page'), (2, 'Second page')]


def test_docx_and_text(tmp_path: Path):
    word = tmp_path / 'a.docx'
    word.write_bytes(make_docx(['Hello', 'World']))
    plain = tmp_path / 'a.txt'
    plain.write_text('Just text')

    assert extract_pages(word, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')[0].text == (
        'Hello\n\nWorld'
    )
    assert extract_pages(plain, 'text/plain') == [Page(None, 'Just text')]


def test_broken_or_empty_files(tmp_path: Path):
    broken = tmp_path / 'broken.pdf'
    broken.write_bytes(b'not a pdf')
    empty = tmp_path / 'empty.txt'
    empty.write_text('   ')

    with pytest.raises(ExtractionError, match='Could not read'):
        extract_pages(broken, 'application/pdf')
    with pytest.raises(ExtractionError, match='No text found'):
        extract_pages(empty, 'text/plain')


def test_chunks_never_span_pages():
    chunks = chunk_pages([Page(1, 'One.'), Page(2, 'Two.'), Page(3, 'Three.')])

    assert [(c.page, c.text) for c in chunks] == [(1, 'One.'), (2, 'Two.'), (3, 'Three.')]


def test_long_text_is_split_with_overlap():
    text = ' '.join(f'Sentence {i} is about topic {i}.' for i in range(100))

    chunks = chunk_pages([Page(None, text)], size=300, overlap=60)

    assert len(chunks) > 5
    assert all(len(c.text) <= 300 + 60 for c in chunks)
    last_word = chunks[0].text.split()[-1]
    assert last_word in chunks[1].text


def test_split_long_falls_back_to_words_and_hard_cuts():
    assert split_long('short', 100) == ['short']
    assert all(len(p) <= 10 for p in split_long('word ' * 20, 10))
    assert split_long('x' * 25, 10) == ['x' * 10, 'x' * 10, 'x' * 5]
