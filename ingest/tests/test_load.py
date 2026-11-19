import hashlib
import random

from waypoint_ingest.chunk import Chunk
from waypoint_ingest.embeddings import DIMENSIONS
from waypoint_ingest.load import load_source, read_chunks
from waypoint_ingest.pipeline import write_jsonl
from waypoint_ingest.sources import Source

META = {"retrieved_on": "2026-11-18", "sha256": "abc123"}
SOURCE = Source(
    id="aim",
    title="Test manual",
    publisher="Transport Canada",
    tp_number="TP 1",
    edition="2026-2",
    published="2026-10",
    url="https://example.org/aim.pdf",
    jurisdiction="CA",
    format="pdf",
    priority=1,
    exams=["PSTAR"],
    licence="test",
)


class StubEmbed:
    """Fixed vectors derived from the text, recording each call."""

    def __init__(self):
        self.calls = []

    def __call__(self, texts, input_type):
        self.calls.append((list(texts), input_type))
        return [vector(text) for text in texts]


def vector(text):
    seed = hashlib.sha256(text.encode()).digest()
    rng = random.Random(seed)
    return [rng.uniform(-1, 1) for _ in range(DIMENSIONS)]


def chunk(ref, text):
    return Chunk(
        id=f"aim:{ref}:0",
        source_id="aim",
        edition="2026-2",
        jurisdiction="CA",
        section_ref=ref,
        heading_path=["RAC—Rules", ref],
        page=1,
        text=text,
        token_count=len(text.split()),
    )


CHUNKS = [
    chunk("RAC 1.1", "Altimeter setting."),
    chunk("RAC 1.2", "Cruising altitudes."),
]


def count(conn, table):
    return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def test_load_writes_document_and_chunks(conn):
    result = load_source(conn, SOURCE, META, CHUNKS, StubEmbed(), model="stub")
    assert (result.embedded, result.unchanged, result.removed) == (2, 0, 0)
    assert count(conn, "document") == 1
    assert count(conn, "chunk") == 2
    row = conn.execute("SELECT edition, sha256, jurisdiction FROM document").fetchone()
    assert row == ("2026-2", "abc123", "CA")


def test_documents_are_embedded_with_their_heading_path(conn):
    stub = StubEmbed()
    load_source(conn, SOURCE, META, CHUNKS[:1], stub, model="stub")
    assert stub.calls == [(["RAC—Rules > RAC 1.1\n\nAltimeter setting."], "document")]


def test_reloading_creates_no_duplicates_and_embeds_nothing(conn):
    load_source(conn, SOURCE, META, CHUNKS, StubEmbed(), model="stub")
    stub = StubEmbed()
    result = load_source(conn, SOURCE, META, CHUNKS, stub, model="stub")
    assert (result.embedded, result.unchanged) == (0, 2)
    assert stub.calls == [([], "document")]
    assert count(conn, "document") == 1
    assert count(conn, "chunk") == 2


def test_only_changed_chunks_are_embedded_again(conn):
    load_source(conn, SOURCE, META, CHUNKS, StubEmbed(), model="stub")
    edited = [CHUNKS[0], chunk("RAC 1.2", "Cruising altitudes, revised.")]
    result = load_source(conn, SOURCE, META, edited, StubEmbed(), model="stub")
    assert (result.embedded, result.unchanged) == (1, 1)


def test_a_new_model_embeds_everything_again(conn):
    load_source(conn, SOURCE, META, CHUNKS, StubEmbed(), model="stub")
    result = load_source(conn, SOURCE, META, CHUNKS, StubEmbed(), model="stub-2")
    assert result.embedded == 2


def test_chunks_no_longer_produced_are_removed(conn):
    load_source(conn, SOURCE, META, CHUNKS, StubEmbed(), model="stub")
    result = load_source(conn, SOURCE, META, CHUNKS[:1], StubEmbed(), model="stub")
    assert result.removed == 1
    assert count(conn, "chunk") == 1


def test_chunks_with_unicode_line_separators_read_back_intact(tmp_path):
    chunks = [chunk("COM 4.7", "capability. For collocated sites"), CHUNKS[0]]
    path = tmp_path / "aim.jsonl"
    write_jsonl(path, [c.model_dump() for c in chunks])
    assert read_chunks(path) == chunks
