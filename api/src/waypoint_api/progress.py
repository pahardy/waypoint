"""Student progress: the `objective_mastery` table and the mastery rule."""

from collections import Counter
from datetime import datetime
from typing import Literal, NamedTuple

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


Confidence = Literal["low", "medium", "high"]

MIN_SEEN = 5
MAX_RECOMMENDATIONS = 5

OBJECTIVES = """
    SELECT o.id, o.subject, o.text, coalesce(m.correct, 0), coalesce(m.seen, 0),
           m.self_confidence
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
    confidence: Confidence | None = None


class SubjectProgress(BaseModel):
    """Answers so far across one subject's objectives."""

    subject: str
    correct: int
    seen: int
    percent: int | None


class WeakObjective(BaseModel):
    """An objective below the pass mark after enough answers, or rated low
    in confidence, and why."""

    objective_id: str
    topic: str
    correct: int
    seen: int
    percent: int | None
    reason: str


class Progress(BaseModel):
    """An exam's progress per subject, its weak objectives and the ones
    recommended for study next."""

    exam: str
    pass_percent: int
    subjects: list[SubjectProgress]
    weak: list[WeakObjective]
    recommendations: list[WeakObjective]


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


def below_mark(o: ObjectiveCounts, pass_percent: int) -> bool:
    """Seen at least MIN_SEEN times and below the pass mark."""
    return o.seen >= MIN_SEEN and not exams.meets(o.correct, o.seen, pass_percent)


def reason(o: ObjectiveCounts, pass_percent: int) -> str:
    """The numbers behind a weak objective, then a low rating if given."""
    low = "rated low confidence" if o.confidence == "low" else None
    if o.seen == 0:
        return "Rated low confidence"
    numbers = f"{o.correct} of {o.seen} correct ({percent(o.correct, o.seen)}%)"
    if below_mark(o, pass_percent):
        numbers += f", below the {pass_percent}% pass mark"
    return f"{numbers}; {low}" if low else numbers


def weak(objectives: list[ObjectiveCounts], pass_percent: int) -> list[WeakObjective]:
    """Objectives below the pass mark after MIN_SEEN answers, or rated low
    in confidence; lowest mastery first, ties by objective id."""
    found = [
        o for o in objectives if below_mark(o, pass_percent) or o.confidence == "low"
    ]
    found.sort(key=lambda o: (mastery(o.correct, o.seen) or 0.0, o.objective_id))
    return [
        WeakObjective(
            objective_id=o.objective_id,
            topic=o.topic,
            correct=o.correct,
            seen=o.seen,
            percent=percent(o.correct, o.seen),
            reason=reason(o, pass_percent),
        )
        for o in found
    ]


def recommend(weak_objectives: list[WeakObjective]) -> list[WeakObjective]:
    """The weakest objectives to study next: the start of the weak list."""
    return weak_objectives[:MAX_RECOMMENDATIONS]


def rate(
    conn: psycopg.Connection, objective_id: str, confidence: Confidence | None
) -> bool:
    """Set or clear an answered objective's confidence rating. False if the
    objective has not been answered."""
    updated = conn.execute(
        "UPDATE objective_mastery SET self_confidence = %s WHERE objective_id = %s",
        (confidence, objective_id),
    ).rowcount
    conn.commit()
    return updated == 1


def load(conn: psycopg.Connection, exam: str) -> Progress:
    """The exam's progress from `objective_mastery`."""
    objectives = [ObjectiveCounts(*r) for r in conn.execute(OBJECTIVES, (exam,))]
    pass_percent = exams.RULES[exam].pass_percent
    found = weak(objectives, pass_percent)
    return Progress(
        exam=exam,
        pass_percent=pass_percent,
        subjects=subjects(objectives),
        weak=found,
        recommendations=recommend(found),
    )
