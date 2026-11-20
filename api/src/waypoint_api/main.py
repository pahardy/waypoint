"""Waypoint API application."""

import os
from collections.abc import Iterable, Iterator
from typing import Annotated, Literal
from uuid import UUID

import psycopg
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from waypoint_api import llm
from waypoint_api.ask import database_search
from waypoint_api.conversations import Conversation, SavedMessage, load, save
from waypoint_api.instructor import Answer, Level, Search, label, respond
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
    allow_methods=["GET", "POST"],
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


def model_stream() -> llm.Stream:
    """The model call that streams the instructor's answer."""
    return llm.stream


def model_complete() -> llm.Complete:
    """The model call that rewrites follow-up questions."""
    return llm.complete


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


class Citation(Passage):
    """A passage the answer cites, with the label used in its text."""

    label: str


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
        citations=[
            Citation(**p.model_dump(), label=label(p)) for p in answer.citations
        ],
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
