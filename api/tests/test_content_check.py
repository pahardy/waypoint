import pytest

from waypoint_api.content_check import (
    CheckError,
    ContentVerdict,
    PointVerdict,
    check,
    check_prompt,
    key_points,
    problems,
)
from waypoint_api.exercises import Exercise, Scenario
from waypoint_api.sessions import exercise_ids, load_any

RUBRIC = [
    {"id": "a", "description": "d", "weight": 1, "key_points": ["One.", "Two."]},
    {"id": "b", "description": "d", "weight": 1, "key_points": ["Three."]},
]
ORAL = Exercise(
    id="oral",
    exam="PPAER",
    objective_id="o",
    prompt="Explain.",
    sources=["s"],
    rubric=RUBRIC,
)
SCENARIO = Scenario(
    id="scenario",
    exam="PPAER",
    objective_id="o",
    prompt="A flight.",
    sources=["s"],
    stages=[
        {"id": "one", "facts": ["Fact one."], "question": "Q1?", "rubric": RUBRIC[:1]},
        {"id": "two", "facts": ["Fact two."], "question": "Q2?", "rubric": RUBRIC[1:]},
    ],
)


def test_every_exercise_file_loads():
    ids = exercise_ids()
    assert "static-port" in ids
    for exercise_id in ids:
        loaded = load_any(exercise_id)
        assert loaded.id == exercise_id
        assert loaded.exam in ("PSTAR", "PPAER", "FLIGHT_TEST")


def test_key_points_have_ids_per_criterion_and_stage():
    assert key_points(ORAL) == {"a/1": "One.", "a/2": "Two.", "b/1": "Three."}
    assert list(key_points(SCENARIO)) == ["one/a/1", "one/a/2", "two/b/1"]


def test_the_prompt_holds_the_scenario_facts_and_every_point():
    prompt = check_prompt(SCENARIO, [])
    for text in ("Fact one.", "Fact two.", "Q2?", '<point id="two/b/1">Three.</point>'):
        assert text in prompt


def verdict(*supported, faa=False):
    ids = list(key_points(ORAL))
    return ContentVerdict(
        points=[
            PointVerdict(point_id=i, supported=s, reason="r")
            for i, s in zip(ids, supported)
        ],
        faa_as_canadian=faa,
        faa_reason="FAA rule." if faa else "",
    )


def stub(response):
    return lambda model, effort, system, prompt, schema: response


def test_all_supported_has_no_problems():
    assert problems(ORAL, check(ORAL, [], stub(verdict(True, True, True)))) == []


def test_an_unsupported_point_and_faa_as_canadian_are_reported():
    found = problems(ORAL, check(ORAL, [], stub(verdict(True, False, True, faa=True))))
    assert found == ["unsupported a/2: Two. (r)", "FAA as Canadian: FAA rule."]


def test_a_verdict_missing_a_point_is_rejected():
    with pytest.raises(CheckError):
        check(ORAL, [], stub(verdict(True, True)))
