from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from waypoint_api import llm
from waypoint_api.instructor import (
    NOT_FOUND,
    SYSTEM_PROMPT,
    ask,
    cited,
    label,
    prompt,
)
from waypoint_api.llm import LLMError, Reply, reply_from
from waypoint_api.retrieval import Passage


def passage(document_id, ref, jurisdiction="CA", score=0.6, text="Some text."):
    return Passage(
        chunk_id=f"{document_id}:{ref}:0",
        document_id=document_id,
        document_title=f"Title of {document_id}",
        edition="2026",
        jurisdiction=jurisdiction,
        section_ref=ref,
        heading_path=[ref],
        page=None,
        subject=None,
        text=text,
        score=score,
    )


AIM = passage("tc-aim", "AIR 3.9", text="Allow 24 hours.")
CAR = passage("cars", "CAR 602.03", text="Not within 12 hours.")
PHAK = passage(
    "faa-phak", "PHAK p.437", jurisdiction="non-CA", text="Alcohol and altitude."
)


class StubSearch:
    """Returns fixed passages per jurisdiction and records each search."""

    def __init__(self, canadian, background=()):
        self.results = {"CA": list(canadian), "non-CA": list(background)}
        self.calls = []

    def __call__(self, question, level, jurisdiction, limit):
        self.calls.append((question, level, jurisdiction, limit))
        return self.results[jurisdiction][:limit]


class StubModel:
    """Returns a fixed answer and records each request."""

    def __init__(self, text="An answer [CAR 602.03]."):
        self.text = text
        self.calls = []

    def __call__(self, system, messages):
        self.calls.append((system, messages))
        return Reply(self.text, "stub", 10, 5)


# Labels and prompt


def test_aim_labels_name_the_document_and_others_use_their_reference():
    assert label(AIM) == "TC AIM AIR 3.9"
    assert label(CAR) == "CAR 602.03"


def test_prompt_gives_level_then_labelled_passages_then_question():
    text = prompt("How long after drinking?", "PSTAR", [AIM, CAR])[0]["content"]
    level = text.index("Student Pilot Permit exam")
    first, second = (
        text.index('label="TC AIM AIR 3.9"'),
        text.index('label="CAR 602.03"'),
    )
    question = text.index("<question>\nHow long after drinking?")
    assert level < first < second < question
    assert "Allow 24 hours." in text and "Not within 12 hours." in text


def test_prompt_labels_faa_passages_as_background_only():
    text = prompt("q", "PPAER", [AIM, PHAK])[0]["content"]
    assert (
        'label="TC AIM AIR 3.9" source="Title of tc-aim, 2026" jurisdiction="Canadian"'
        in text
    )
    assert (
        'jurisdiction="FAA (United States): background only, not Canadian rules"'
        in text
    )


def test_the_model_gets_the_system_prompt_and_one_user_turn():
    model = StubModel()
    ask("How long after drinking?", "PSTAR", StubSearch([CAR]), model)
    system, messages = model.calls[0]
    assert system == SYSTEM_PROMPT
    assert [m["role"] for m in messages] == ["user"]


# Citations


def test_citations_are_mapped_to_passages_in_order_of_first_use():
    citations, unknown = cited(
        "Twelve hours [CAR 602.03]. Better 24 [TC AIM AIR 3.9; CAR 602.03].",
        [AIM, CAR],
    )
    assert citations == [CAR, AIM]
    assert unknown == []


def test_references_to_passages_not_retrieved_are_flagged():
    citations, unknown = cited("See [CAR 602.14] and [CAR 602.03].", [CAR])
    assert citations == [CAR]
    assert unknown == ["CAR 602.14"]


def test_text_inside_brackets_beyond_the_label_is_flagged():
    _, unknown = cited("[PHAK p.437, an FAA handbook]", [PHAK])
    assert unknown == ["PHAK p.437, an FAA handbook"]


# Retrieval and the not-found path


def test_canadian_passages_come_first_with_limited_faa_background():
    search = StubSearch([AIM, CAR], [PHAK])
    answer = ask("q", "PPAER", search, StubModel())
    assert answer.passages == [AIM, CAR, PHAK]
    assert [(c[2], c[3]) for c in search.calls] == [("CA", 6), ("non-CA", 2)]
    assert {c[1] for c in search.calls} == {"PPAER"}


def test_passages_below_the_relevance_threshold_are_dropped():
    weak = passage("tc-aim", "GEN 1.1", score=0.2)
    answer = ask("q", "PPAER", StubSearch([CAR, weak]), StubModel())
    assert answer.passages == [CAR]


def test_nothing_relevant_answers_not_found_without_calling_the_model():
    model = StubModel()
    weak = passage("tc-aim", "GEN 1.1", score=0.2)
    answer = ask("A lasagna recipe?", "PPAER", StubSearch([weak]), model)
    assert (answer.text, answer.found, answer.citations) == (NOT_FOUND, False, [])
    assert model.calls == []


def test_answer_reports_citations_and_unknown_references():
    model = StubModel("Twelve hours [CAR 602.03], see also [CAR 999.99].")
    answer = ask("q", "PSTAR", StubSearch([CAR]), model)
    assert answer.found
    assert answer.citations == [CAR]
    assert answer.unknown_references == ["CAR 999.99"]


# Model errors


def response(stop_reason, text="Done."):
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="text", text=text)],
        model="claude-sonnet-5-5",
        usage=SimpleNamespace(input_tokens=10, output_tokens=2),
    )


def test_a_finished_answer_is_accepted():
    assert reply_from(response("end_turn")).text == "Done."


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens", "pause_turn"])
def test_unfinished_answers_raise_instead_of_returning_partial_text(stop_reason):
    with pytest.raises(LLMError):
        reply_from(response(stop_reason))


@pytest.mark.parametrize(
    "error",
    [
        anthropic.APITimeoutError(request=httpx2.Request("POST", "https://api")),
        anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api")),
    ],
)
def test_api_failures_raise_a_clear_error(monkeypatch, error):
    def fail(**kwargs):
        raise error

    client = SimpleNamespace(
        beta=SimpleNamespace(messages=SimpleNamespace(create=fail))
    )
    monkeypatch.setattr(llm.anthropic, "Anthropic", lambda: client)
    with pytest.raises(LLMError, match="language model"):
        llm.complete("system", [{"role": "user", "content": "q"}])


def test_model_errors_reach_the_caller_with_no_answer():
    def failing_model(system, messages):
        raise LLMError("The language model timed out.")

    with pytest.raises(LLMError):
        ask("q", "PSTAR", StubSearch([CAR]), failing_model)
