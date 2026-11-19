"""Measure retrieval quality on the hand-written eval set (recall@5, MRR@10)."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import psycopg
import yaml
from pydantic import BaseModel

from waypoint_ingest.embeddings import MODEL
from waypoint_ingest.load import Embed, Hit, nearest
from waypoint_ingest.sources import REPO_ROOT

QUESTIONS_FILE = REPO_ROOT / "ingest" / "eval" / "retrieval.yaml"
EVALS_DIR = REPO_ROOT / "docs" / "evals"
RECALL_K = 5
MRR_K = 10


class Question(BaseModel):
    """A student question and the sections (`source:section`) that answer it."""

    id: str
    exam: str
    subject: str
    question: str
    expected: list[str]


@dataclass
class Outcome:
    """Where the first correct section ranked, and what came back."""

    question: Question
    rank: int | None
    hits: list[Hit]


def load_questions(path: Path = QUESTIONS_FILE) -> list[Question]:
    """Load the eval set. Ids must be unique."""
    questions = [Question(**item) for item in yaml.safe_load(path.read_text())]
    ids = [q.id for q in questions]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        raise ValueError(f"duplicate question ids: {sorted(duplicates)}")
    return questions


def first_rank(hits: list[Hit], expected: list[str]) -> int | None:
    """1-based rank of the first hit from an expected section, or None."""
    for rank, hit in enumerate(hits, start=1):
        if hit.section_key in expected:
            return rank
    return None


def recall_at(ranks: list[int | None], k: int) -> float:
    """Share of questions with a correct section in the top k."""
    return sum(r is not None and r <= k for r in ranks) / len(ranks)


def mean_reciprocal_rank(ranks: list[int | None], k: int) -> float:
    """Mean of 1/rank, counting misses and ranks beyond k as 0."""
    return sum(1 / r for r in ranks if r is not None and r <= k) / len(ranks)


def unknown_sections(conn: psycopg.Connection, questions: list[Question]) -> set[str]:
    """Expected sections that have no chunks in the database."""
    stored = {
        f"{row[0]}:{row[1]}"
        for row in conn.execute("SELECT DISTINCT document_id, section_ref FROM chunk")
    }
    return {e for q in questions for e in q.expected} - stored


def evaluate(
    conn: psycopg.Connection,
    questions: list[Question],
    embed: Embed,
    jurisdiction: str | None = None,
) -> list[Outcome]:
    """Retrieve the top chunks for every question and rank the first hit."""
    unknown = unknown_sections(conn, questions)
    if unknown:
        raise ValueError(f"expected sections not in the database: {sorted(unknown)}")
    vectors = embed([q.question for q in questions], "query")
    outcomes = []
    for question, vector in zip(questions, vectors, strict=True):
        hits = nearest(conn, vector, MRR_K, jurisdiction)
        outcomes.append(Outcome(question, first_rank(hits, question.expected), hits))
    return outcomes


def scores(outcomes: list[Outcome]) -> tuple[float, float]:
    """Recall@5 and MRR@10."""
    ranks = [o.rank for o in outcomes]
    return recall_at(ranks, RECALL_K), mean_reciprocal_rank(ranks, MRR_K)


def report_path(
    sources: list[str], run_on: date, jurisdiction: str | None = None
) -> Path:
    """`docs/evals/retrieval-<date>-<sources>.md`, so runs over different
    sources on the same day do not overwrite each other."""
    only = f"-{jurisdiction}-only" if jurisdiction else ""
    return EVALS_DIR / f"retrieval-{run_on.isoformat()}-{'-'.join(sources)}{only}.md"


def report(
    outcomes: list[Outcome],
    sources: list[str],
    chunk_count: int,
    run_on: date,
    jurisdiction: str | None = None,
) -> str:
    """A Markdown report: overall and per-subject scores, then every miss."""
    recall, mrr = scores(outcomes)
    lines = [
        f"# Retrieval Eval: {run_on.isoformat()}",
        "",
        f"- Model: `{MODEL}`, vector search only (cosine)",
        f"- Questions: {len(outcomes)} (`ingest/eval/retrieval.yaml`)",
        f"- Sources: {', '.join(sources)} ({chunk_count} chunks)"
        + (f", {jurisdiction} only" if jurisdiction else ""),
        "",
        f"| Subject | Questions | Recall@{RECALL_K} | MRR@{MRR_K} |",
        "|---|---|---|---|",
    ]
    for subject in dict.fromkeys(o.question.subject for o in outcomes):
        group = [o for o in outcomes if o.question.subject == subject]
        r, m = scores(group)
        lines.append(f"| {subject} | {len(group)} | {r:.2f} | {m:.2f} |")
    lines.append(
        f"| **all** | **{len(outcomes)}** | **{recall:.2f}** | **{mrr:.2f}** |"
    )
    lines += ["", f"## Not in the top {RECALL_K}", ""]
    misses = [o for o in outcomes if o.rank is None or o.rank > RECALL_K]
    if not misses:
        lines.append("None.")
    for o in misses:
        rank = "not in top 10" if o.rank is None else f"rank {o.rank}"
        top = ", ".join(h.section_ref for h in o.hits[:3])
        expected = ", ".join(e.split(":", 1)[1] for e in o.question.expected)
        lines.append(
            f"- **{o.question.id}** ({rank}): {o.question.question}"
            f" Expected {expected}; top 3 were {top}."
        )
    return "\n".join(lines) + "\n"
