"""Student progress: the `objective_mastery` table and the mastery rule."""

from collections import Counter
from datetime import datetime
from typing import NamedTuple

import psycopg

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
