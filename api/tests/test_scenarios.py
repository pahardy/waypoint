import pytest
from pydantic import ValidationError

from waypoint_api.exercises import Scenario, load_scenario
from waypoint_api.grading import grade_prompt
from waypoint_api.scenarios import (
    ScenarioFinished,
    ScenarioState,
    overall_score,
    stage_exercise,
)

RUBRIC = [{"id": "c", "description": "d", "weight": 1, "key_points": ["k"]}]


def stage(stage_id, *facts):
    return {"id": stage_id, "facts": list(facts), "question": "q?", "rubric": RUBRIC}


SCENARIO = {
    "id": "weather",
    "exam": "PPAER",
    "objective_id": "ppaer.meteorology.094",
    "prompt": "A flight.",
    "sources": ["cars:CAR 602.115:0"],
    "stages": [stage("one", "METAR A"), stage("two", "Rain ahead", "Low cloud")],
}


def scenario(**change):
    return Scenario(**{**SCENARIO, **change})


# Validation


def test_the_repository_scenario_is_valid():
    loaded = load_scenario("deteriorating-weather")
    assert [s.id for s in loaded.stages] == ["before-departure", "en-route"]
    assert all("Synthetic" in fact for fact in loaded.stages[0].facts)


@pytest.mark.parametrize(
    "change",
    [
        {"stages": [stage("one", "f")]},
        {"stages": [stage("one", "f"), stage("one", "g")]},
        {"stages": [stage("one", "f"), {**stage("two", "g"), "question": ""}]},
        {"stages": [stage("one", "f"), {**stage("two", "g"), "rubric": []}]},
        {"stages": [stage("one", "f"), stage("two")]},
        {"sources": []},
    ],
)
def test_an_incomplete_scenario_is_rejected(change):
    with pytest.raises(ValidationError):
        scenario(**change)


# State machine


def test_stages_advance_in_order_and_facts_accumulate():
    state = ScenarioState(scenario())
    assert state.stage.id == "one"
    assert state.revealed() == ["METAR A"]
    state.advance()
    assert state.stage.id == "two"
    assert state.revealed() == ["METAR A", "Rain ahead", "Low cloud"]
    state.advance()
    assert state.finished


def test_a_finished_scenario_cannot_advance():
    state = ScenarioState(scenario(), index=2)
    with pytest.raises(ScenarioFinished):
        state.advance()
    with pytest.raises(ScenarioFinished):
        stage_exercise(state)


# Grading


def test_the_stage_two_grading_prompt_includes_stage_one_facts():
    state = ScenarioState(scenario(), index=1)
    prompt = grade_prompt(stage_exercise(state), [], "my answer")
    for fact in ("METAR A", "Rain ahead", "Low cloud"):
        assert fact in prompt
    assert stage_exercise(state).rubric == state.stage.rubric


def test_the_stage_one_grading_prompt_holds_only_stage_one_facts():
    prompt = grade_prompt(stage_exercise(ScenarioState(scenario())), [], "a")
    assert "METAR A" in prompt
    assert "Rain ahead" not in prompt


@pytest.mark.parametrize(
    ("scores", "expected"), [([100, 100], 100), ([0, 0], 0), ([100, 25], 63)]
)
def test_the_overall_score_is_the_mean_of_the_stage_scores(scores, expected):
    assert overall_score(scores) == expected
