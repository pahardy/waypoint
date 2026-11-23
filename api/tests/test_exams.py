import random
from datetime import UTC, datetime, timedelta

from waypoint_api.exams import (
    PSTAR,
    accepts_answer,
    assemble_mock,
    assemble_quiz,
    score,
    section_counts,
)

START = datetime(2026, 11, 23, 12, 0, tzinfo=UTC)


# Scoring


def test_all_correct_passes():
    assert score([0, 1, 2], [0, 1, 2], 90).passed


def test_none_correct_fails():
    result = score([1, 2, 3], [0, 1, 2], 90)
    assert (result.correct, result.passed) == (0, False)


def test_exactly_the_pass_mark_passes():
    answers = [0] * 50
    chosen = [0] * 45 + [1] * 5
    assert score(chosen, answers, 90).passed


def test_just_below_the_pass_mark_fails():
    answers = [0] * 50
    chosen = [0] * 44 + [1] * 6
    assert not score(chosen, answers, 90).passed


def test_an_empty_attempt_scores_zero():
    result = score([None] * 50, [0] * 50, 90)
    assert (result.correct, result.total, result.passed) == (0, 50, False)


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
    chosen = assemble_mock(pool, PSTAR.question_count, random.Random(1))
    assert len(chosen) == len(set(chosen)) == 50
    expected = section_counts({k: len(v) for k, v in pool.items()}, 50)
    for key, count in expected.items():
        assert sum(q.startswith(f"{key}-") for q in chosen) == count


def test_quiz_takes_ten_or_the_whole_pool():
    pool = [str(i) for i in range(29)]
    assert len(set(assemble_quiz(pool, 10, random.Random(1)))) == 10
    assert sorted(assemble_quiz(pool[:5], 10, random.Random(1))) == pool[:5]
