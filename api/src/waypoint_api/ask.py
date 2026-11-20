"""Command line: `uv run instructor "question" --level PPAER`."""

import argparse
import os
from typing import get_args

import psycopg

from waypoint_api.instructor import Answer, Level, Search, ask, label
from waypoint_api.llm import LLMError, complete
from waypoint_api.retrieval import EmbedQuery, RetrieveRequest, embed_query, retrieve


def database_search(
    conn: psycopg.Connection, embed: EmbedQuery = embed_query
) -> Search:
    """Search the knowledge base in `conn`, embedding each question once."""
    vectors: dict[str, list[float]] = {}

    def search(question, level, jurisdiction, limit):
        if question not in vectors:
            vectors[question] = embed(question)
        request = RetrieveRequest(
            question=question, exam=level, jurisdiction=jurisdiction, limit=limit
        )
        return retrieve(conn, request, vectors[question])

    return search


def show(answer: Answer) -> None:
    """Print the answer, then the sources it cites."""
    print(answer.text)
    if answer.citations:
        print("\nSources:")
        for p in answer.citations:
            print(f"  [{label(p)}] {p.document_title}, {p.edition}")
    if answer.unknown_references:
        print(f"\nCheck: cited but not retrieved: {answer.unknown_references}")


def main() -> None:
    """Answer one question from the knowledge base."""
    parser = argparse.ArgumentParser(prog="instructor")
    parser.add_argument("question")
    parser.add_argument("--level", choices=get_args(Level), default="PPAER")
    args = parser.parse_args()
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        try:
            answer = ask(args.question, args.level, database_search(conn), complete)
        except LLMError as error:
            raise SystemExit(f"Error: {error}") from error
    show(answer)
