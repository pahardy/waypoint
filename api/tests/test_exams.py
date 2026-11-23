import random
from datetime import UTC, datetime, timedelta

from waypoint_api.exams import (
    PPAER,
    PSTAR,
    accepts_answer,
    assemble_mock,
    assemble_quiz,
    mock_counts,
    outcome,
    section_counts,
)

START = datetime(2026, 11, 23, 12, 0, tzinfo=UTC)


# Scoring (PSTAR: one subject, 90% pass mark)


def pstar(correct, total=50):
    return outcome({"regulations": (correct, total)}, 90, per_subject=False)


def test_all_correct_passes():
    assert pstar(50) == "pass"


def test_none_correct_fails():
    assert pstar(0) == "fail"


def test_exactly_the_pass_mark_passes():
    assert pstar(45) == "pass"


def test_just_below_the_pass_mark_fails():
    assert pstar(44) == "fail"


# Timing


def test_answer_one_second_before_the_limit_counts():
    now = START + timedelta(seconds=PSTAR.time_limit_s - 1)
    assert accepts_answer(START, PSTAR.time_limit_s, now)


def test_answer_one_second_after_the_limit_does_not_count():
    now = START + timedelta(seconds=PSTAR.time_limit_s + 1)
    assert not accepts_answer(START, PSTAR.time_limit_s, now)


def test_untimed_attempt_always_accepts():
    assert accepts_answer(START, None, START + timedelta(days=1))


# Selection


def test_section_counts_are_proportional_and_sum_to_total():
    counts = section_counts({"a": 29, "b": 10, "c": 5}, 10)
    assert sum(counts.values()) == 10
    assert counts == {"a": 7, "b": 2, "c": 1}


def test_mock_has_the_right_count_and_mix_without_duplicates():
    pool = {
        f"s{n}": [f"s{n}-{i}" for i in range(size)]
        for n, size in enumerate([10, 8, 29, 8, 11, 23, 14, 13, 11, 6, 14, 21, 12, 5])
    }
    expected = mock_counts(PSTAR, {k: len(v) for k, v in pool.items()})
    chosen = assemble_mock(pool, expected, random.Random(1))
    assert len(chosen) == len(set(chosen)) == 50
    assert expected == section_counts({k: len(v) for k, v in pool.items()}, 50)
    for key, count in expected.items():
        assert sum(q.startswith(f"{key}-") for q in chosen) == count


def test_quiz_takes_ten_or_the_whole_pool():
    pool = [str(i) for i in range(29)]
    assert len(set(assemble_quiz(pool, 10, random.Random(1)))) == 10
    assert sorted(assemble_quiz(pool[:5], 10, random.Random(1))) == pool[:5]


def test_ppaer_mock_takes_25_from_each_subject():
    pool = {
        subject: [f"{subject}-{i}" for i in range(size)]
        for subject, size in [
            ("air-law", 25),
            ("navigation", 30),
            ("meteorology", 25),
            ("aeronautics", 40),
        ]
    }
    counts = mock_counts(PPAER, {k: len(v) for k, v in pool.items()})
    assert counts == dict.fromkeys(pool, 25)
    chosen = assemble_mock(pool, counts, random.Random(1))
    assert len(chosen) == len(set(chosen)) == 100
    for subject in pool:
        assert sum(q.startswith(f"{subject}-") for q in chosen) == 25


# PPAER outcome (TP 12880)


def subjects(*correct):
    names = ["air-law", "navigation", "meteorology", "aeronautics"]
    return {name: (c, 25) for name, c in zip(names, correct)}


def test_ppaer_pass_with_every_subject_at_60_percent():
    assert outcome(subjects(15, 15, 15, 15), 60, per_subject=True) == "pass"


def test_ppaer_partial_pass_when_one_subject_is_under_60_percent():
    assert outcome(subjects(25, 25, 14, 25), 60, per_subject=True) == "partial"


def test_ppaer_fail_when_under_60_percent_overall():
    assert outcome(subjects(15, 15, 15, 14), 60, per_subject=True) == "fail"


def test_ppaer_fail_overrides_a_subject_shortfall():
    assert outcome(subjects(25, 20, 0, 14), 60, per_subject=True) == "fail"


def test_without_per_subject_marks_a_weak_subject_still_passes():
    assert outcome(subjects(25, 25, 0, 25), 60, per_subject=False) == "pass"
