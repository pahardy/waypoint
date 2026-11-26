"""Waypoint API application."""

import os
import random
from collections.abc import Callable, Iterable, Iterator
from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

import psycopg
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from waypoint_api import attempts, exams, flight_test, llm, progress, sessions
from waypoint_api.ask import database_search
from waypoint_api.conversations import Conversation, SavedMessage, load, save
from waypoint_api.exercises import Exercise, Scenario, source_passages
from waypoint_api.grading import GradingError
from waypoint_api.instructor import Answer, Citation, Level, Search, cite, respond
from waypoint_api.retrieval import (
    EmbedQuery,
    Passage,
    RetrieveRequest,
    embed_query,
    retrieve,
)

app = FastAPI(title="Waypoint API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type"],
)


def database() -> Iterator[psycopg.Connection]:
    """A connection to the database in DATABASE_URL for one request."""
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        yield conn


def query_embedder() -> EmbedQuery:
    """The function that embeds questions."""
    return embed_query


def knowledge_search(
    conn: Annotated[psycopg.Connection, Depends(database)],
    embed: Annotated[EmbedQuery, Depends(query_embedder)],
) -> Search:
    """How the instructor searches the knowledge base."""
    return database_search(conn, embed)


def clock() -> datetime:
    """The current time; attempts are timed by the server, not the browser."""
    return datetime.now(UTC)


def question_rng() -> random.Random:
    """The random source that chooses quiz and mock-exam questions."""
    return random.Random()


def model_stream() -> llm.Stream:
    """The model call that streams the instructor's answer."""
    return llm.stream


def model_complete() -> llm.Complete:
    """The model call that rewrites follow-up questions."""
    return llm.complete


def exercise_passages() -> Callable[
    [psycopg.Connection, Exercise | Scenario], list[Passage]
]:
    """How an exercise's cited passages are read."""
    return source_passages


def model_parse() -> llm.Parse:
    """The structured model call that grades exercise answers."""
    return llm.parse


class RetrieveResponse(BaseModel):
    """Retrieved passages, most relevant first. Empty when nothing matches."""

    results: list[Passage]


class Message(BaseModel):
    """One turn of the conversation sent by the client."""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    """The conversation so far, ending with the student's new message."""

    level: Level
    messages: list[Message] = Field(min_length=1, max_length=40)
    conversation_id: UUID | None = None

    @model_validator(mode="after")
    def ends_with_the_student(self) -> ChatRequest:
        """The last message is the one to answer."""
        if self.messages[-1].role != "user":
            raise ValueError("the last message must be the student's")
        return self


class Delta(BaseModel):
    """The next piece of the answer."""

    type: Literal["delta"] = "delta"
    text: str


class Done(BaseModel):
    """The answer is complete: its citations and the saved conversation."""

    type: Literal["done"] = "done"
    conversation_id: UUID
    found: bool
    citations: list[Citation]
    unknown_references: list[str]


class ChatError(BaseModel):
    """The answer could not be completed; any text sent is incomplete."""

    type: Literal["error"] = "error"
    message: str


ChatEvent = Annotated[Delta | Done | ChatError, Field(discriminator="type")]


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the API is running."""
    return {"status": "ok"}


@app.post("/retrieve")
def retrieve_passages(
    request: RetrieveRequest,
    conn: Annotated[psycopg.Connection, Depends(database)],
    embed: Annotated[EmbedQuery, Depends(query_embedder)],
) -> RetrieveResponse:
    """The knowledge-base passages that best answer a question, with their
    citations, optionally limited by exam, subject and jurisdiction."""
    return RetrieveResponse(results=retrieve(conn, request, embed(request.question)))


@app.post("/chat")
def chat(
    request: ChatRequest,
    conn: Annotated[psycopg.Connection, Depends(database)],
    search: Annotated[Search, Depends(knowledge_search)],
    stream: Annotated[llm.Stream, Depends(model_stream)],
    complete: Annotated[llm.Complete, Depends(model_complete)],
) -> Iterable[ChatEvent]:
    """Answer the latest message as JSON Lines: `delta` events with the
    text, then `done` with the citations. A model failure ends the stream
    with `error` instead of `done`, and nothing is saved."""
    conversation = [m.model_dump() for m in request.messages]
    try:
        for item in respond(conversation, request.level, search, stream, complete):
            if isinstance(item, Answer):
                answer = item
            else:
                yield Delta(text=item)
    except llm.LLMError as error:
        yield ChatError(message=str(error))
        return
    reply = SavedMessage(
        role="assistant",
        content=answer.text,
        citations=[p.chunk_id for p in answer.citations],
        unknown_references=answer.unknown_references,
    )
    saved = [SavedMessage(**turn) for turn in conversation] + [reply]
    yield Done(
        conversation_id=save(conn, request.conversation_id, request.level, saved),
        found=answer.found,
        citations=[cite(p) for p in answer.citations],
        unknown_references=answer.unknown_references,
    )


@app.get("/conversations/{conversation_id}")
def read_conversation(
    conversation_id: UUID,
    conn: Annotated[psycopg.Connection, Depends(database)],
) -> Conversation:
    """A saved conversation."""
    conversation = load(conn, conversation_id)
    if conversation is None:
        raise HTTPException(404, "No conversation with this id.")
    return conversation


class ExamInfo(BaseModel):
    """An exam's rules and the topics a quiz can be drawn from."""

    exam: str
    question_count: int
    time_limit_s: int
    pass_percent: int
    source: str
    unverified: list[str]
    mock_available: bool
    quiz_length: int
    topics: list[attempts.Topic]


