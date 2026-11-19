"""Command-line entry point: `uv run ingest <command>`."""

import argparse
import logging
import os
from datetime import date
from typing import get_args

import psycopg

from waypoint_ingest.curriculum import extract_all, write_objectives
from waypoint_ingest.embeddings import embed
from waypoint_ingest.evaluate import (
    evaluate,
    load_questions,
    report,
    report_path,
    scores,
)
from waypoint_ingest.fetch import RAW_DIR, fetch_all
from waypoint_ingest.load import load_source, read_chunks, read_meta
from waypoint_ingest.pipeline import CHUNKS_DIR, chunk_source
from waypoint_ingest.retrieve import Method, search
from waypoint_ingest.sources import REPO_ROOT, Source, load_sources


def main() -> None:
    """Run an ingest command."""
    parser = argparse.ArgumentParser(prog="ingest")
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="download manifest sources")
    fetch.add_argument("--priority", type=int, default=3, help="highest priority")
    commands.add_parser("objectives", help="extract learning objectives")
    chunk = commands.add_parser("chunk", help="split a source into citable chunks")
    chunk.add_argument("source_id", help="manifest id, for example tc-aim")
    load = commands.add_parser("load", help="embed a source's chunks into the database")
    load.add_argument("source_id", help="manifest id, for example tc-aim")
    find = commands.add_parser("search", help="show the chunks nearest a question")
    find.add_argument("query")
    find.add_argument("--limit", type=int, default=5)
    find.add_argument("--method", choices=get_args(Method), default="vector")
    score = commands.add_parser("eval", help="score retrieval on the eval set")
    score.add_argument("--method", choices=get_args(Method), default="vector")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.command == "fetch":
        run_fetch(args.priority)
    elif args.command == "objectives":
        run_objectives()
    elif args.command == "chunk":
        run_chunk(source_by_id(args.source_id))
    elif args.command == "load":
        run_load(source_by_id(args.source_id))
    elif args.command == "search":
        run_search(args.query, args.method, args.limit)
    elif args.command == "eval":
        run_eval(args.method)


def source_by_id(source_id: str) -> Source:
    """The manifest entry with this id."""
    return next(s for s in load_sources() if s.id == source_id)


def run_fetch(priority: int) -> None:
    """Download manifest sources up to a priority."""
    sources = [s for s in load_sources() if s.priority <= priority]
    for source_id, status in fetch_all(sources).items():
        print(f"{status:<10} {source_id}")


def run_objectives() -> None:
    """Extract learning objectives from the study guides."""
    objectives, problems = extract_all(RAW_DIR)
    write_objectives(objectives)
    for exam in ("PSTAR", "PPAER", "FLIGHT_TEST"):
        count = sum(o.exam == exam for o in objectives)
        print(f"{exam:<12} {count} objectives")
    for problem in problems:
        print(f"check: {problem}")


def run_chunk(source: Source) -> None:
    """Split a source into chunks and report their sizes."""
    chunks, missing = chunk_source(source)
    sizes = sorted(c.token_count for c in chunks)
    sections = len({c.section_ref for c in chunks})
    print(f"{len(chunks)} chunks from {sections} sections")
    print(f"tokens: min {sizes[0]}, median {sizes[len(sizes) // 2]}, max {sizes[-1]}")
    for heading in missing:
        print(
            f"check: heading not found: {heading.ref} {heading.title} (p{heading.page})"
        )


def run_load(source: Source) -> None:
    """Embed new or changed chunks and write them to the database."""
    chunks = read_chunks(CHUNKS_DIR / f"{source.id}.jsonl")
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        result = load_source(conn, source, read_meta(RAW_DIR, source.id), chunks, embed)
    print(
        f"embedded {result.embedded}, unchanged {result.unchanged},"
        f" removed {result.removed}"
    )


def run_search(query: str, method: Method, limit: int) -> None:
    """Print the chunks that best answer a question."""
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        for hit in search(conn, query, embed, method, limit):
            print(f"{hit.score:.3f}  {hit.id}  (edition {hit.edition})")
            print(f"       {hit.text[:160]!r}")


def run_eval(method: Method) -> None:
    """Score retrieval on the eval set and write a report to docs/evals/."""
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        outcomes = evaluate(conn, load_questions(), embed, method)
        chunk_count = conn.execute("SELECT count(*) FROM chunk").fetchone()[0]
        sources = [r[0] for r in conn.execute("SELECT id FROM document ORDER BY id")]
    today = date.today()
    path = report_path(method, sources, today)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report(outcomes, method, sources, chunk_count, today))
    recall, mrr = scores(outcomes)
    print(f"recall@5 {recall:.2f}, MRR@10 {mrr:.2f} over {len(outcomes)} questions")
    print(f"report: {path.relative_to(REPO_ROOT)}")
