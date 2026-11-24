"""Exercise sessions: the `exercise_session` and `stage_answer` tables.

An oral exercise runs as a session with one stage; a scenario has one stage
per scenario stage. The session holds the current stage, so a reload
continues where the student left off.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

import psycopg
import yaml
from psycopg.types.json import Jsonb
from pydantic import BaseModel

from waypoint_api import llm
from waypoint_api.exercises import (
    EXERCISES_DIR,
    Exercise,
    Scenario,
    load_exercise,
    load_scenario,
)
from waypoint_api.grading import grade
from waypoint_api.retrieval import Passage
from waypoint_api.scenarios import (
    SYNTHETIC,
    ScenarioState,
    overall_score,
    stage_exercise,
)

ExerciseKind = Literal["oral", "scenario"]


class ExerciseSummary(BaseModel):
    """An exercise as listed for the student."""

    id: str
    kind: ExerciseKind
    exam: str
    prompt: str


class StageView(BaseModel):
    """The current stage: the facts it reveals and its question."""

    index: int
    id: str
    facts: list[str]
    question: str


class GradedMark(BaseModel):
    """A criterion's mark, with the criterion it was given against."""

    criterion_id: str
    description: str
    weight: int
    mark: str
    evidence: str
    reason: str


class GradedStage(BaseModel):
    """A stage the student has answered, with its marks and score."""

    index: int
    id: str
    question: str
    answer: str
    marks: list[GradedMark]
    score: int


class SessionState(BaseModel):
    """Everything the exercise page needs, after a start, answer or reload."""

    id: UUID
    exercise_id: str
    kind: ExerciseKind
    exam: str
    intro: str | None
    synthetic_notice: str | None
    stage_count: int
    current: StageView | None
    revealed: list[str]
    graded: list[GradedStage]
    overall_score: int | None


class SessionError(Exception):
    """The session cannot take this answer."""


def load_any(exercise_id: str) -> Exercise | Scenario:
    """An exercise file: a scenario if it has stages, else an oral exercise."""
    data = yaml.safe_load((EXERCISES_DIR / f"{exercise_id}.yaml").read_text())
    if "stages" in data:
        return load_scenario(exercise_id)
    return load_exercise(exercise_id)


def exercise_ids() -> list[str]:
    """The ids of every exercise file."""
    return sorted(path.stem for path in EXERCISES_DIR.glob("*.yaml"))


def kind(exercise: Exercise | Scenario) -> ExerciseKind:
    """Oral exercise or scenario."""
    return "scenario" if isinstance(exercise, Scenario) else "oral"


def summaries() -> list[ExerciseSummary]:
    """Every exercise, for the list page."""
    return [
        ExerciseSummary(id=e.id, kind=kind(e), exam=e.exam, prompt=e.prompt)
        for e in map(load_any, exercise_ids())
    ]


def stage_count(exercise: Exercise | Scenario) -> int:
    """How many answers the exercise asks for."""
    return len(exercise.stages) if isinstance(exercise, Scenario) else 1


def stage_view(exercise: Exercise | Scenario, index: int) -> StageView:
    """The stage at index as the student sees it."""
    if isinstance(exercise, Exercise):
        return StageView(index=0, id="answer", facts=[], question=exercise.prompt)
    stage = exercise.stages[index]
    return StageView(
        index=index, id=stage.id, facts=stage.facts, question=stage.question
    )


def grading_exercise(exercise: Exercise | Scenario, index: int) -> Exercise:
    """What the grader grades the stage at index against."""
    if isinstance(exercise, Exercise):
        return exercise
    return stage_exercise(ScenarioState(exercise, index))


def revealed(exercise: Exercise | Scenario, index: int) -> list[str]:
    """Facts revealed up to the stage at index (all of them once finished)."""
    if isinstance(exercise, Exercise):
        return []
    return ScenarioState(exercise, min(index, len(exercise.stages) - 1)).revealed()


def start(conn: psycopg.Connection, exercise_id: str, now: datetime) -> UUID:
    """Start a session on an exercise. Raises FileNotFoundError if there is
    no such exercise."""
    load_any(exercise_id)
    row = conn.execute(
        "INSERT INTO exercise_session (exercise_id, started_at) VALUES (%s, %s) "
        "RETURNING id",
        (exercise_id, now),
    ).fetchone()
    return row[0]


def load(conn: psycopg.Connection, session_id: UUID) -> SessionState | None:
    """A session's state, or None if there is no such session."""
    row = conn.execute(
        "SELECT exercise_id, stage_index FROM exercise_session WHERE id = %s",
        (session_id,),
    ).fetchone()
    if row is None:
        return None
    exercise_id, index = row
    exercise = load_any(exercise_id)
    count = stage_count(exercise)
    answers = conn.execute(
        "SELECT stage_index, answer, marks, score FROM stage_answer "
        "WHERE session_id = %s ORDER BY stage_index",
        (session_id,),
    ).fetchall()
    graded = [graded_stage(exercise, *answer) for answer in answers]
    finished = index == count
    return SessionState(
        id=session_id,
        exercise_id=exercise_id,
        kind=kind(exercise),
        exam=exercise.exam,
        intro=exercise.prompt if isinstance(exercise, Scenario) else None,
        synthetic_notice=SYNTHETIC if isinstance(exercise, Scenario) else None,
        stage_count=count,
        current=None if finished else stage_view(exercise, index),
        revealed=revealed(exercise, index),
        graded=graded,
        overall_score=overall_score([g.score for g in graded]) if finished else None,
    )


def graded_stage(
    exercise: Exercise | Scenario, index: int, answer: str, marks: list, score: int
) -> GradedStage:
    """A stored answer joined with its stage's question and rubric."""
    rubric = {c.id: c for c in grading_exercise(exercise, index).rubric}
    view = stage_view(exercise, index)
    return GradedStage(
        index=index,
        id=view.id,
        question=view.question,
        answer=answer,
        marks=[
            GradedMark(
                description=rubric[m["criterion_id"]].description,
                weight=rubric[m["criterion_id"]].weight,
                **m,
            )
            for m in marks
        ],
        score=score,
    )


def answer(
    conn: psycopg.Connection,
    session_id: UUID,
    text: str,
    passages: list[Passage],
    parse: llm.Parse,
    now: datetime,
) -> None:
    """Grade the current stage's answer, store it and advance. Raises
    SessionError if the session is finished. Grading errors propagate before
    anything is stored."""
    exercise_id, index = conn.execute(
        "SELECT exercise_id, stage_index FROM exercise_session WHERE id = %s",
        (session_id,),
    ).fetchone()
    exercise = load_any(exercise_id)
    count = stage_count(exercise)
    if index == count:
        raise SessionError("This exercise is finished.")
    graded = grade(grading_exercise(exercise, index), passages, text, parse)
    marks = [m.model_dump() for m in graded.marks]
    with conn.transaction():
        conn.execute(
            "INSERT INTO stage_answer "
            "(session_id, stage_index, answer, marks, score, graded_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (session_id, index, text, Jsonb(marks), graded.score, now),
        )
        conn.execute(
            "UPDATE exercise_session SET stage_index = %s, finished_at = %s "
            "WHERE id = %s",
            (index + 1, now if index + 1 == count else None, session_id),
        )
