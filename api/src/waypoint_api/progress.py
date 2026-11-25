"""Student progress: the `objective_mastery` table and the mastery rule."""

from collections import Counter
from datetime import datetime
from typing import NamedTuple

import psycopg
from pydantic import BaseModel

from waypoint_api import exams

UPSERT = """
    INSERT INTO objective_mastery (objective_id, correct, seen, last_seen_at)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (objective_id) DO UPDATE SET
        correct = objective_mastery.correct + EXCLUDED.correct,
        seen = objective_mastery.seen + EXCLUDED.seen,
        last_seen_at = EXCLUDED.last_seen_at
"""


def mastery(correct: int, seen: int) -> float | None:
    """The share of an objective's questions answered correctly, or None if
    none has been seen."""
    return correct / seen if seen else None


def record(conn: psycopg.Connection, items: list[NamedTuple], now: datetime) -> None:
    """Add a submitted attempt's items to each objective's counts. An
    unanswered item counts as seen and wrong. Does not commit."""
    seen = Counter(i.objective_id for i in items)
    correct = Counter(i.objective_id for i in items if i.chosen_index == i.answer_index)
    conn.cursor().executemany(
        UPSERT, [(o, correct[o], n, now) for o, n in sorted(seen.items())]
    )


MIN_SEEN = 5

OBJECTIVES = """
    SELECT o.id, o.subject, o.text, coalesce(m.correct, 0), coalesce(m.seen, 0)
    FROM objective o LEFT JOIN objective_mastery m ON m.objective_id = o.id
    WHERE o.exam = %s ORDER BY o.id
"""


class ObjectiveCounts(NamedTuple):
    """One objective's answers so far."""

    objective_id: str
    subject: str
    topic: str
    correct: int
    seen: int


class SubjectProgress(BaseModel):
    """Answers so far across one subject's objectives."""

    subject: str
    correct: int
    seen: int
    percent: int | None


class WeakObjective(BaseModel):
    """An objective answered often enough, and below the pass mark."""

    objective_id: str
    topic: str
    correct: int
    seen: int
    percent: int
    reason: str


class Progress(BaseModel):
    """An exam's progress per subject and its weak objectives."""

    exam: str
    pass_percent: int
    subjects: list[SubjectProgress]
    weak: list[WeakObjective]


def percent(correct: int, seen: int) -> int | None:
    """Mastery as a whole percentage, rounded down so it never reaches the
    pass mark when the share is below it."""
    return correct * 100 // seen if seen else None


def subjects(objectives: list[ObjectiveCounts]) -> list[SubjectProgress]:
    """Totals per subject, in alphabetical order."""
    totals: dict[str, list[int]] = {}
    for o in objectives:
        total = totals.setdefault(o.subject, [0, 0])
        total[0] += o.correct
        total[1] += o.seen
    return [
        SubjectProgress(subject=s, correct=c, seen=n, percent=percent(c, n))
        for s, (c, n) in sorted(totals.items())
    ]


def weak(objectives: list[ObjectiveCounts], pass_percent: int) -> list[WeakObjective]:
    """Objectives seen at least MIN_SEEN times with mastery below the pass
    mark, lowest first; ties by objective id."""
    found = [
        o
        for o in objectives
        if o.seen >= MIN_SEEN and not exams.meets(o.correct, o.seen, pass_percent)
    ]
    found.sort(key=lambda o: (o.correct / o.seen, o.objective_id))
    return [
        WeakObjective(
            objective_id=o.objective_id,
            topic=o.topic,
            correct=o.correct,
            seen=o.seen,
            percent=percent(o.correct, o.seen),
            reason=f"{o.correct} of {o.seen} correct ({percent(o.correct, o.seen)}%),"
            f" below the {pass_percent}% pass mark",
        )
        for o in found
    ]


def load(conn: psycopg.Connection, exam: str) -> Progress:
    """The exam's progress from `objective_mastery`."""
    objectives = [ObjectiveCounts(*r) for r in conn.execute(OBJECTIVES, (exam,))]
    pass_percent = exams.RULES[exam].pass_percent
    return Progress(
        exam=exam,
        pass_percent=pass_percent,
        subjects=subjects(objectives),
        weak=weak(objectives, pass_percent),
    )
