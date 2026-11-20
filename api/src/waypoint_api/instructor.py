"""The AI instructor: answer a student's question from retrieved sources, with
citations. Facts come only from the passages; see docs/plans/03."""

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Literal

from waypoint_api.llm import Complete, Reply, Stream
from waypoint_api.retrieval import Jurisdiction, Passage

Level = Literal["PSTAR", "PPAER", "FLIGHT_TEST"]
Search = Callable[[str, Level, Jurisdiction, int], list[Passage]]
# {"role": "user" | "assistant", "content": str}; the last turn is the student's.
Turn = dict[str, str]

# Top retrieval scores: in-scope eval questions are all 0.395 or more,
# off-topic questions 0.307 or less (measured 2026-11-19).
MIN_SCORE = 0.35
CANADIAN_PASSAGES = 6
BACKGROUND_PASSAGES = 2

LEVELS = {
    "PSTAR": "the Student Pilot Permit exam (PSTAR)",
    "PPAER": "the Private Pilot Licence written exam (PPAER)",
    "FLIGHT_TEST": "the Private Pilot Licence flight test",
}

# The TC AIM's section numbers do not name the document; other sources do.
LABEL_PREFIXES = {"tc-aim": "TC AIM"}

NOT_FOUND = (
    "I could not find this in Waypoint's sources, so I can't answer it reliably. "
    "Please ask your flight instructor, or check the current Transport Canada "
    "publication."
)

SYSTEM_PROMPT = """\
You are Waypoint, a study companion for student pilots in Canada working \
toward the Private Pilot Licence (Aeroplane). You explain aviation knowledge \
clearly, at the student's level.

Each question comes with passages from Transport Canada publications, the \
Canadian Aviation Regulations and FAA handbooks. Ground your answer in them:
- Facts such as rules, numbers, limits and procedures must come from the \
passages. Explanations and examples may use general knowledge.
- After each fact, cite the passage that supports it with its label in square \
brackets, exactly as given, for example [TC AIM RAC 2.8.1] or [CAR 602.14]. \
Cite several as [CAR 602.14; TC AIM RAC 5.4]. Cite only labels you were given.
- If the passages do not answer the question, say so plainly and suggest the \
student ask their flight instructor or check the current official \
publication. Do not fill the gap from memory.
- Canadian rules come only from Canadian passages. Passages marked FAA \
describe United States practice: use them only for general theory such as \
aerodynamics, weather or physiology, and say in your sentence that the \
information comes from an FAA handbook. Brackets hold only labels.
- You are an educational aid. Do not decide whether a real flight should go \
ahead; explain the considerations and refer the student to their instructor \
and official sources.
- Use plain language and short paragraphs, and define abbreviations the first \
time you use them. You may end with one short question that checks the \
student's understanding."""

REWRITE_PROMPT = """\
You turn a student pilot's latest message into a search query for a \
library of Canadian aviation publications. Use the conversation to make the \
query stand on its own: replace words like "it" or "that" with what they \
refer to. Keep the student's meaning; do not answer. Reply with the query \
only."""


@dataclass
class Answer:
    """The instructor's answer, the passages it cites, and any reference it
    made to a passage it was not given."""

    text: str
    passages: list[Passage]
    citations: list[Passage] = field(default_factory=list)
    unknown_references: list[str] = field(default_factory=list)
    found: bool = True
    reply: Reply | None = None


def label(passage: Passage) -> str:
    """The reference the model cites, for example `TC AIM RAC 2.8.1`."""
    prefix = LABEL_PREFIXES.get(passage.document_id)
    return f"{prefix} {passage.section_ref}" if prefix else passage.section_ref


def gather(search: Search, question: str, level: Level) -> list[Passage]:
    """Canadian passages first, then a little FAA background, keeping only
    those relevant enough to answer from."""
    passages = search(question, level, "CA", CANADIAN_PASSAGES) + search(
        question, level, "non-CA", BACKGROUND_PASSAGES
    )
    return [p for p in passages if p.score >= MIN_SCORE]


