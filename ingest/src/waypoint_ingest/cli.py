"""Command-line entry point: `uv run ingest <command>`."""

import argparse
import logging

from waypoint_ingest.curriculum import extract_all, write_objectives
from waypoint_ingest.fetch import RAW_DIR, fetch_all
from waypoint_ingest.sources import load_sources


def main() -> None:
    """Run an ingest command."""
    parser = argparse.ArgumentParser(prog="ingest")
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="download manifest sources")
    fetch.add_argument("--priority", type=int, default=3, help="highest priority")
    commands.add_parser("objectives", help="extract learning objectives")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.command == "fetch":
        sources = [s for s in load_sources() if s.priority <= args.priority]
        for source_id, status in fetch_all(sources).items():
            print(f"{status:<10} {source_id}")
    elif args.command == "objectives":
        objectives, problems = extract_all(RAW_DIR)
        write_objectives(objectives)
        for exam in ("PSTAR", "PPAER", "FLIGHT_TEST"):
            count = sum(o.exam == exam for o in objectives)
            print(f"{exam:<12} {count} objectives")
        for problem in problems:
            print(f"check: {problem}")
