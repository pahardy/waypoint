"""Turn a downloaded source into section text and chunks under data/."""

import json
from dataclasses import asdict
from pathlib import Path

from waypoint_ingest.chunk import Chunk, pack, token_count
from waypoint_ingest.extract import Heading, extract_sections
from waypoint_ingest.fetch import RAW_DIR
from waypoint_ingest.normalize import paragraphs
from waypoint_ingest.sources import REPO_ROOT, Source

TEXT_DIR = REPO_ROOT / "data" / "text"
CHUNKS_DIR = REPO_ROOT / "data" / "chunks"


def build_chunks(
    source: Source, pdf: Path
) -> tuple[list[dict], list[Chunk], list[Heading]]:
    """Return section records, chunks, and headings that were not found."""
    sections, missing = extract_sections(pdf)
    records, chunks = [], []
    for section in sections:
        heading = section.heading
        body = paragraphs(section.lines)
        records.append(
            {
                "source_id": source.id,
                "section_ref": heading.ref,
                "heading_path": heading.path,
                "page": heading.page,
                "paragraphs": [asdict(p) for p in body],
            }
        )
        for index, piece in enumerate(pack(body)):
            chunks.append(
                Chunk(
                    id=f"{source.id}:{heading.ref}:{index}",
                    source_id=source.id,
                    edition=source.edition,
                    jurisdiction=source.jurisdiction,
                    section_ref=heading.ref,
                    heading_path=heading.path,
                    page=piece.page,
                    text=piece.text,
                    token_count=token_count(piece.text),
                )
            )
    return records, chunks, missing


def chunk_source(
    source: Source, raw_dir: Path = RAW_DIR
) -> tuple[list[Chunk], list[Heading]]:
    """Chunk one downloaded PDF source and write data/text and data/chunks."""
    pdf = raw_dir / source.id / f"{source.id}.pdf"
    records, chunks, missing = build_chunks(source, pdf)
    write_jsonl(TEXT_DIR / f"{source.id}.jsonl", records)
    write_jsonl(CHUNKS_DIR / f"{source.id}.jsonl", [c.model_dump() for c in chunks])
    return chunks, missing


def write_jsonl(path: Path, records: list[dict]) -> None:
    """Write one JSON object per line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = (json.dumps(r, ensure_ascii=False) for r in records)
    path.write_text("\n".join(lines) + "\n")
