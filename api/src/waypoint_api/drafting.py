"""Draft practice questions from objectives and knowledge-base passages.

Drafts are written to db/seed/ppaer-questions.yaml as `status: draft`. The
owner reviews them in that file and marks each `reviewed` or `retired`.
"""

import random
from collections.abc import Callable
from typing import Literal

import anthropic
import psycopg
from anthropic import transform_schema
from pydantic import BaseModel, field_validator, model_validator

from waypoint_api import llm
from waypoint_api.instructor import MIN_SCORE, label, passage_block
from waypoint_api.judge import JUDGE_EFFORT, JUDGE_MODEL, JUDGE_TIMEOUT_S
from waypoint_api.retrieval import EmbedQuery, Passage, RetrieveRequest, retrieve

CANADIAN_PASSAGES = 3
BACKGROUND_PASSAGES = 2


class AnswerCheck(BaseModel):
    """The judge's answer to a draft, from its cited passage alone, and
    whether the answer leans on FAA material for something Canada-specific."""

    answer_index: int | None
    faa_as_canadian: bool = False
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
    def passes_check(self) -> bool:
        """The judge reached the same answer, without FAA rules as Canadian."""
        return (
            self.check is not None
            and self.check.answer_index == self.answer_index
            and not self.check.faa_as_canadian
        )

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
Canadian passages (the Canadian Aviation Regulations or the TC AIM) come \
first. FAA (United States) passages are background: use them only for facts \
that are the same in every country, such as aerodynamics, engines, \
instruments or weather physics. Never base a question on an FAA rule, \
procedure, limit or report format (for example METAR or TAF codes, airspace, \
phraseology).

- The stem is self-contained and asks about one fact or rule in the passages.
- Exactly four choices. Exactly one is correct according to the passages. The \
other three are plausible to a student but clearly wrong from the passages.
- No "all of the above", "none of the above" or negatively worded stems.
- The explanation says why the answer is correct, in one to three sentences, \
and names the source section (for example "CAR 602.14" or "TC AIM MET 3.9").
- source_label is the label of the passage the answer rests on.
- Do not use knowledge from outside the passages.\
"""

CHECK_SYSTEM = """\
You check practice questions for Canadian student pilots. Using only the \
passages given (one source section, possibly split into parts), answer the \
multiple-choice question. Give the index (0 to 3) of the one choice the \
passages show to be correct. If they do not settle the question, or more than \
one choice could be correct, give null and say why.

Set faa_as_canadian to true if the passages are FAA (United States) material \
and the question asks about a rule, procedure, limit or format that may \
differ in Canada. Facts that are the same everywhere (aerodynamics, engines, \
instruments, weather physics) are fine from FAA passages.\
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
    """One structured model call with server-side fallback, as for the
    instructor. Refusals and truncation raise LLMError before the JSON is read:
    a refused answer can end in filler text that is not valid JSON."""
    output_format = {"type": "json_schema", "schema": transform_schema(schema)}
    with llm.api_errors():
        response = anthropic.Anthropic(timeout=JUDGE_TIMEOUT_S).beta.messages.create(
            model=model,
            max_tokens=8000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={"effort": effort, "format": output_format},
            betas=[llm.FALLBACK_BETA],
            fallbacks="default",
        )
    return schema.model_validate_json(llm.reply_from(response).text)


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


def candidate_objectives(objectives: list[dict], subject: str, count: int):
    """A subject's essential objectives: `count` evenly spaced ones first,
    then the rest in order, so a failed draft can be replaced."""
    essential = [
        o for o in objectives if o["subject"] == subject and o.get("essential")
    ]
    spread = [essential[i * len(essential) // count] for i in range(count)]
    return spread + [o for o in essential if o not in spread]


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
    passages to its text, then a little FAA background."""
    ref = objective.get("ref") or ""
    if ref.startswith("CAR "):
        return car_section(conn, ref)
    text = f"{objective['topic']}: {objective['text']}"
    vector = embed(text)
    passages = []
    for jurisdiction, limit in [
        ("CA", CANADIAN_PASSAGES),
        ("non-CA", BACKGROUND_PASSAGES),
    ]:
        request = RetrieveRequest(
            question=text, exam="PPAER", jurisdiction=jurisdiction, limit=limit
        )
        passages += retrieve(conn, request, vector)
    return [p for p in passages if p.score >= MIN_SCORE]
