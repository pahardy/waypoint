"""Load a source's chunks and their embeddings into PostgreSQL."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import psycopg

from waypoint_ingest.chunk import Chunk
from waypoint_ingest.embeddings import MODEL, InputType
from waypoint_ingest.sources import Source

Embed = Callable[[list[str], InputType], list[list[float]]]


@dataclass
class LoadResult:
    """How many chunks were embedded, left as they were, or removed."""

    embedded: int
    unchanged: int
    removed: int


def read_chunks(path: Path) -> list[Chunk]:
    """Read chunks written by `ingest chunk`.

    Records are split on newlines only: chunk text can contain other line
    separators, such as U+2029, that `str.splitlines` would also split on.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    return [Chunk.model_validate_json(line) for line in lines if line]


def embedding_text(chunk: Chunk) -> str:
    """The heading path gives short chunks the context they lack on their own."""
    return " > ".join(chunk.heading_path) + "\n\n" + chunk.text


def load_source(
    conn: psycopg.Connection,
    source: Source,
    meta: dict,
    chunks: list[Chunk],
    embed: Embed,
    model: str = MODEL,
) -> LoadResult:
    """Upsert the document and its chunks in one transaction.

    Only new or changed chunks are embedded, so re-running is cheap and
    never creates duplicates. Chunks no longer produced are removed.
    """
    with conn.transaction():
        upsert_document(conn, source, meta)
        stored = {
            row[0]: (row[1], row[2], row[3])
            for row in conn.execute(
                "SELECT id, text, heading_path, embedding_model FROM chunk"
                " WHERE document_id = %s",
                (source.id,),
            )
        }
        changed = [
            c for c in chunks if stored.get(c.id) != (c.text, c.heading_path, model)
        ]
        vectors = embed([embedding_text(c) for c in changed], "document")
        for chunk, vector in zip(changed, vectors, strict=True):
            upsert_chunk(conn, chunk, model, vector)
        removed = conn.execute(
            "DELETE FROM chunk WHERE document_id = %s AND NOT (id = ANY(%s))",
            (source.id, [c.id for c in chunks]),
        ).rowcount
    return LoadResult(len(changed), len(chunks) - len(changed), removed)


def upsert_document(conn: psycopg.Connection, source: Source, meta: dict) -> None:
    """Insert or refresh the document row from the manifest and fetch record."""
    conn.execute(
        """
        INSERT INTO document (id, title, publisher, tp_number, edition, published,
                              retrieved_on, jurisdiction, url, sha256)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            title = excluded.title, publisher = excluded.publisher,
            tp_number = excluded.tp_number, edition = excluded.edition,
            published = excluded.published, retrieved_on = excluded.retrieved_on,
            jurisdiction = excluded.jurisdiction, url = excluded.url,
            sha256 = excluded.sha256
        """,
        (
            source.id,
            source.title,
            source.publisher,
            source.tp_number,
            source.edition,
            source.published,
            meta["retrieved_on"],
            source.jurisdiction,
            str(source.url),
            meta["sha256"],
        ),
    )


def upsert_chunk(
    conn: psycopg.Connection, chunk: Chunk, model: str, vector: list[float]
) -> None:
    """Insert or replace one chunk and its embedding."""
    conn.execute(
        """
        INSERT INTO chunk (id, document_id, section_ref, heading_path, page, text,
                           token_count, embedding_model, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
        ON CONFLICT (id) DO UPDATE SET
            section_ref = excluded.section_ref, heading_path = excluded.heading_path,
            page = excluded.page, text = excluded.text,
            token_count = excluded.token_count,
            embedding_model = excluded.embedding_model,
            embedding = excluded.embedding
        """,
        (
            chunk.id,
            chunk.source_id,
            chunk.section_ref,
            chunk.heading_path,
            chunk.page,
            chunk.text,
            chunk.token_count,
            model,
            vector,
        ),
    )


def search(
    conn: psycopg.Connection, query: str, embed: Embed, limit: int = 5
) -> list[tuple[str, str, float, str]]:
    """Nearest chunks to a question: (id, edition, similarity, text)."""
    return [
        (hit.id, hit.edition, hit.similarity, hit.text)
        for hit in nearest(conn, embed([query], "query")[0], limit)
    ]


@dataclass
class Hit:
    """One retrieved chunk."""

    id: str
    document_id: str
    section_ref: str
    edition: str
    similarity: float
    text: str

    @property
    def section_key(self) -> str:
        """Source and section, for example `tc-aim:RAC 4.4.8`."""
        return f"{self.document_id}:{self.section_ref}"


def nearest(
    conn: psycopg.Connection,
    vector: list[float],
    limit: int,
    jurisdiction: str | None = None,
) -> list[Hit]:
    """Chunks nearest a query vector, most similar first (cosine), optionally
    only from sources of one jurisdiction (`CA` or `non-CA`)."""
    rows = conn.execute(
        """
        SELECT c.id, c.document_id, c.section_ref, d.edition,
               1 - (c.embedding <=> %s::vector) AS similarity, c.text
        FROM chunk c JOIN document d ON d.id = c.document_id
        WHERE %s::text IS NULL OR d.jurisdiction = %s
        ORDER BY c.embedding <=> %s::vector
        LIMIT %s
        """,
        (vector, jurisdiction, jurisdiction, vector, limit),
    ).fetchall()
    return [Hit(*row) for row in rows]


def read_meta(raw_dir: Path, source_id: str) -> dict:
    """The fetch record: retrieval date and SHA-256 of the downloaded file."""
    return json.loads((raw_dir / source_id / "meta.json").read_text())