class StartRequest(BaseModel):
    """Start a quiz (optionally on one topic) or a timed mock exam."""

    exam: Literal["PSTAR", "PPAER"]
    kind: attempts.Kind
    objective_id: str | None = None


class AnswerRequest(BaseModel):
    """The choice for one question of an attempt."""

    position: int = Field(ge=0)
    chosen_index: int = Field(ge=0)


@app.get("/exams/{exam}")
def exam_info(
    exam: Literal["PSTAR", "PPAER"],
    conn: Annotated[psycopg.Connection, Depends(database)],
) -> ExamInfo:
    """The exam's rules, with unverified facts named, and its quiz topics."""
    rules = exams.RULES[exam]
    return ExamInfo(
        exam=rules.exam,
        question_count=rules.question_count,
        time_limit_s=rules.time_limit_s,
        pass_percent=rules.pass_percent,
        source=rules.source,
        unverified=list(rules.unverified),
        mock_available=rules.mock_available,
        quiz_length=exams.QUIZ_LENGTH,
        topics=attempts.topics(conn, exam),
    )


@app.get("/progress/{exam}")
def read_progress(
    exam: Literal["PSTAR", "PPAER"],
    conn: Annotated[psycopg.Connection, Depends(database)],
) -> progress.Progress:
    """Answers so far per subject, and the weak objectives with reasons."""
    return progress.load(conn, exam)


class ConfidenceRequest(BaseModel):
    """A confidence rating, or null to clear it."""

    confidence: progress.Confidence | None


@app.put("/objectives/{objective_id}/confidence", status_code=204)
def rate_confidence(
    objective_id: str,
    body: ConfidenceRequest,
    conn: Annotated[psycopg.Connection, Depends(database)],
) -> None:
    """Set or clear the student's confidence in an answered objective."""
    if not progress.rate(conn, objective_id, body.confidence):
        raise HTTPException(404, "Answer a question on this objective first.")


@app.get("/flight-test")
def read_flight_test(
    conn: Annotated[psycopg.Connection, Depends(database)],
) -> list[flight_test.ChecklistItem]:
    """The TP 13723 items in guide order, with the student's checklist."""
    return flight_test.load(conn)


@app.put("/flight-test/{objective_id}", status_code=204)
def save_flight_test_item(
    objective_id: str,
    entry: flight_test.ChecklistEntry,
    conn: Annotated[psycopg.Connection, Depends(database)],
    now: Annotated[datetime, Depends(clock)],
) -> None:
    """Save the student's reviewed mark and note for one item."""
    if not flight_test.save(conn, objective_id, entry, now):
        raise HTTPException(404, "Not a flight-test item.")


@app.post("/attempts", status_code=201)
def start_attempt(
    request: StartRequest,
    conn: Annotated[psycopg.Connection, Depends(database)],
    now: Annotated[datetime, Depends(clock)],
    rng: Annotated[random.Random, Depends(question_rng)],
) -> attempts.Attempt:
    """Choose the questions and start the attempt. No answers are sent."""
    try:
        attempt_id = attempts.start(
            conn, request.exam, request.kind, request.objective_id, now, rng
        )
    except attempts.AttemptError as error:
        raise HTTPException(422, str(error))
    return attempts.load(conn, attempt_id)


