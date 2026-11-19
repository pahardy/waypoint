"""Rebuild paragraphs from a section's visual lines."""

import re
from dataclasses import dataclass

from waypoint_ingest.pdf_lines import Line

PARAGRAPH_GAP = 1.5
HEADING_SIZE_STEP = 2
LIST_ITEM = re.compile(r"^(\(\w{1,4}\)|\d+\.|NOTES?\s?:)")
SENTENCE_END = (".", ":", ";", "?", "!")


@dataclass
class Paragraph:
    """Paragraph text and the page it starts on (None for unpaged sources)."""

    page: int | None
    text: str


@dataclass
class TextSection:
    """A citable section: its reference, heading path and paragraphs."""

    ref: str
    heading_path: list[str]
    page: int | None
    paragraphs: list[Paragraph]


def paragraphs(lines: list[Line]) -> list[Paragraph]:
    """Group lines into paragraphs and join them into clean text."""
    result: list[Paragraph] = []
    previous = None
    for line in lines:
        if previous is None or starts_paragraph(line, previous):
            result.append(Paragraph(line.page, line.text))
        else:
            result[-1].text = join(result[-1].text, line.text)
        previous = line
    return result


def starts_paragraph(line: Line, previous: Line) -> bool:
    """True when a line begins a new paragraph rather than continuing one."""
    if line.bullet or LIST_ITEM.match(line.text):
        return True
    if is_heading_over(line, previous) or is_heading_over(previous, line):
        return True
    if (line.page, line.column) != (previous.page, previous.column):
        return previous.text.endswith(SENTENCE_END)
    return line.y - previous.y > PARAGRAPH_GAP * max(line.size, previous.size)


def is_heading_over(line: Line, other: Line) -> bool:
    """A bold line clearly larger than its neighbour is a heading. Requiring
    bold keeps symbols and subscripts in body text from splitting it."""
    return line.bold and line.size - other.size >= HEADING_SIZE_STEP


def join(text: str, more: str) -> str:
    """Join wrapped lines. A line-end hyphen is a real compound hyphen in TC
    documents, so it is kept and no space is added."""
    if text.endswith("-"):
        return text + more
    return f"{text} {more}"
