"""Split a PDF without numbered section bookmarks into one section per page."""

import re
from pathlib import Path

import pymupdf

from waypoint_ingest.extract import outline_headings
from waypoint_ingest.normalize import Paragraph, TextSection, paragraphs
from waypoint_ingest.pdf_lines import page_lines, tidy

PAGE_NUMBER = re.compile(r"^([ivxlc]+|\d+|\d+-\d+)$", re.IGNORECASE)


def page_sections(
    pdf: Path, prefix: str, title: str, columns: int = 1
) -> list[TextSection]:
    """One section per page with text, cited as `<prefix> p.<page>`.

    Single-column pages are rebuilt from their lines. Two-column pages are
    read in the PDF's own block order, which follows the columns. The
    heading path is the document title and the page's first bold text.
    Page numbers are dropped.
    """
    doc = pymupdf.open(pdf)
    read = block_paragraphs if columns == 2 else line_paragraphs
    sections = []
    for number in range(1, doc.page_count + 1):
        body, heading = read(doc, number)
        if not body:
            continue
        ref = f"{prefix} p.{number}"
        path = [title, heading, ref] if heading else [title, ref]
        sections.append(TextSection(ref, path, number, body))
    return sections


def line_paragraphs(
    doc: pymupdf.Document, number: int
) -> tuple[list[Paragraph], str | None]:
    """Paragraphs rebuilt from a single-column page's lines, and its heading."""
    lines = [
        line
        for line in page_lines(doc, number, columns=1)
        if not PAGE_NUMBER.match(line.text)
    ]
    heading = next((line.text for line in lines if line.bold), None)
    return paragraphs(lines), heading


def block_paragraphs(
    doc: pymupdf.Document, number: int
) -> tuple[list[Paragraph], str | None]:
    """One paragraph per text block in the PDF's order, and the first bold one."""
    body, heading = [], None
    for block in doc[number - 1].get_text("dict")["blocks"]:
        spans = [
            s
            for line in block.get("lines", [])
            for s in line["spans"]
            if s["text"].strip()
        ]
        text = tidy(" ".join(" ".join(s["text"] for s in spans).split()))
        if not text or PAGE_NUMBER.match(text):
            continue
        if heading is None and all(s["flags"] & 16 for s in spans):
            heading = text
        body.append(Paragraph(number, text))
    return body, heading


def has_section_bookmarks(pdf: Path) -> bool:
    """True when the PDF's bookmarks give numbered sections, as in the TC AIM."""
    return bool(outline_headings(pymupdf.open(pdf)))
