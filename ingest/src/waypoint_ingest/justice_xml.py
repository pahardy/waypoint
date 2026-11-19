"""Split a Justice Laws regulation (XML) into one section per numbered section."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from waypoint_ingest.normalize import Paragraph, TextSection

RESERVED = re.compile(r"^\[Reserved[^\]]*\]$")


def regulation_sections(path: Path, prefix: str) -> list[TextSection]:
    """Sections of the regulation body in order, skipping repealed ones.

    `prefix` names the instrument in references, for example `CAR` gives
    `CAR 602.14`. Schedules are not included.
    """
    body = ET.parse(path).getroot().find("Body")
    headings: dict[int, str] = {}
    sections = []
    for element in body:
        if element.tag == "Heading":
            level = int(element.get("level"))
            headings = {k: v for k, v in headings.items() if k < level}
            headings[level] = heading_text(element)
        elif element.tag == "Section":
            ref = f"{prefix} {element.findtext('Label')}"
            paragraphs = provisions(element)
            if paragraphs:
                path_ = [headings[k] for k in sorted(headings)] + [ref]
                sections.append(TextSection(ref, path_, None, paragraphs))
    return sections


def heading_text(heading: ET.Element) -> str:
    """`PART I General Provisions`, or the title alone when it has no label."""
    title = " ".join("".join(heading.find("TitleText").itertext()).split())
    label = heading.findtext("Label")
    return f"{label} {title}" if label else title


def provisions(section: ET.Element) -> list[Paragraph]:
    """One paragraph per labelled provision or table row, in document order."""
    result = []
    for element in walk(section):
        if element.tag == "row":
            cells = [flat_text(entry) for entry in element.iter("entry")]
            result.append(Paragraph(None, " | ".join(c for c in cells if c)))
            continue
        text = element.find("Text")
        if text is None or text.find("Repealed") is not None:
            continue
        body = flat_text(text)
        if RESERVED.match(body):
            continue
        label = element.findtext("Label") if element.tag != "Section" else None
        result.append(Paragraph(None, f"{label} {body}" if label else body))
    return [p for p in result if p.text]


def walk(element: ET.Element):
    """Elements in document order, without historical notes. Table rows are
    yielded whole rather than descended into."""
    yield element
    for child in element:
        if child.tag in ("HistoricalNote", "Label", "MarginalNote", "Text"):
            continue
        if child.tag == "row":
            yield child
        else:
            yield from walk(child)


def flat_text(element: ET.Element) -> str:
    """All text inside an element, with whitespace collapsed."""
    return " ".join("".join(element.itertext()).split())
