"""Turn a downloaded source into section text and chunks under data/."""

import json
from dataclasses import asdict
from pathlib import Path

from waypoint_ingest.chunk import Chunk, pack, token_count
from waypoint_ingest.extract import Heading, extract_sections
from waypoint_ingest.fetch import RAW_DIR
from waypoint_ingest.html_sections import html_sections
from waypoint_ingest.justice_xml import regulation_sections
from waypoint_ingest.normalize import TextSection, paragraphs
from waypoint_ingest.pages import has_outline, page_sections
from waypoint_ingest.sources import REPO_ROOT, Source

TEXT_DIR = REPO_ROOT / "data" / "text"
CHUNKS_DIR = REPO_ROOT / "data" / "chunks"


def pdf_sections(pdf: Path) -> tuple[list[TextSection], list[Heading]]:
    """Sections of an outlined PDF, and bookmarks whose heading was not found."""
    sections, missing = extract_sections(pdf)
    return [
        TextSection(s.heading.ref, s.heading.path, s.heading.page, paragraphs(s.lines))
        for s in sections
    ], missing


def source_sections(
    source: Source, raw_dir: Path
) -> tuple[list[TextSection], list[Heading]]:
    """Read a downloaded source into sections, by its format."""
    path = raw_dir / source.id / f"{source.id}.{source.format}"
    if source.format == "pdf" and has_outline(path):
        return pdf_sections(path)
    if source.format == "pdf":
        return page_sections(path, source.section_prefix, source.title), []
    if source.format == "xml":
        return regulation_sections(path, source.section_prefix), []
    if source.format == "html":
        return html_sections(path, source.section_prefix), []
    raise ValueError(f"{source.id}: chunking {source.format} is not supported yet")


def build_chunks(
    source: Source, sections: list[TextSection]
) -> tuple[list[dict], list[Chunk]]:
    """Section records for data/text and chunks for data/chunks."""
    records, chunks = [], []
    for section in sections:
        records.append(
            {
                "source_id": source.id,
                "section_ref": section.ref,
                "heading_path": section.heading_path,
                "page": section.page,
                "paragraphs": [asdict(p) for p in section.paragraphs],
            }
        )
        for index, piece in enumerate(pack(section.paragraphs)):
            chunks.append(
                Chunk(
                    id=f"{source.id}:{section.ref}:{index}",
                    source_id=source.id,
                    edition=source.edition,
                    jurisdiction=source.jurisdiction,
                    section_ref=section.ref,
                    heading_path=section.heading_path,
                    page=piece.page,
                    text=piece.text,
                    token_count=token_count(piece.text),
                )
            )
    return records, chunks


def chunk_source(
    source: Source, raw_dir: Path = RAW_DIR
) -> tuple[list[Chunk], list[Heading]]:
    """Chunk one downloaded source and write data/text and data/chunks."""
    sections, missing = source_sections(source, raw_dir)
    records, chunks = build_chunks(source, sections)
    write_jsonl(TEXT_DIR / f"{source.id}.jsonl", records)
    write_jsonl(CHUNKS_DIR / f"{source.id}.jsonl", [c.model_dump() for c in chunks])
    return chunks, missing


def write_jsonl(path: Path, records: list[dict]) -> None:
    """Write one JSON object per line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = (json.dumps(r, ensure_ascii=False) for r in records)
    path.write_text("\n".join(lines) + "\n")
