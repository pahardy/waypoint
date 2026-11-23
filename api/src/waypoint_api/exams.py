"""Examination rules, question selection and scoring. Deterministic code only."""

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

Outcome = Literal["pass", "partial", "fail"]


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
    mock_mix: Literal["by_section", "by_subject"]
    subject_pass: bool


PSTAR = ExamRules(
    exam="PSTAR",
    question_count=50,
    time_limit_s=90 * 60,
    pass_percent=90,
    source="TP 11919 (7th ed.), introduction",
    unverified=("time_limit_s",),
    mock_available=True,
    mock_mix="by_section",
    subject_pass=False,
)
PPAER = ExamRules(
    exam="PPAER",
    question_count=100,
    time_limit_s=3 * 60 * 60,
    pass_percent=60,
    source="TP 12880 (6th ed.), p. 4",
    unverified=(),
    mock_available=True,
    mock_mix="by_subject",
    subject_pass=True,
)
RULES = {"PSTAR": PSTAR, "PPAER": PPAER}
QUIZ_LENGTH = 10
# The supplementary exam for each subject below 60% on a PPAER partial pass
# (TP 12880, p. 5).
SUPPLEMENTARY = {
    "air-law": "PALAW",
    "navigation": "PANAV",
    "meteorology": "PAMET",
    "aeronautics": "PAGEN",
}


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


def equal_counts(keys: list[str], total: int) -> dict[str, int]:
    """The same number of questions from each group (PPAER: 25 per subject).
    Waypoint's rule; Transport Canada does not publish the split."""
    return {key: total // len(keys) for key in keys}


def mock_counts(rules: ExamRules, sizes: dict[str, int]) -> dict[str, int]:
    """How many mock-exam questions to draw from each group of the pool."""
    if rules.mock_mix == "by_subject":
        return equal_counts(sorted(sizes), rules.question_count)
    return section_counts(sizes, rules.question_count)


def assemble_mock(
    pool: dict[str, list[str]], counts: dict[str, int], rng: random.Random
) -> list[str]:
    """Question ids for a mock exam: `counts[key]` drawn from each group."""
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


def meets(correct: int, total: int, pass_percent: int) -> bool:
    """At or above the pass mark."""
    return correct * 100 >= pass_percent * total


def outcome(
    subjects: dict[str, tuple[int, int]], pass_percent: int, per_subject: bool
) -> Outcome:
    """Pass, partial pass or fail from (correct, total) per subject.

    Under the pass mark overall is a fail. With `per_subject` (the PPAER mock
    exam, TP 12880), passing overall with any subject under the mark is a
    partial pass.
    """
    correct = sum(c for c, _ in subjects.values())
    total = sum(t for _, t in subjects.values())
    if not meets(correct, total, pass_percent):
        return "fail"
    if per_subject and not all(meets(c, t, pass_percent) for c, t in subjects.values()):
        return "partial"
    return "pass"
