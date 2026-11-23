"""Quizzes and mock exams: the `attempt` and `attempt_item` tables."""

import random
from collections import defaultdict
from datetime import datetime
from typing import Literal, NamedTuple
from uuid import UUID

import psycopg
from psycopg.rows import namedtuple_row
from pydantic import BaseModel

from waypoint_api import exams

Kind = Literal["quiz", "mock"]


class AttemptQuestion(BaseModel):
    """A question as the student sees it during an attempt: no answer."""

    position: int
    question_id: str
    number: str | None
    objective_id: str
    topic: str
    stem: str
    choices: list[str]
    origin: Literal["official", "generated"]
    chosen_index: int | None


class Attempt(BaseModel):
    """An attempt in progress or submitted."""

    id: UUID
    kind: Kind
    exam: str
    started_at: datetime
    deadline: datetime | None
    submitted_at: datetime | None
    questions: list[AttemptQuestion]


class ReviewItem(AttemptQuestion):
    """A question after submission, with its correct answer."""

    answer_index: int
    correct: bool


class TopicScore(BaseModel):
    """Correct answers for one topic (objective)."""

    objective_id: str
    topic: str
    correct: int
    total: int


class Results(BaseModel):
    """A submitted attempt's score, topic breakdown and question review."""

    id: UUID
    kind: Kind
    exam: str
    correct: int
    total: int
    pass_percent: int
    passed: bool
    submitted_at: datetime
    topics: list[TopicScore]
    review: list[ReviewItem]


class AttemptError(Exception):
    """The attempt cannot accept this request (for example, time is up)."""


def question_pool(
    conn: psycopg.Connection, exam: str, objective_id: str | None
) -> dict[str, list[str]]:
    """Reviewed question ids by objective, optionally for one objective."""
    rows = conn.execute(
        "SELECT objective_id, id FROM question"
        " WHERE exam = %s AND status = 'reviewed'"
        " AND (%s::text IS NULL OR objective_id = %s) ORDER BY id",
        (exam, objective_id, objective_id),
    ).fetchall()
    pool: dict[str, list[str]] = defaultdict(list)
    for objective, question_id in rows:
        pool[objective].append(question_id)
    return pool


def start(
    conn: psycopg.Connection,
    exam: str,
    kind: Kind,
    objective_id: str | None,
    now: datetime,
    rng: random.Random,
) -> UUID:
    """Choose the questions and record a new attempt."""
    rules = exams.RULES[exam]
    if kind == "mock" and not rules.mock_available:
        raise AttemptError(f"There is no {exam} mock exam yet.")
    pool = question_pool(conn, exam, objective_id)
    if kind == "mock":
        chosen = exams.assemble_mock(pool, rules.question_count, rng)
        time_limit = rules.time_limit_s
    else:
        all_ids = [q for ids in pool.values() for q in ids]
        chosen = exams.assemble_quiz(all_ids, exams.QUIZ_LENGTH, rng)
        time_limit = None
    if not chosen:
        raise AttemptError("No reviewed questions for this topic.")
    attempt_id = conn.execute(
        "INSERT INTO attempt (kind, exam, started_at, time_limit_s, total)"
        " VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (kind, exam, now, time_limit, len(chosen)),
    ).fetchone()[0]
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO attempt_item (attempt_id, position, question_id)"
            " VALUES (%s, %s, %s)",
            [(attempt_id, i, q) for i, q in enumerate(chosen)],
        )
    conn.commit()
    return attempt_id


ITEMS = """
    SELECT i.position, q.id AS question_id, q.number, q.objective_id, o.text AS topic,
           q.stem, q.choices, q.origin, i.chosen_index, q.answer_index
    FROM attempt_item i
    JOIN question q ON q.id = i.question_id
    JOIN objective o ON o.id = q.objective_id
    WHERE i.attempt_id = %s ORDER BY i.position
"""
ATTEMPT = """
    SELECT id, kind, exam, started_at, time_limit_s, submitted_at, correct, total,
           passed
    FROM attempt WHERE id = %s
"""


def attempt_row(conn: psycopg.Connection, attempt_id: UUID) -> NamedTuple | None:
    """The attempt's own columns, or None if there is none with this id."""
    cur = conn.cursor(row_factory=namedtuple_row)
    return cur.execute(ATTEMPT, (attempt_id,)).fetchone()


