"""Draft practice questions from objectives and knowledge-base passages.

Drafts are written to db/seed/ppaer-questions.yaml as `status: draft`. The
owner reviews them in that file and marks each `reviewed` or `retired`.
"""

import random
from collections.abc import Callable
from typing import Literal

import anthropic
import psycopg
from pydantic import BaseModel, field_validator, model_validator

from waypoint_api import llm
from waypoint_api.instructor import MIN_SCORE, label, passage_block
from waypoint_api.judge import JUDGE_EFFORT, JUDGE_MODEL, JUDGE_TIMEOUT_S
from waypoint_api.retrieval import EmbedQuery, Passage, RetrieveRequest, retrieve

SEARCH_PASSAGES = 3


class AnswerCheck(BaseModel):
    """The judge's answer to a draft, from its cited passage alone."""

    answer_index: int | None
    reason: str


class GeneratedQuestion(BaseModel):
    """A practice question drafted by the model. Never an official question."""

    id: str
    exam: Literal["PPAER"] = "PPAER"
    objective_id: str
    stem: str
    choices: list[str]
    answer_index: int
    explanation: str
    source_chunk_id: str
    status: Literal["draft", "reviewed", "retired"] = "draft"
    check: AnswerCheck | None = None

    @field_validator("objective_id", "stem", "explanation", "source_chunk_id")
    @classmethod
    def not_blank(cls, value: str) -> str:
        """Every question needs an objective, a stem, an explanation and a
        source chunk."""
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @model_validator(mode="after")
    def four_distinct_choices(self) -> GeneratedQuestion:
        """Four different, non-empty choices and an answer among them."""
        if len(self.choices) != 4 or len(set(self.choices)) != 4:
            raise ValueError("needs four distinct choices")
        if not all(c.strip() for c in self.choices):
            raise ValueError("choices must not be blank")
        if self.answer_index not in range(4):
            raise ValueError("answer_index must be 0 to 3")
        return self

    @property
    def source(self) -> str:
        """The document the source chunk belongs to."""
        return self.source_chunk_id.split(":")[0]


class Draft(BaseModel):
    """What the drafting model returns."""

    stem: str
    choices: list[str]
    answer_index: int
    explanation: str
    source_label: str


DRAFT_SYSTEM = """\
You write multiple-choice practice questions for Canadian student pilots \
preparing for the Transport Canada PPAER written examination (Private Pilot \
Licence, Aeroplane).

Write one question for the learning objective, using only the passages given. \
The passages are current Canadian sources: the Canadian Aviation Regulations \
(CARs) or the TC AIM.

- The stem is self-contained and asks about one fact or rule in the passages.
- Exactly four choices. Exactly one is correct according to the passages. The \
other three are plausible to a student but clearly wrong from the passages.
- No "all of the above", "none of the above" or negatively worded stems.
- The explanation says why the answer is correct, in one to three sentences, \
and names the source section (for example "CAR 602.14").
- source_label is the label of the passage the answer rests on.
- Do not use knowledge from outside the passages.\
"""

CHECK_SYSTEM = """\
You check practice questions for an aviation study app. Using only the \
passages given (one regulation section, possibly split into parts), answer the multiple-choice question. Give the index (0 to 3) \
of the one choice the passages show to be correct. If they do not \
settle the question, or more than one choice could be correct, give null and \
say why.\
"""

Parse = Callable[..., BaseModel]


def draft_prompt(objective: dict, passages: list[Passage]) -> str:
    """The user turn: the objective, then the labelled passages."""
    blocks = "\n\n".join(passage_block(p) for p in passages)
    return (
        f"<objective>\n{objective['topic']}: {objective['text']}"
        f" ({objective.get('ref') or 'no reference'})\n</objective>\n\n"
        f"<passages>\n{blocks}\n</passages>"
    )


def check_prompt(question: GeneratedQuestion, passages: list[Passage]) -> str:
    """The user turn: the cited section, then the question without its answer."""
    choices = "\n".join(f"{i}. {c}" for i, c in enumerate(question.choices))
    blocks = "\n\n".join(passage_block(p) for p in passages)
    return f"{blocks}\n\n<question>\n{question.stem}\n\n{choices}\n</question>"


