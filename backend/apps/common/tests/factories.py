import io
import json
from itertools import count

import docx

from apps.users.models import User
from core.db import SessionLocal
from core.llm import AnswerEvent
from core.security import create_access_token, hash_password

PASSWORD = 'Str0ngPass!42'

_numbers = count(1)


async def create_user(**kwargs) -> User:
    async with SessionLocal() as db:
        email = kwargs.pop('email', f'user{next(_numbers)}@example.com')
        user = User(email=email, hashed_password=hash_password(PASSWORD))
        db.add(user)
        await db.commit()
        return user


def auth(user: User) -> dict:
    return {'Authorization': f'Bearer {create_access_token(user.id)}'}


def make_pdf(pages: list[str]) -> bytes:
    """A small but valid PDF with one line of text per page, written by hand to avoid extra libraries."""
    objects = ['<< /Type /Catalog /Pages 2 0 R >>', None, '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    kids = []
    for text in pages:
        stream = f'BT /F1 12 Tf 50 750 Td ({text}) Tj ET'
        objects.append(f'<< /Length {len(stream)} >>\nstream\n{stream}\nendstream')
        objects.append(
            f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {len(objects)} 0 R '
            '/Resources << /Font << /F1 3 0 R >> >> >>'
        )
        kids.append(len(objects))
    objects[1] = f'<< /Type /Pages /Kids [{" ".join(f"{k} 0 R" for k in kids)}] /Count {len(kids)} >>'

    out, offsets = b'%PDF-1.4\n', []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f'{number} 0 obj\n{body}\nendobj\n'.encode()
    xref = len(out)
    out += f'xref\n0 {len(objects) + 1}\n0000000000 65535 f \n'.encode()
    out += b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets)
    out += f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode()
    return out


def make_docx(paragraphs: list[str]) -> bytes:
    document = docx.Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'


async def upload(client, user, name: str, content: bytes, content_type: str):
    return await client.post('/documents', files={'file': (name, content, content_type)}, headers=auth(user))


class FakeLLM:
    """Stands in for Claude. Cites the first source it gets and answers with `answer_text`."""

    def __init__(self):
        self.answer_text = 'Refunds are possible within 14 days.'
        self.refuse = False
        self.calls: list[dict] = []

    async def answer(self, question, history, sources):
        self.calls.append({'question': question, 'history': history, 'sources': sources})
        if sources:
            citation = AnswerEvent(type='citation', source=sources[0], cited_text=sources[0].text[:30])
            yield citation
            yield citation  # the same chunk twice, the service keeps one
        if self.refuse:
            yield AnswerEvent(type='refused')
        else:
            for word in self.answer_text.split(' '):
                yield AnswerEvent(type='text', text=word + ' ')
        yield AnswerEvent(type='done')


def parse_sse(body: str) -> list[tuple[str, dict]]:
    events = []
    for block in body.strip().split('\n\n'):
        lines = dict(line.split(': ', 1) for line in block.splitlines())
        events.append((lines['event'], json.loads(lines['data'])))
    return events
