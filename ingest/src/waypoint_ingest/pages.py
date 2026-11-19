"""Split a PDF without bookmarks into one section per page."""

import re
from pathlib import Path

import pymupdf

from waypoint_ingest.normalize import TextSection, paragraphs
from waypoint_ingest.pdf_lines import page_lines

PAGE_NUMBER = re.compile(r"^([ivxlc]+|\d+)$", re.IGNORECASE)


def page_sections(pdf: Path, prefix: str, title: str) -> list[TextSection]:
    """One section per page with text, cited as `<prefix> p.<page>`.

    The heading path is the document title and the page's first bold line.
    Lines holding only a page number are dropped.
    """
    doc = pymupdf.open(pdf)
    sections = []
    for number in range(1, doc.page_count + 1):
        lines = [
            line
            for line in page_lines(doc, number, columns=1)
            if not PAGE_NUMBER.match(line.text)
        ]
        if not lines:
            continue
        ref = f"{prefix} p.{number}"
        heading = next((line.text for line in lines if line.bold), None)
        path = [title, heading, ref] if heading else [title, ref]
        sections.append(TextSection(ref, path, number, paragraphs(lines)))
    return sections


def has_outline(pdf: Path) -> bool:
    """True when the PDF has bookmarks to split sections by."""
    return bool(pymupdf.open(pdf).get_toc())
