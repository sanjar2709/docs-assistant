"""Cutting text into overlapping pieces for search.

Pieces are cut on paragraph, then sentence, then word boundaries, so a chunk rarely starts in the
middle of a thought. Neighbouring chunks share a little text: an answer sitting right on a border
can still be found in one of them. A chunk never spans two PDF pages, so a citation can name the page.
"""

import re
from dataclasses import dataclass

from .extract import Page

CHUNK_SIZE = 1200  # characters, roughly 250-300 tokens
OVERLAP = 200

SENTENCE_END = re.compile(r'(?<=[.!?])\s+')


@dataclass
class TextChunk:
    text: str
    page: int | None


def split_long(text: str, size: int) -> list[str]:
    """Break a paragraph that alone is longer than `size` into sentences, or words as the last resort."""
    if len(text) <= size:
        return [text]
    parts, current = [], ''
    pieces = SENTENCE_END.split(text)
    if len(pieces) == 1:
        pieces = text.split(' ')
    for piece in pieces:
        if current and len(current) + len(piece) + 1 > size:
            parts.append(current)
            current = piece
        else:
            current = f'{current} {piece}'.strip()
    if current:
        parts.append(current)
    # A single word longer than `size` (e.g. a URL) is cut hard
    return [p[i:i + size] for p in parts for i in range(0, len(p), size)]


def chunk_pages(pages: list[Page], size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[TextChunk]:
    blocks = [
        (piece, page.number)
        for page in pages
        for paragraph in page.text.split('\n\n')
        if paragraph.strip()
        for piece in split_long(paragraph.strip(), size)
    ]

    chunks: list[TextChunk] = []
    current, current_page = '', None
    for text, page in blocks:
        if current and page != current_page:
            # New page: close the chunk without overlap, so every chunk belongs to exactly one page
            chunks.append(TextChunk(current, current_page))
            current = ''
        elif current and len(current) + len(text) + 2 > size:
            chunks.append(TextChunk(current, current_page))
            # Start the next chunk with the end of this one
            tail = current[-overlap:]
            tail = tail[tail.find(' ') + 1:] if ' ' in tail else tail
            current, current_page = tail, page
        if not current:
            current_page = page
        current = f'{current}\n\n{text}' if current else text
    if current:
        chunks.append(TextChunk(current, current_page))
    return chunks
