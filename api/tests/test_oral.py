import pytest
from pydantic import ValidationError

from waypoint_api.exercises import (
    Criterion,
    Exercise,
    load_exercise,
    score,
    source_passages,
)
from waypoint_api.grading import CriterionMark, Grading, GradingError, grade

ANSWER = "The altimeter freezes. The VSI reads zero. I am not sure about airspeed."
RUBRIC = [
    {"id": "altimeter", "description": "d", "weight": 1, "key_points": ["k"]},
    {"id": "vsi", "description": "d", "weight": 1, "key_points": ["k"]},
    {"id": "airspeed", "description": "d", "weight": 2, "key_points": ["k"]},
]
EXERCISE = {
    "id": "static-port",
    "exam": "PPAER",
    "objective_id": "ppaer.aeronautics.100",
    "prompt": "Explain a blocked static port.",
    "sources": ["faa-phak:PHAK p.213:0"],
    "rubric": RUBRIC,
}


def exercise(**change):
    return Exercise(**{**EXERCISE, **change})


# Exercise files


def test_the_repository_exercise_is_valid():
    loaded = load_exercise("static-port")
    assert [c.id for c in loaded.rubric] == ["altimeter", "vsi", "airspeed"]
    assert loaded.sources


@pytest.mark.parametrize(
    "change",
    [
        {"prompt": ""},
        {"sources": []},
        {"rubric": []},
        {"rubric": [{**RUBRIC[0], "weight": 0}]},
        {"rubric": [{**RUBRIC[0], "key_points": []}]},
    ],
)
def test_an_incomplete_exercise_is_rejected(change):
    with pytest.raises(ValidationError):
        exercise(**change)


class FakeConnection:
    """Returns no chunks, as if the sources were not in the knowledge base."""

    def execute(self, query, params):
        return self

    def fetchall(self):
        return []


def test_sources_must_be_in_the_knowledge_base():
    with pytest.raises(ValueError, match="not in the knowledge base"):
        source_passages(FakeConnection(), exercise())


# Score


def rubric():
    return [Criterion(**c) for c in RUBRIC]


@pytest.mark.parametrize(
    ("marks", "expected"),
    [
        (("met", "met", "met"), 100),
        (("not_met", "not_met", "not_met"), 0),
        (("met", "met", "not_met"), 50),
        (("not_met", "not_met", "met"), 50),
        (("partly_met", "met", "partly_met"), 63),
    ],
)
def test_the_score_is_weighted(marks, expected):
    assert (
        score(rubric(), dict(zip(["altimeter", "vsi", "airspeed"], marks))) == expected
    )


# Grading with a stub model


def mark(criterion_id, value, evidence):
    return CriterionMark(
        criterion_id=criterion_id, mark=value, evidence=evidence, reason="."
    )


GOOD = Grading(
    marks=[
        mark("vsi", "met", "the VSI reads zero"),
        mark("airspeed", "not_met", ""),
        mark("altimeter", "met", "The altimeter freezes."),
    ]
)
MISSING = Grading(marks=GOOD.marks[:2])
MISQUOTED = Grading(
    marks=[*GOOD.marks[:2], mark("altimeter", "met", "the altimeter sticks")]
)
UNQUOTED = Grading(marks=[*GOOD.marks[:2], mark("altimeter", "met", "")])


def stub(*responses):
    calls = []

    def parse(model, effort, system, prompt, schema):
        assert ANSWER in prompt
        calls.append(prompt)
        return responses[len(calls) - 1]

    return parse, calls


def test_a_valid_grading_gives_marks_in_rubric_order_and_the_score():
    parse, calls = stub(GOOD)
    graded = grade(exercise(), [], ANSWER, parse)
    assert [m.criterion_id for m in graded.marks] == ["altimeter", "vsi", "airspeed"]
    assert graded.score == 50
    assert len(calls) == 1


@pytest.mark.parametrize("bad", [MISSING, MISQUOTED, UNQUOTED])
def test_a_bad_grading_is_retried_once(bad):
    parse, calls = stub(bad, GOOD)
    assert grade(exercise(), [], ANSWER, parse).score == 50
    assert len(calls) == 2


def test_two_bad_gradings_fail():
    parse, calls = stub(MISQUOTED, MISSING)
    with pytest.raises(GradingError, match="do not match rubric"):
        grade(exercise(), [], ANSWER, parse)
    assert len(calls) == 2