def parse(model: str, effort: str, system: str, prompt: str, schema) -> BaseModel:
    """One structured model call. Refusals and truncation raise LLMError."""
    with llm.api_errors():
        response = anthropic.Anthropic(timeout=JUDGE_TIMEOUT_S).messages.parse(
            model=model,
            max_tokens=8000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={"effort": effort},
            output_format=schema,
        )
    if response.stop_reason != "end_turn" or response.parsed_output is None:
        raise llm.LLMError(f"no structured answer ({response.stop_reason})")
    return response.parsed_output


def draft(
    objective: dict, passages: list[Passage], parse: Parse = parse
) -> GeneratedQuestion:
    """Draft and validate one question; raises ValueError if it is invalid."""
    result = parse(
        llm.MODEL, llm.EFFORT, DRAFT_SYSTEM, draft_prompt(objective, passages), Draft
    )
    first_chunk = {}
    for passage in passages:
        first_chunk.setdefault(label(passage), passage.chunk_id)
    if result.source_label not in first_chunk:
        raise ValueError(f"cited a passage it was not given: {result.source_label}")
    question = GeneratedQuestion(
        id=f"{objective['id']}.q1",
        objective_id=objective["id"],
        stem=result.stem,
        choices=result.choices,
        answer_index=result.answer_index,
        explanation=result.explanation,
        source_chunk_id=first_chunk[result.source_label],
    )
    return shuffled(question)


def shuffled(question: GeneratedQuestion) -> GeneratedQuestion:
    """Shuffle the choices, seeded by the question id, so the correct answer
    is not always in the position the model tends to put it."""
    order = list(range(4))
    random.Random(question.id).shuffle(order)
    return question.model_copy(
        update={
            "choices": [question.choices[i] for i in order],
            "answer_index": order.index(question.answer_index),
        }
    )


def cited_passages(question: GeneratedQuestion, passages: list[Passage]):
    """Every chunk of the section the question cites (a long section is
    split across several chunks with the same label)."""
    labels = {p.chunk_id: label(p) for p in passages}
    return [p for p in passages if label(p) == labels[question.source_chunk_id]]


def check(
    question: GeneratedQuestion, passages: list[Passage], parse: Parse = parse
) -> AnswerCheck:
    """Ask the judge to answer the question from its cited section alone."""
    return parse(
        JUDGE_MODEL,
        JUDGE_EFFORT,
        CHECK_SYSTEM,
        check_prompt(question, passages),
        AnswerCheck,
    )


def pick_objectives(objectives: list[dict], subject: str, count: int) -> list[dict]:
    """Every third essential objective of a subject, in order, up to `count`."""
    essential = [
        o for o in objectives if o["subject"] == subject and o.get("essential")
    ]
    return essential[::3][:count]


CAR_SECTION = """
    SELECT c.id, d.id, d.title, d.edition, d.jurisdiction, c.section_ref,
           c.heading_path, c.page, c.subject, c.text, 1.0
    FROM chunk c JOIN document d ON d.id = c.document_id
    WHERE d.id = 'cars' AND c.section_ref = %s
    ORDER BY c.id
"""


def car_section(conn: psycopg.Connection, ref: str) -> list[Passage]:
    """Every chunk of one CAR section, for example `CAR 602.14`."""
    rows = conn.execute(CAR_SECTION, (ref,)).fetchall()
    return [Passage(**dict(zip(Passage.model_fields, row))) for row in rows]


def source_passages(
    conn: psycopg.Connection, objective: dict, embed: EmbedQuery
) -> list[Passage]:
    """The CAR section an objective names, or else the closest Canadian
    passages to its text."""
    ref = objective.get("ref") or ""
    if ref.startswith("CAR "):
        return car_section(conn, ref)
    text = f"{objective['topic']}: {objective['text']}"
    request = RetrieveRequest(
        question=text, exam="PPAER", jurisdiction="CA", limit=SEARCH_PASSAGES
    )
    return [p for p in retrieve(conn, request, embed(text)) if p.score >= MIN_SCORE]