def prompt(question: str, level: Level, passages: list[Passage]) -> list[dict]:
    """The user turn: the student's level, the passages with their labels and
    jurisdiction, then the question."""
    blocks = "\n\n".join(passage_block(p) for p in passages)
    text = (
        f"The student is preparing for {LEVELS[level]}.\n\n"
        f"<passages>\n{blocks}\n</passages>\n\n"
        f"<question>\n{question}\n</question>"
    )
    return [{"role": "user", "content": text}]


def passage_block(passage: Passage) -> str:
    """One passage, labelled with its reference, source and jurisdiction."""
    origin = (
        "Canadian"
        if passage.jurisdiction == "CA"
        else "FAA (United States): background only, not Canadian rules"
    )
    return (
        f'<passage label="{label(passage)}" source="{passage.document_title}, '
        f'{passage.edition}" jurisdiction="{origin}">\n{passage.text}\n</passage>'
    )


REFERENCE = re.compile(r"\[([^\[\]]+)\]")


def cited(text: str, passages: list[Passage]) -> tuple[list[Passage], list[str]]:
    """Passages the answer cites, in order of first citation, and references
    that match no passage it was given."""
    by_label = {label(p): p for p in passages}
    citations: list[Passage] = []
    unknown: list[str] = []
    for bracket in REFERENCE.findall(text):
        for reference in (r.strip() for r in bracket.split(";")):
            passage = by_label.get(reference)
            if passage is None:
                unknown.append(reference)
            elif passage not in citations:
                citations.append(passage)
    return citations, unknown


def search_query(conversation: list[Turn], complete: Complete) -> str:
    """The latest message as a search query. A follow-up is rewritten with
    the conversation so it stands on its own; a first question is used as is."""
    question = conversation[-1]["content"]
    if len(conversation) == 1:
        return question
    transcript = "\n\n".join(
        f"{turn['role']}: {turn['content']}" for turn in conversation[:-1]
    )
    text = (
        f"<conversation>\n{transcript}\n</conversation>\n\n"
        f"<latest_message>\n{question}\n</latest_message>"
    )
    return complete(REWRITE_PROMPT, [{"role": "user", "content": text}]).text.strip()


def messages(conversation: list[Turn], level: Level, passages: list[Passage]):
    """The earlier turns as they were, then the latest question with its
    level and passages."""
    return conversation[:-1] + prompt(conversation[-1]["content"], level, passages)


def respond(
    conversation: list[Turn],
    level: Level,
    search: Search,
    stream: Stream,
    complete: Complete,
) -> Iterator[str | Answer]:
    """Answer the latest message: yield the text as it is generated, then the
    finished Answer. When nothing relevant is retrieved, say so without
    asking the model. Model errors raise LLMError and no Answer follows."""
    passages = gather(search, search_query(conversation, complete), level)
    if not passages:
        yield NOT_FOUND
        yield Answer(NOT_FOUND, [], found=False)
        return
    for item in stream(SYSTEM_PROMPT, messages(conversation, level, passages)):
        if isinstance(item, Reply):
            citations, unknown = cited(item.text, passages)
            yield Answer(item.text, passages, citations, unknown, reply=item)
        else:
            yield item


def streamed(complete: Complete) -> Stream:
    """A Stream that sends a complete answer in one piece."""

    def stream(system: str, turns: list[dict]) -> Iterator[str | Reply]:
        reply = complete(system, turns)
        yield reply.text
        yield reply

    return stream


def ask(question: str, level: Level, search: Search, complete: Complete) -> Answer:
    """Answer one question, without streaming (the CLI and the eval)."""
    conversation = [{"role": "user", "content": question}]
    *_, answer = respond(conversation, level, search, streamed(complete), complete)
    return answer
