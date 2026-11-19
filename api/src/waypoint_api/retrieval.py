"""Find the knowledge-base chunks that best answer a student's question.

Questions are embedded with the same model as the chunks (see
docs/EMBEDDINGS.md), and only chunks embedded with that model are searched.
"""

from collections.abc import Callable
from typing import Literal

import psycopg
import voyageai
from pydantic import BaseModel, Field

MODEL = "voyage-4-large"
DIMENSIONS = 1024

Exam = Literal["PSTAR", "PPAER", "FLIGHT_TEST"]
Subject = Literal["air-law", "navigation", "meteorology", "aeronautics", "flight-test"]
Jurisdiction = Literal["CA", "non-CA"]
EmbedQuery = Callable[[str], list[float]]


class RetrieveRequest(BaseModel):
    """A question and optional filters."""

    question: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=20)
    exam: Exam | None = None
    subject: Subject | None = None
    jurisdiction: Jurisdiction | None = None


class Passage(BaseModel):
    """A retrieved chunk with everything a citation needs."""

    chunk_id: str
    document_id: str
    document_title: str
    edition: str
    jurisdiction: Jurisdiction
    section_ref: str
    heading_path: list[str]
    page: int | None
    subject: Subject | None
    text: str
    score: float


def embed_query(question: str) -> list[float]:
    """Embed a question with Voyage AI. Reads VOYAGE_API_KEY."""
    result = voyageai.Client().embed(
        [question], model=MODEL, input_type="query", output_dimension=DIMENSIONS
    )
    return result.embeddings[0]


def retrieve(
    conn: psycopg.Connection, request: RetrieveRequest, vector: list[float]
) -> list[Passage]:
    """The chunks nearest the question vector (cosine), most similar first,
    within the requested exam, subject and jurisdiction."""
    rows = conn.execute(
        """
        SELECT c.id, d.id, d.title, d.edition, d.jurisdiction, c.section_ref,
               c.heading_path, c.page, c.subject, c.text,
               1 - (c.embedding <=> %(vector)s::vector) AS score
        FROM chunk c JOIN document d ON d.id = c.document_id
        WHERE c.embedding_model = %(model)s
          AND (%(exam)s::text IS NULL OR %(exam)s = ANY(d.exams))
          AND (%(subject)s::text IS NULL OR c.subject = %(subject)s)
          AND (%(jurisdiction)s::text IS NULL OR d.jurisdiction = %(jurisdiction)s)
        ORDER BY c.embedding <=> %(vector)s::vector
        LIMIT %(limit)s
        """,
        {
            "vector": vector,
            "model": MODEL,
            "exam": request.exam,
            "subject": request.subject,
            "jurisdiction": request.jurisdiction,
            "limit": request.limit,
        },
    ).fetchall()
    return [
        Passage(**dict(zip(Passage.model_fields, row, strict=True))) for row in rows
    ]