def item_rows(conn: psycopg.Connection, attempt_id: UUID) -> list[NamedTuple]:
    """The attempt's questions in order, with choices and answers."""
    cur = conn.cursor(row_factory=namedtuple_row)
    return cur.execute(ITEMS, (attempt_id,)).fetchall()


def load(conn: psycopg.Connection, attempt_id: UUID) -> Attempt | None:
    """The attempt with its questions, without answers."""
    row = attempt_row(conn, attempt_id)
    if row is None:
        return None
    fields = AttemptQuestion.model_fields
    return Attempt(
        id=row.id,
        kind=row.kind,
        exam=row.exam,
        started_at=row.started_at,
        deadline=exams.deadline(row.started_at, row.time_limit_s),
        submitted_at=row.submitted_at,
        questions=[
            AttemptQuestion(**{k: getattr(r, k) for k in fields})
            for r in item_rows(conn, attempt_id)
        ],
    )


def answer(
    conn: psycopg.Connection,
    attempt_id: UUID,
    position: int,
    chosen_index: int,
    now: datetime,
) -> None:
    """Record a choice, unless the attempt is submitted or out of time."""
    row = attempt_row(conn, attempt_id)
    if row.submitted_at is not None:
        raise AttemptError("This attempt has been submitted.")
    if not exams.accepts_answer(row.started_at, row.time_limit_s, now):
        raise AttemptError("Time is up: answers are no longer accepted.")
    updated = conn.execute(
        "UPDATE attempt_item i SET chosen_index = %s, answered_at = %s"
        " FROM question q WHERE q.id = i.question_id"
        " AND i.attempt_id = %s AND i.position = %s"
        " AND %s < jsonb_array_length(q.choices)",
        (chosen_index, now, attempt_id, position, chosen_index),
    ).rowcount
    if updated == 0:
        raise AttemptError("No such question or choice in this attempt.")
    conn.commit()


def submit(conn: psycopg.Connection, attempt_id: UUID, now: datetime) -> None:
    """Score the attempt and mark it submitted. Submitting twice is a no-op."""
    row = attempt_row(conn, attempt_id)
    if row.submitted_at is not None:
        return
    items = item_rows(conn, attempt_id)
    result = exams.score(
        [i.chosen_index for i in items],
        [i.answer_index for i in items],
        exams.RULES[row.exam].pass_percent,
    )
    conn.execute(
        "UPDATE attempt SET submitted_at = %s, correct = %s, passed = %s WHERE id = %s",
        (now, result.correct, result.passed, attempt_id),
    )
    conn.commit()


def results(conn: psycopg.Connection, attempt_id: UUID) -> Results | None:
    """The submitted attempt's results, or None if it is not submitted."""
    row = attempt_row(conn, attempt_id)
    if row is None or row.submitted_at is None:
        return None
    fields = ReviewItem.model_fields
    review = [
        ReviewItem(
            **{k: getattr(r, k) for k in fields if k != "correct"},
            correct=r.chosen_index == r.answer_index,
        )
        for r in item_rows(conn, attempt_id)
    ]
    return Results(
        id=row.id,
        kind=row.kind,
        exam=row.exam,
        correct=row.correct,
        total=row.total,
        pass_percent=exams.RULES[row.exam].pass_percent,
        passed=row.passed,
        submitted_at=row.submitted_at,
        topics=topic_scores(review),
        review=review,
    )


def topic_scores(review: list[ReviewItem]) -> list[TopicScore]:
    """Correct answers per topic, in objective order."""
    topics: dict[str, TopicScore] = {}
    for item in review:
        entry = topics.setdefault(
            item.objective_id,
            TopicScore(
                objective_id=item.objective_id, topic=item.topic, correct=0, total=0
            ),
        )
        entry.total += 1
        entry.correct += item.correct
    return [topics[key] for key in sorted(topics)]


class Topic(BaseModel):
    """A topic a quiz can be drawn from."""

    objective_id: str
    topic: str
    question_count: int


def topics(conn: psycopg.Connection, exam: str) -> list[Topic]:
    """Topics with reviewed questions for an exam, in objective order."""
    rows = conn.execute(
        "SELECT o.id, o.text, count(*) FROM question q"
        " JOIN objective o ON o.id = q.objective_id"
        " WHERE q.exam = %s AND q.status = 'reviewed'"
        " GROUP BY o.id, o.text ORDER BY o.id",
        (exam,),
    ).fetchall()
    return [Topic(objective_id=r[0], topic=r[1], question_count=r[2]) for r in rows]