@app.get("/attempts/{attempt_id}")
def read_attempt(
    attempt_id: UUID,
    conn: Annotated[psycopg.Connection, Depends(database)],
) -> attempts.Attempt:
    """An attempt with its questions and the choices made so far."""
    attempt = attempts.load(conn, attempt_id)
    if attempt is None:
        raise HTTPException(404, "No attempt with this id.")
    return attempt


@app.post("/attempts/{attempt_id}/answers", status_code=204)
def answer_question(
    attempt_id: UUID,
    request: AnswerRequest,
    conn: Annotated[psycopg.Connection, Depends(database)],
    now: Annotated[datetime, Depends(clock)],
) -> None:
    """Record a choice. Refused (409) after submission or the time limit."""
    if attempts.attempt_row(conn, attempt_id) is None:
        raise HTTPException(404, "No attempt with this id.")
    try:
        attempts.answer(conn, attempt_id, request.position, request.chosen_index, now)
    except attempts.AttemptError as error:
        raise HTTPException(409, str(error))


@app.post("/attempts/{attempt_id}/submit")
def submit_attempt(
    attempt_id: UUID,
    conn: Annotated[psycopg.Connection, Depends(database)],
    now: Annotated[datetime, Depends(clock)],
) -> attempts.Results:
    """Score the attempt and return its results."""
    if attempts.attempt_row(conn, attempt_id) is None:
        raise HTTPException(404, "No attempt with this id.")
    attempts.submit(conn, attempt_id, now)
    return attempts.results(conn, attempt_id)


@app.get("/attempts/{attempt_id}/results")
def read_results(
    attempt_id: UUID,
    conn: Annotated[psycopg.Connection, Depends(database)],
) -> attempts.Results:
    """A submitted attempt's results. 409 while it is still in progress."""
    if attempts.attempt_row(conn, attempt_id) is None:
        raise HTTPException(404, "No attempt with this id.")
    result = attempts.results(conn, attempt_id)
    if result is None:
        raise HTTPException(409, "This attempt has not been submitted.")
    return result


class StartSessionRequest(BaseModel):
    """Start a session on an exercise."""

    exercise_id: str = Field(pattern=r"^[a-z0-9-]+$", max_length=100)


class SessionAnswerRequest(BaseModel):
    """The student's answer to the current stage."""

    answer: str = Field(min_length=1, max_length=8000)


@app.get("/exercises")
def list_exercises() -> list[sessions.ExerciseSummary]:
    """Every oral exercise and scenario."""
    return sessions.summaries()


@app.post("/sessions", status_code=201)
def start_session(
    request: StartSessionRequest,
    conn: Annotated[psycopg.Connection, Depends(database)],
    now: Annotated[datetime, Depends(clock)],
) -> sessions.SessionState:
    """Start an exercise session at its first stage."""
    try:
        session_id = sessions.start(conn, request.exercise_id, now)
    except FileNotFoundError:
        raise HTTPException(404, "No exercise with this id.")
    return sessions.load(conn, session_id)


@app.get("/sessions/{session_id}")
def read_session(
    session_id: UUID,
    conn: Annotated[psycopg.Connection, Depends(database)],
) -> sessions.SessionState:
    """A session's revealed facts, current stage and graded stages."""
    state = sessions.load(conn, session_id)
    if state is None:
        raise HTTPException(404, "No session with this id.")
    return state


@app.post("/sessions/{session_id}/answers")
def answer_stage(
    session_id: UUID,
    request: SessionAnswerRequest,
    conn: Annotated[psycopg.Connection, Depends(database)],
    now: Annotated[datetime, Depends(clock)],
    passages: Annotated[
        Callable[[psycopg.Connection, Exercise | Scenario], list[Passage]],
        Depends(exercise_passages),
    ],
    parse: Annotated[llm.Parse, Depends(model_parse)],
) -> sessions.SessionState:
    """Grade the current stage and advance. 409 once the session is
    finished; 502 if grading fails, with nothing stored."""
    state = sessions.load(conn, session_id)
    if state is None:
        raise HTTPException(404, "No session with this id.")
    exercise = sessions.load_any(state.exercise_id)
    try:
        sessions.answer(
            conn, session_id, request.answer, passages(conn, exercise), parse, now
        )
    except sessions.SessionError as error:
        raise HTTPException(409, str(error))
    except llm.LLMError as error:
        raise HTTPException(502, str(error))
    except GradingError:
        raise HTTPException(502, "The answer could not be graded. Try again.")
    return sessions.load(conn, session_id)
