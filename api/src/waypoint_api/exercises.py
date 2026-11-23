"""Oral and scenario exercises: YAML files in content/exercises/, each with a
prompt, sources and a weighted rubric. The score is calculated in code."""

import math
from pathlib import Path
from typing import Literal

import psycopg
import yaml
from pydantic import BaseModel, Field

from waypoint_api.retrieval import Passage

EXERCISES_DIR = Path(__file__).resolve().parents[3] / "content" / "exercises"
DISCLAIMER = "Educational simulation. Not operational guidance."

Mark = Literal["met", "partly_met", "not_met"]
CREDIT = {"met": 1.0, "partly_met": 0.5, "not_met": 0.0}


class Criterion(BaseModel):
    """One thing a good answer must cover."""

    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    weight: int = Field(gt=0)
    key_points: list[str] = Field(min_length=1)


class Exercise(BaseModel):
    """An oral question and the rubric its answers are graded against."""

    id: str = Field(min_length=1)
    exam: Literal["PSTAR", "PPAER", "FLIGHT_TEST"]
    objective_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    sources: list[str] = Field(min_length=1)
    rubric: list[Criterion] = Field(min_length=1)


def load_exercise(exercise_id: str, directory: Path = EXERCISES_DIR) -> Exercise:
    """Read and validate one exercise file."""
    path = directory / f"{exercise_id}.yaml"
    return Exercise(**yaml.safe_load(path.read_text()))


SOURCE_PASSAGES = """
    SELECT c.id, d.id, d.title, d.edition, d.jurisdiction, c.section_ref,
           c.heading_path, c.page, c.subject, c.text, 1.0
    FROM chunk c JOIN document d ON d.id = c.document_id
    WHERE c.id = ANY(%s) ORDER BY c.id
"""


def source_passages(conn: psycopg.Connection, exercise: Exercise) -> list[Passage]:
    """The exercise's cited passages. Raises ValueError if any is missing
    from the knowledge base."""
    rows = conn.execute(SOURCE_PASSAGES, (exercise.sources,)).fetchall()
    passages = [Passage(**dict(zip(Passage.model_fields, row))) for row in rows]
    missing = set(exercise.sources) - {p.chunk_id for p in passages}
    if missing:
        raise ValueError(f"{exercise.id}: sources not in the knowledge base: {missing}")
    return passages


def score(rubric: list[Criterion], marks: dict[str, Mark]) -> int:
    """The weighted score as a whole percentage, halves rounded up (62.5
    gives 63; Python's round() would give 62)."""
    total = sum(c.weight for c in rubric)
    earned = sum(c.weight * CREDIT[marks[c.id]] for c in rubric)
    return math.floor(100 * earned / total + 0.5)
