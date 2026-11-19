"""Waypoint API application."""

import os
from collections.abc import Iterator
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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


class RetrieveResponse(BaseModel):
    """Retrieved passages, most relevant first. Empty when nothing matches."""

    results: list[Passage]


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
