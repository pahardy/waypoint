import pytest

from waypoint_api.instructor import NOT_FOUND, Answer
from waypoint_api.instructor_eval import METRICS, cost, grade, load_cases
from waypoint_api.judge import FactCheck, Judgement, Verdict, judge_prompt
from waypoint_api.retrieval import Passage

CAR = Passage(
    chunk_id="cars:CAR 602.03:0",
    document_id="cars",
    document_title="CARs",
    edition="2026",
    jurisdiction="CA",
    section_ref="CAR 602.03",
    heading_path=["CAR 602.03"],
    page=None,
    subject="air-law",
    text="Not within 12 hours.",
    score=0.6,
)
ANSWER_CASE = {
    "id": "alcohol",
    "kind": "answer",
    "level": "PPAER",
    "question": "How long after drinking can I fly?",
    "expected_sections": ["cars:CAR 602.03"],
    "key_facts": ["12 hours.", "AIM advises 24 hours."],
}
DECLINE_CASE = {
    "id": "solo",
    "kind": "decline",
    "level": "PSTAR",
    "question": "Should I fly solo today?",
    "expectation": "Does not decide.",
}


def verdict(stated=(True, True), unsupported=(), faa=False, behaviour=True):
    return Judgement(
        Verdict(
            facts=[
                FactCheck(fact=f"f{i}", stated=s, reason="r")
                for i, s in enumerate(stated)
            ],
            unsupported_claims=list(unsupported),
            faa_as_canadian=faa,
            faa_reason="",
            behaviour_ok=behaviour,
            behaviour_reason="ok",
        ),
        "claude-opus-5-5",
        100,
        50,
    )


def answer(unknown=(), citations=(CAR,)):
    return Answer("Twelve hours [CAR 602.03].", [CAR], list(citations), list(unknown))


def test_every_metric_is_reported_for_every_case_kind():
    ids = [m["id"] for m in METRICS]
    for case in (ANSWER_CASE, DECLINE_CASE):
        scores, _ = grade(case, answer(), verdict())
        assert list(scores) == ids
    not_found = {"kind": "not_found"}
    scores, _ = grade(not_found, Answer(NOT_FOUND, [], found=False), None)
    assert list(scores) == ids


def test_an_answer_passes_with_every_fact_grounded_and_valid_citations():
    scores, _ = grade(ANSWER_CASE, answer(), verdict())
    assert scores["pass"] == 1.0
    assert scores["key_facts"] == 1.0
    assert scores["cites_expected"] == 1.0


@pytest.mark.parametrize(
    "graded",
    [
        verdict(stated=(True, False)),
        verdict(unsupported=["Says 8 hours."]),
        verdict(faa=True),
    ],
)
def test_a_missing_fact_or_unsupported_claim_fails_the_answer(graded):
    assert grade(ANSWER_CASE, answer(), graded)[0]["pass"] == 0.0


def test_an_invalid_citation_fails_the_answer():
    scores, reasons = grade(ANSWER_CASE, answer(unknown=["CAR 999.9"]), verdict())
    assert (scores["pass"], scores["citations_valid"]) == (0.0, 0.0)
    assert "CAR 999.9" in reasons["citations_valid"]


def test_key_facts_is_the_share_stated():
    assert (
        grade(ANSWER_CASE, answer(), verdict(stated=(True, False)))[0]["key_facts"]
        == 0.5
    )


def test_a_verdict_with_fewer_facts_than_the_case_cannot_pass():
    scores, _ = grade(ANSWER_CASE, answer(), verdict(stated=(True,)))
    assert (scores["key_facts"], scores["pass"]) == (0.5, 0.0)


def test_a_decline_passes_on_behaviour_without_key_facts():
    scores, _ = grade(DECLINE_CASE, answer(), verdict(stated=()))
    assert scores["pass"] == 1.0
    assert scores["key_facts"] is None and scores["cites_expected"] is None
    assert (
        grade(DECLINE_CASE, answer(), verdict(stated=(), behaviour=False))[0]["pass"]
        == 0.0
    )


def test_not_found_passes_only_on_the_no_model_path():
    case = {"kind": "not_found"}
    assert grade(case, Answer(NOT_FOUND, [], found=False), None)[0]["pass"] == 1.0
    assert grade(case, Answer("Lasagna needs...", [CAR]), None)[0]["pass"] == 0.0


def test_the_judge_sees_question_passages_criteria_and_answer_in_order():
    text = judge_prompt(ANSWER_CASE, [CAR], "Twelve hours.")
    positions = [
        text.index(tag)
        for tag in ("<question>", "<passages>", "<criteria>", "<key_facts>", "<answer>")
    ]
    assert positions == sorted(positions)
    assert 'label="CAR 602.03"' in text and "- AIM advises 24 hours." in text


def test_cost_prices_cache_reads_and_writes():
    usage = {
        "input_tokens": 1_000_000,
        "output_tokens": 100_000,
        "cache_read_input_tokens": 1_000_000,
        "cache_creation_input_tokens": 1_000_000,
    }
    assert cost("claude-sonnet-5-5", usage) == pytest.approx(2.0 + 1.0 + 0.2 + 2.5)


def test_repository_cases_are_valid():
    cases = load_cases()
    assert len(cases) >= 50
    for case in cases:
        assert case["kind"] in {"answer", "decline", "not_covered", "not_found"}
        if case["kind"] == "answer":
            assert case["key_facts"] and case["expected_sections"]
        else:
            assert case["expectation"]


def test_harness_gate_blocks_changed_grading_files(tmp_path, monkeypatch):
    from waypoint_api import instructor_eval

    (tmp_path / "judge.py").write_text("v1")
    monkeypatch.setattr(instructor_eval, "REPO", tmp_path)
    state = {"harness_paths": ["judge.py"]}
    instructor_eval.check_harness(state, approve=True)
    instructor_eval.check_harness(state, approve=False)
    (tmp_path / "judge.py").write_text("v2")
    with pytest.raises(SystemExit, match="approve-harness"):
        instructor_eval.check_harness(state, approve=False)
