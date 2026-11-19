"""Split section paragraphs into chunks that never cross a section boundary."""

import re

from pydantic import BaseModel

from waypoint_ingest.normalize import Paragraph

MAX_TOKENS = 800
TOKEN = re.compile(r"\w+|[^\w\s]")


class Chunk(BaseModel):
    """A citable passage: its text plus everything a citation needs."""

    id: str
    source_id: str
    edition: str
    jurisdiction: str
    section_ref: str
    heading_path: list[str]
    page: int | None
    text: str
    token_count: int


def token_count(text: str) -> int:
    """Approximate token count: words and punctuation marks."""
    return len(TOKEN.findall(text))


def pack(paragraphs: list[Paragraph], max_tokens: int = MAX_TOKENS) -> list[Paragraph]:
    """Merge consecutive paragraphs into pieces of at most `max_tokens`.

    Each piece keeps the page of its first paragraph.
    """
    pieces: list[Paragraph] = []
    size = 0
    for paragraph in split_long(paragraphs, max_tokens):
        tokens = token_count(paragraph.text)
        if pieces and size + tokens <= max_tokens:
            pieces[-1] = Paragraph(
                pieces[-1].page, f"{pieces[-1].text}\n\n{paragraph.text}"
            )
            size += tokens
        else:
            pieces.append(paragraph)
            size = tokens
    return pieces


def split_long(paragraphs: list[Paragraph], max_tokens: int) -> list[Paragraph]:
    """Split any paragraph over `max_tokens` into word runs that fit."""
    result = []
    for paragraph in paragraphs:
        words: list[str] = []
        size = 0
        for word in paragraph.text.split(" "):
            tokens = token_count(word)
            if words and size + tokens > max_tokens:
                result.append(Paragraph(paragraph.page, " ".join(words)))
                words, size = [], 0
            words.append(word)
            size += tokens
        result.append(Paragraph(paragraph.page, " ".join(words)))
    return result
