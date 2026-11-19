"""Find the chunks that best answer a question: vector, keyword or hybrid."""

from dataclasses import dataclass, replace
from typing import Literal

import psycopg

from waypoint_ingest.load import Embed

Method = Literal["vector", "keyword", "hybrid"]
CANDIDATES = 50
RRF_K = 60
SELECT = """
    SELECT c.id, c.document_id, c.section_ref, d.edition, {score} AS score, c.text
    FROM chunk c JOIN document d ON d.id = c.document_id
"""


@dataclass
class Hit:
    """One retrieved chunk and its score under the method that found it."""

    id: str
    document_id: str
    section_ref: str
    edition: str
    score: float
    text: str

    @property
    def section_key(self) -> str:
        """Source and section, for example `tc-aim:RAC 4.4.8`."""
        return f"{self.document_id}:{self.section_ref}"


def vector_hits(conn: psycopg.Connection, vector: list[float], limit: int) -> list[Hit]:
    """Nearest chunks by cosine similarity (score 1 is identical)."""
    rows = conn.execute(
        SELECT.format(score="1 - (c.embedding <=> %s::vector)")
        + "ORDER BY c.embedding <=> %s::vector LIMIT %s",
        (vector, vector, limit),
    ).fetchall()
    return [Hit(*row) for row in rows]


def keyword_hits(conn: psycopg.Connection, question: str, limit: int) -> list[Hit]:
    """Chunks sharing words with the question, ranked by PostgreSQL full-text
    cover density. Any word may match: a question's words are ORed, not ANDed."""
    rows = conn.execute(
        "WITH q AS (SELECT replace(plainto_tsquery('english', %s)::text, '&', '|')"
        "::tsquery AS query) "
        + SELECT.format(score="ts_rank_cd(c.search, q.query, 1)")
        + "CROSS JOIN q WHERE c.search @@ q.query ORDER BY score DESC LIMIT %s",
        (question, limit),
    ).fetchall()
    return [Hit(*row) for row in rows]


def fuse(rankings: list[list[Hit]], limit: int) -> list[Hit]:
    """Reciprocal rank fusion: each list adds 1 / (60 + rank) to a chunk."""
    scores: dict[str, float] = {}
    hits: dict[str, Hit] = {}
    for ranking in rankings:
        for rank, hit in enumerate(ranking, start=1):
            scores[hit.id] = scores.get(hit.id, 0.0) + 1 / (RRF_K + rank)
            hits.setdefault(hit.id, hit)
    best = sorted(scores, key=lambda chunk_id: scores[chunk_id], reverse=True)
    return [replace(hits[i], score=scores[i]) for i in best[:limit]]


def search(
    conn: psycopg.Connection, question: str, embed: Embed, method: Method, limit: int
) -> list[Hit]:
    """Embed a question and retrieve its top chunks."""
    return retrieve(conn, method, question, embed([question], "query")[0], limit)


def retrieve(
    conn: psycopg.Connection,
    method: Method,
    question: str,
    vector: list[float],
    limit: int,
) -> list[Hit]:
    """The top chunks for a question by the chosen method."""
    if method == "vector":
        return vector_hits(conn, vector, limit)
    if method == "keyword":
        return keyword_hits(conn, question, limit)
    return fuse(
        [
            vector_hits(conn, vector, CANDIDATES),
            keyword_hits(conn, question, CANDIDATES),
        ],
        limit,
    )
