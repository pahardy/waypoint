import pytest
from pydantic import ValidationError

from waypoint_api.drafting import (
    Draft,
    GeneratedQuestion,
    check_prompt,
    cited_passages,
    draft,
    pick_objectives,
    shuffled,
)
from waypoint_api.retrieval import Passage

CAR = Passage(
    chunk_id="cars:CAR 602.14:0",
    document_id="cars",
    document_title="Canadian Aviation Regulations",
    edition="2026-10-01",
    jurisdiction="CA",
    section_ref="CAR 602.14",
    heading_path=["Part VI", "CAR 602.14"],
    page=None,
    subject="air-law",
    text="Over a built-up area, 1,000 feet above the highest obstacle.",
    score=1.0,
)
OBJECTIVE = {
    "id": "ppaer.air-law.061",
    "subject": "air-law",
    "topic": "CAR 602 Operating and Flight Rules (General)",
    "text": "Minimum Altitude and Distances",
    "ref": "CAR 602.14",
    "essential": True,
}
VALID = {
    "id": "ppaer.air-law.061.q1",
    "objective_id": "ppaer.air-law.061",
    "stem": "Over a built-up area, the minimum altitude is",
    "choices": ["500 ft", "1,000 ft", "1,500 ft", "2,000 ft"],
    "answer_index": 1,
    "explanation": "CAR 602.14: 1,000 feet above the highest obstacle.",
    "source_chunk_id": "cars:CAR 602.14:0",
}


# Validation


def test_a_valid_question_is_a_draft_by_default():
    question = GeneratedQuestion(**VALID)
    assert (question.status, question.exam, question.source) == (
        "draft",
        "PPAER",
        "cars",
    )


@pytest.mark.parametrize("field", ["objective_id", "source_chunk_id", "explanation"])
def test_a_question_without_a_required_field_is_rejected(field):
    with pytest.raises(ValidationError):
        GeneratedQuestion(**{k: v for k, v in VALID.items() if k != field})
    with pytest.raises(ValidationError, match="blank"):
        GeneratedQuestion(**{**VALID, field: " "})


@pytest.mark.parametrize(
    "change",
    [
        {"choices": ["a", "b", "c"]},
        {"choices": ["a", "b", "c", "c"]},
        {"choices": ["a", "b", "c", " "]},
        {"answer_index": 4},
    ],
)
def test_choices_must_be_four_distinct_with_an_answer_among_them(change):
    with pytest.raises(ValidationError):
        GeneratedQuestion(**{**VALID, **change})


# Drafting with a stub model


def stub_parse(source_label):
    def parse(model, effort, system, prompt, schema):
        assert "Minimum Altitude and Distances" in prompt
        return Draft(
            stem=VALID["stem"],
            choices=VALID["choices"],
            answer_index=1,
            explanation=VALID["explanation"],
            source_label=source_label,
        )

    return parse


CAR_PART_2 = CAR.model_copy(update={"chunk_id": "cars:CAR 602.14:1", "text": "..."})
OTHER = CAR.model_copy(
    update={"chunk_id": "cars:CAR 602.15:0", "section_ref": "CAR 602.15"}
)


def test_draft_cites_the_first_chunk_of_the_section():
    question = draft(OBJECTIVE, [CAR, CAR_PART_2], stub_parse("CAR 602.14"))
    assert question.id == "ppaer.air-law.061.q1"
    assert question.source_chunk_id == "cars:CAR 602.14:0"
    assert question.status == "draft"


def test_the_check_sees_every_chunk_of_the_cited_section():
    question = draft(OBJECTIVE, [CAR, CAR_PART_2, OTHER], stub_parse("CAR 602.14"))
    cited = cited_passages(question, [CAR, CAR_PART_2, OTHER])
    assert [p.chunk_id for p in cited] == ["cars:CAR 602.14:0", "cars:CAR 602.14:1"]


def test_shuffling_keeps_the_answer_and_is_repeatable():
    question = GeneratedQuestion(**VALID)
    once, twice = shuffled(question), shuffled(question)
    assert once.choices[once.answer_index] == "1,000 ft"
    assert sorted(once.choices) == sorted(question.choices)
    assert once == twice


def test_shuffling_spreads_answers_across_positions():
    positions = {
        shuffled(GeneratedQuestion(**{**VALID, "id": f"q{n}"})).answer_index
        for n in range(20)
    }
    assert positions == {0, 1, 2, 3}


def test_draft_citing_an_unknown_passage_is_rejected():
    with pytest.raises(ValueError, match="not given"):
        draft(OBJECTIVE, [CAR], stub_parse("CAR 999.99"))


def test_the_check_prompt_hides_the_answer():
    prompt = check_prompt(GeneratedQuestion(**VALID), [CAR])
    assert "1,000 feet above the highest obstacle" in prompt
    assert "CAR 602.14: 1,000 feet" not in prompt


# Picking objectives


def test_every_third_essential_objective_of_the_subject():
    objectives = [
        {"id": f"ppaer.air-law.{n:03d}", "subject": "air-law", "essential": n % 2 == 0}
        for n in range(20)
    ] + [{"id": "ppaer.navigation.001", "subject": "navigation", "essential": True}]
    picked = [o["id"] for o in pick_objectives(objectives, "air-law", 3)]
    assert picked == ["ppaer.air-law.000", "ppaer.air-law.006", "ppaer.air-law.012"]
