"""Command line: `uv run oral static-port`, then type or pipe the answer."""

import argparse
import os
import sys

import psycopg

from waypoint_api.exercises import DISCLAIMER, load_exercise, source_passages
from waypoint_api.grading import GradedAnswer, grade

MARK_LABELS = {"met": "Met", "partly_met": "Partly met", "not_met": "Not met"}


def show(graded: GradedAnswer, weights: dict[str, int]) -> None:
    """Print each criterion's mark with its evidence and reason, then the score."""
    for mark in graded.marks:
        print(
            f"\n{mark.criterion_id} (weight {weights[mark.criterion_id]}): "
            f"{MARK_LABELS[mark.mark]}"
        )
        if mark.evidence:
            print(f'  Evidence: "{mark.evidence}"')
        print(f"  {mark.reason}")
    print(f"\nScore: {graded.score}%")


def main() -> None:
    """Ask the exercise's question and grade the answer from stdin."""
    parser = argparse.ArgumentParser(prog="oral")
    parser.add_argument("exercise_id")
    args = parser.parse_args()

    exercise = load_exercise(args.exercise_id)
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        passages = source_passages(conn, exercise)
    print(DISCLAIMER)
    print(f"\n{exercise.prompt}\n")
    if sys.stdin.isatty():
        print("Your answer (end with Ctrl-D):")
    answer = sys.stdin.read().strip()
    graded = grade(exercise, passages, answer)
    show(graded, {c.id: c.weight for c in exercise.rubric})
    print(f"\n{DISCLAIMER}")
