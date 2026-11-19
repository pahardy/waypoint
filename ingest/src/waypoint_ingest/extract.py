"""Split an outlined PDF into sections, using its bookmarks as the section list."""

import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

from waypoint_ingest.pdf_lines import Line, page_lines

HEADER_MAX_Y = 40
FOOTER_MIN_Y = 750
SIDE_TAB_MIN_SIZE = 20
CONTINUATION_INDENT = 5
CONTINUATION_GAP = 1.6
NUMBERED = re.compile(r"^(\d+(?:\.\d+)*)\s+(.*)$")


@dataclass
class Heading:
    """One numbered bookmark: where a section starts and what it is called."""

    part: str
    number: str
    title: str
    page: int
    path: list[str]

    @property
    def ref(self) -> str:
        """Citation reference, for example `GEN 1.1.5`."""
        return f"{self.part} {self.number}"


@dataclass
class Section:
    """A section's heading and its body lines."""

    heading: Heading
    lines: list[Line] = field(default_factory=list)


def outline_headings(doc: pymupdf.Document) -> list[Heading]:
    """Numbered bookmarks under each `PART—Title` top-level bookmark."""
    headings: list[Heading] = []
    part, path = None, []
    for level, title, page in doc.get_toc():
        title = " ".join(title.split())
        if level == 1:
            part = title.split("—")[0] if "—" in title else None
            path = [title]
            continue
        match = NUMBERED.match(title)
        if part is None or not match:
            continue
        path = path[: level - 1] + [title]
        headings.append(Heading(part, match[1], match[2], page, path))
    return headings


def is_margin(line: Line) -> bool:
    """Running header or page number."""
    return line.y < HEADER_MAX_Y or line.y > FOOTER_MIN_Y


def starts_heading(line: Line, heading: Heading) -> bool:
    """A bold line on the bookmark's page that begins with its number."""
    return (
        line.bold
        and line.page == heading.page
        and line.text.split()[0] == heading.number
    )


def extract_sections(path: Path) -> tuple[list[Section], list[Heading]]:
    """Return the sections found and the bookmarks whose heading was not found.

    Text under a missing heading stays in the previous section.
    """
    doc = pymupdf.open(path)
    headings = outline_headings(doc)
    sections: list[Section] = []
    missing: list[Heading] = []
    pending = 0
    heading_line = None
    for page_number in range(headings[0].page, doc.page_count + 1):
        while pending < len(headings) and headings[pending].page < page_number:
            missing.append(headings[pending])
            pending += 1
        for line in page_lines(doc, page_number, max_size=SIDE_TAB_MIN_SIZE):
            if is_margin(line):
                continue
            if pending < len(headings) and starts_heading(line, headings[pending]):
                sections.append(Section(headings[pending]))
                heading_line = previous = line
                pending += 1
            elif heading_line and continues_heading(line, heading_line, previous):
                previous = line
            elif sections:
                heading_line = None
                sections[-1].lines.append(line)
    return sections, missing + headings[pending:]


def continues_heading(line: Line, heading_line: Line, previous: Line) -> bool:
    """A wrapped heading line: bold, about the same size, indented past the
    number and directly below the previous heading line."""
    return (
        line.bold
        and abs(line.size - heading_line.size) <= 1
        and line.x > heading_line.x + CONTINUATION_INDENT
        and line.column == previous.column
        and 0 < line.y - previous.y < CONTINUATION_GAP * line.size
    )
