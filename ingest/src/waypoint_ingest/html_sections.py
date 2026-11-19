"""Split a government web page into sections at its h2 to h4 headings."""

from pathlib import Path

from bs4 import BeautifulSoup, Tag

from waypoint_ingest.normalize import Paragraph, TextSection

SECTION_HEADINGS = ["h2", "h3", "h4"]
BLOCKS = [
    "p",
    "li",
    "tr",
    "dt",
    "dd",
    "h5",
    "h6",
    "caption",
    "pre",
    "figcaption",
    "div",
]
SKIPPED_SECTIONS = {"table of contents"}


def html_sections(path: Path, prefix: str) -> list[TextSection]:
    """Sections of the page's main content in order.

    A section is cited by its heading path below the page title, for
    example `STD 421 Division I - General / 421.05 Recency Requirements`,
    because headings such as "1. Prerequisites" repeat on some pages.
    """
    main = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser").find("main")
    title = flat(main.find("h1"))
    headings: dict[int, str] = {}
    sections: list[TextSection] = []
    current: TextSection | None = None
    for element in main.find_all(SECTION_HEADINGS + BLOCKS):
        if element.name in SECTION_HEADINGS:
            level = int(element.name[1])
            headings = {k: v for k, v in headings.items() if k < level}
            current = None
            if flat(element).lower() in SKIPPED_SECTIONS:
                continue
            headings[level] = flat(element)
            path_ = [headings[k] for k in sorted(headings)]
            current = TextSection(
                f"{prefix} {' / '.join(path_)}", [title, *path_], None, []
            )
            sections.append(current)
        elif current is not None:
            text = own_text(element)
            if text:
                current.paragraphs.append(Paragraph(None, text))
    return [s for s in sections if s.paragraphs]


def own_text(element: Tag) -> str:
    """Text that belongs to this block and not to a block nested inside it,
    so nested paragraphs are read once. A div gives only its loose text.
    Table rows join their cells with ` | `."""
    if element.name == "tr":
        cells = [own_strings(cell, element) for cell in element.find_all(["th", "td"])]
        return " | ".join(c for c in cells if c)
    return own_strings(element, element)


def own_strings(within: Tag, block: Tag) -> str:
    """Strings inside `within` whose nearest block is `block`."""
    strings = [
        s for s in within.find_all(string=True) if s.find_parent(BLOCKS) is block
    ]
    return " ".join("".join(strings).split())


def flat(element: Tag) -> str:
    """All text in an element, whitespace collapsed."""
    return " ".join(element.get_text(" ").split())
