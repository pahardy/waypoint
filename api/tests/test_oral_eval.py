import pytest
from pydantic import ValidationError

from waypoint_api.exercises import load_exercise
from waypoint_api.oral_eval import (
    EvalSet,
    agreement,
    check_eval_set,
    confusion,
    consistency,
    load_eval_set,
    report,
    spread,
)

EXPECTED = {"a": {"altimeter": "met", "vsi": "not_met"}}


def row(rep, altimeter, vsi, score=0, answer_id="a"):
    def given(mark):
        return {"mark": mark, "evidence": "", "reason": "."}

    return {
        "answer_id": answer_id,
        "rep": rep,
        "marks": {"altimeter": given(altimeter), "vsi": given(vsi)},
        "score": score,
    }


# Metrics


def test_all_reps_agree():
    rows = [row(r, "met", "not_met", 50) for r in range(3)]
    assert consistency(rows) == (2, 2)
    assert agreement(rows, EXPECTED) == (6, 6)
    assert spread(rows) == {"a": 0}


def test_one_rep_differs():
    rows = [row(0, "met", "not_met", 50), row(1, "met", "not_met", 50)]
    rows.append(row(2, "partly_met", "not_met", 25))
    assert consistency(rows) == (1, 2)
    assert agreement(rows, EXPECTED) == (5, 6)
    assert confusion(rows, EXPECTED)["met", "partly_met"] == 1
    assert spread(rows) == {"a": 25}


def test_a_criterion_marked_differently_each_time():
    rows = [row(0, "met", "not_met"), row(1, "partly_met", "not_met")]
    rows.append(row(2, "not_met", "not_met"))
    assert consistency(rows) == (1, 2)
    table = confusion(rows, EXPECTED)
    assert [table["met", m] for m in ("met", "partly_met", "not_met")] == [1, 1, 1]
    assert table.total() == 6


def test_consistent_but_wrong_marks_count_against_agreement_only():
    rows = [row(r, "not_met", "not_met") for r in range(3)]
    assert consistency(rows) == (2, 2)
    assert agreement(rows, EXPECTED) == (3, 6)


# Eval set


def test_the_repository_eval_set_is_valid():
    eval_set, exercise = load_eval_set()
    assert len(eval_set.answers) == 10
    assert exercise.id == eval_set.exercise


def eval_set(*answers):
    return EvalSet(exercise="static-port", answers=list(answers))


FULL = {"altimeter": "met", "vsi": "met", "airspeed": "met"}


@pytest.mark.parametrize(
    "answers",
    [
        [{"id": "a", "answer": "x", "expected": FULL}] * 2,
        [{"id": "a", "answer": "x", "expected": {"altimeter": "met"}}],
        [{"id": "a", "answer": "x", "expected": {**FULL, "extra": "met"}}],
    ],
)
def test_ids_must_be_unique_and_marks_must_match_the_rubric(answers):
    with pytest.raises(ValueError):
        check_eval_set(eval_set(*answers), load_exercise("static-port"))


@pytest.mark.parametrize(
    "answer",
    [
        {"id": "a", "answer": "", "expected": FULL},
        {"id": "a", "answer": "x", "expected": {**FULL, "vsi": "half"}},
    ],
)
def test_an_empty_answer_or_unknown_mark_is_rejected(answer):
    with pytest.raises(ValidationError):
        eval_set(answer)


def test_the_report_lists_inconsistent_marks():
    set_ = EvalSet(
        exercise="static-port",
        answers=[{"id": "a", "answer": "x", "expected": EXPECTED["a"]}],
    )
    rows = [row(0, "met", "not_met"), row(1, "partly_met", "not_met")]
    for r in rows:
        r |= {"model": "m", "effort": "low", "calls": 1, "cost_usd": 0.01}
    text = report(rows, set_, errors=0)
    assert "1/2 (50%)" in text
    assert "**a / altimeter**: expected met" in text
    assert "a / vsi" not in text
