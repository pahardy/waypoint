"""Turn PDF pages into visual lines with font information."""

import re
from dataclasses import dataclass

import pymupdf

COLUMN_SPLIT_X = 300
SAME_LINE_DY = 3


@dataclass
class Line:
    """One visual line of text on a page. x is where its text starts."""

    page: int
    column: int
    x: float
    y: float
    text: str
    size: int
    bold: bool
    bullet: bool


def page_lines(
    doc: pymupdf.Document,
    page_number: int,
    columns: int = 2,
    max_size: float = float("inf"),
) -> list[Line]:
    """Return a page's lines in reading order: left column, then right.

    Spans larger than `max_size` (such as side tabs) are dropped first.
    """
    split_x = COLUMN_SPLIT_X if columns == 2 else float("inf")
    spans = []
    for block in doc[page_number - 1].get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            spans.extend(
                s for s in line["spans"] if s["text"].strip() and s["size"] <= max_size
            )
    spans.sort(key=lambda s: (column_of(s, split_x), s["bbox"][1]))

    groups: list[list[dict]] = []
    for span in spans:
        last = groups[-1][0] if groups else None
        if (
            last
            and column_of(last, split_x) == column_of(span, split_x)
            and abs(last["bbox"][1] - span["bbox"][1]) < SAME_LINE_DY
        ):
            groups[-1].append(span)
        else:
            groups.append([span])

    lines = []
    for group in groups:
        group.sort(key=lambda s: s["bbox"][0])
        line = new_line(page_number, group[0], column_of(group[0], split_x))
        for span in group[1:]:
            merge_span(line, span)
        lines.append(line)
    for line in lines:
        line.text = tidy(line.text)
    return [line for line in lines if line.text]


def tidy(text: str) -> str:
    """Remove spacing artifacts left by joining spans."""
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    return re.sub(r"(?<=\w)-\s+(?=[A-Z])", "-", text)


def column_of(span: dict, split_x: float) -> int:
    """0 for the left column, 1 for the right."""
    return 0 if span["bbox"][0] < split_x else 1


def is_bullet(span: dict) -> bool:
    """Wingdings spans are the guide's "essential knowledge" bullets."""
    return "Wingdings" in span["font"]


def new_line(page_number: int, span: dict, column: int) -> Line:
    """Start a line from its first span."""
    bullet = is_bullet(span)
    return Line(
        page=page_number,
        column=column,
        x=span["bbox"][0],
        y=span["bbox"][1],
        text="" if bullet else span["text"].strip(),
        size=0 if bullet else round(span["size"]),
        bold=not bullet and bool(span["flags"] & 16),
        bullet=bullet,
    )


def merge_span(line: Line, span: dict) -> None:
    """Append a span that sits on the same visual line."""
    if is_bullet(span):
        line.bullet = True
        return
    if not line.text:
        line.x = span["bbox"][0]
    line.text = f"{line.text} {span['text'].strip()}".strip()
    line.size = max(line.size, round(span["size"]))
    line.bold = line.bold or bool(span["flags"] & 16)
