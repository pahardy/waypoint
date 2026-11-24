"""Oral and scenario exercises: YAML files in content/exercises/, each with a
prompt, sources and a weighted rubric. The score is calculated in code."""

import math
from pathlib import Path
from typing import Literal

import psycopg
import yaml
from pydantic import BaseModel, Field, field_validator

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


class Stage(BaseModel):
    """One stage of a scenario: the facts it reveals, its question and rubric."""

    id: str = Field(min_length=1)
    facts: list[str] = Field(min_length=1)
    question: str = Field(min_length=1)
    rubric: list[Criterion] = Field(min_length=1)


class Scenario(BaseModel):
    """A staged situation; each stage's answer is graded on its own rubric."""

    id: str = Field(min_length=1)
    exam: Literal["PSTAR", "PPAER", "FLIGHT_TEST"]
    objective_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    sources: list[str] = Field(min_length=1)
    stages: list[Stage] = Field(min_length=2)

    @field_validator("stages")
    @classmethod
    def unique_stage_ids(cls, stages: list[Stage]) -> list[Stage]:
        """Stage ids must be unique."""
        ids = [s.id for s in stages]
        if len(set(ids)) != len(ids):
            raise ValueError(f"repeated stage ids: {ids}")
        return stages


def read(exercise_id: str, directory: Path) -> dict:
    """The parsed YAML of one exercise file."""
    return yaml.safe_load((directory / f"{exercise_id}.yaml").read_text())


def load_exercise(exercise_id: str, directory: Path = EXERCISES_DIR) -> Exercise:
    """Read and validate one oral exercise file."""
    return Exercise(**read(exercise_id, directory))


def load_scenario(scenario_id: str, directory: Path = EXERCISES_DIR) -> Scenario:
    """Read and validate one scenario file."""
    return Scenario(**read(scenario_id, directory))


SOURCE_PASSAGES = """
    SELECT c.id, d.id, d.title, d.edition, d.jurisdiction, c.section_ref,
           c.heading_path, c.page, c.subject, c.text, 1.0
    FROM chunk c JOIN document d ON d.id = c.document_id
    WHERE c.id = ANY(%s) ORDER BY c.id
"""


def source_passages(
    conn: psycopg.Connection, exercise: Exercise | Scenario
) -> list[Passage]:
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
