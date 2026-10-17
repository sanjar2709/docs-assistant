"""Getting plain text out of uploaded files."""

import re
from dataclasses import dataclass
from pathlib import Path

import docx
from pypdf import PdfReader

SUPPORTED_TYPES = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'text/plain': '.txt',
    'text/markdown': '.md',
}


class ExtractionError(Exception):
    pass


@dataclass
class Page:
    number: int | None  # None for formats without pages
    text: str


def clean(text: str) -> str:
    # PDFs often come with hyphenated line breaks and runs of spaces
    text = re.sub(r'-\n(\w)', r'\1', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_pages(path: Path, content_type: str) -> list[Page]:
    try:
        if content_type == 'application/pdf':
            reader = PdfReader(path)
            pages = [Page(number=i, text=clean(p.extract_text() or '')) for i, p in enumerate(reader.pages, start=1)]
        elif content_type.endswith('wordprocessingml.document'):
            document = docx.Document(path)
            pages = [Page(number=None, text=clean('\n\n'.join(p.text for p in document.paragraphs)))]
        else:
            pages = [Page(number=None, text=clean(path.read_text(encoding='utf-8', errors='replace')))]
    except Exception as e:
        raise ExtractionError(f'Could not read the file: {e}') from e

    pages = [p for p in pages if p.text]
    if not pages:
        # Usually a scanned PDF: images only, no text layer
        raise ExtractionError('No text found in the file. Scanned documents need OCR, which is not supported.')
    return pages
