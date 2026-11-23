"""Examination rules, question selection and scoring. Deterministic code only."""

import random
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class ExamRules:
    """The published facts for one examination, and which are unverified."""

    exam: str
    question_count: int
    time_limit_s: int
    pass_percent: int
    source: str
    unverified: tuple[str, ...]
    mock_available: bool


PSTAR = ExamRules(
    exam="PSTAR",
    question_count=50,
    time_limit_s=90 * 60,
    pass_percent=90,
    source="TP 11919 (7th ed.), introduction",
    unverified=("time_limit_s",),
    mock_available=True,
)
# The 60% pass mark also applies to each subject; that matters for the mock
# exam (plan 04 step 4), not for single-subject quizzes.
PPAER = ExamRules(
    exam="PPAER",
    question_count=100,
    time_limit_s=3 * 60 * 60,
    pass_percent=60,
    source="TP 12880 (6th ed.), p. 4",
    unverified=(),
    mock_available=False,
)
RULES = {"PSTAR": PSTAR, "PPAER": PPAER}
QUIZ_LENGTH = 10


@dataclass(frozen=True)
class Score:
    """The result of a submitted attempt."""

    correct: int
    total: int
    passed: bool


def section_counts(sizes: dict[str, int], total: int) -> dict[str, int]:
    """Split `total` across sections in proportion to their sizes.

    Largest remainder method: each section gets the whole part of its share,
    then the leftover questions go to the largest fractional parts. This is
    Waypoint's rule; Transport Canada does not publish how it selects.
    """
    pool = sum(sizes.values())
    shares = {key: size * total / pool for key, size in sizes.items()}
    counts = {key: int(share) for key, share in shares.items()}
    leftover = total - sum(counts.values())
    by_remainder = sorted(shares, key=lambda k: (counts[k] - shares[k], k))
    for key in by_remainder[:leftover]:
        counts[key] += 1
    return counts


def assemble_mock(
    pool: dict[str, list[str]], count: int, rng: random.Random
) -> list[str]:
    """Question ids for a mock exam, drawn from each section in proportion."""
    counts = section_counts({k: len(v) for k, v in pool.items()}, count)
    chosen = [q for key, ids in pool.items() for q in rng.sample(ids, counts[key])]
    rng.shuffle(chosen)
    return chosen


def assemble_quiz(pool: list[str], count: int, rng: random.Random) -> list[str]:
    """Question ids for a topic quiz: up to `count`, drawn at random."""
    return rng.sample(pool, min(count, len(pool)))


def deadline(started_at: datetime, time_limit_s: int | None) -> datetime | None:
    """When answers stop being accepted, or None for an untimed attempt."""
    if time_limit_s is None:
        return None
    return started_at + timedelta(seconds=time_limit_s)


def accepts_answer(
    started_at: datetime, time_limit_s: int | None, now: datetime
) -> bool:
    """An answer counts only if it arrives by the deadline."""
    end = deadline(started_at, time_limit_s)
    return end is None or now <= end


def score(chosen: list[int | None], answers: list[int], pass_percent: int) -> Score:
    """Count correct answers; unanswered questions are wrong."""
    correct = sum(c == a for c, a in zip(chosen, answers, strict=True))
    total = len(answers)
    return Score(correct, total, correct * 100 >= pass_percent * total)
