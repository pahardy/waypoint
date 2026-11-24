"""Command line: `uv run scenario deteriorating-weather`, then answer each
stage. Piped input separates the stage answers with a line holding only
`---`."""

import argparse
import os
import sys

import psycopg

from waypoint_api.exercises import DISCLAIMER, load_scenario, source_passages
from waypoint_api.grading import grade
from waypoint_api.oral import show
from waypoint_api.scenarios import (
    SYNTHETIC,
    ScenarioState,
    overall_score,
    stage_exercise,
)


def read_answer() -> str:
    """One stage's answer: lines up to `---` or the end of input."""
    if sys.stdin.isatty():
        print("Your answer (end with a line holding only ---):")
    lines = []
    for line in sys.stdin:
        if line.strip() == "---":
            break
        lines.append(line)
    return "".join(lines).strip()


def main() -> None:
    """Show each stage, grade its answer, then show the overall score."""
    parser = argparse.ArgumentParser(prog="scenario")
    parser.add_argument("scenario_id")
    args = parser.parse_args()

    state = ScenarioState(load_scenario(args.scenario_id))
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        passages = source_passages(conn, state.scenario)
    print(f"{DISCLAIMER}\n{SYNTHETIC}\n\n{state.scenario.prompt}")
    scores = []
    while not state.finished:
        stage = state.stage
        print(f"\nStage {state.index + 1}: {stage.id}")
        for fact in stage.facts:
            print(f"- {fact}")
        print(f"\n{stage.question}\n")
        exercise = stage_exercise(state)
        graded = grade(exercise, passages, read_answer())
        show(graded, {c.id: c.weight for c in stage.rubric})
        scores.append(graded.score)
        state.advance()
    print(f"\nOverall score: {overall_score(scores)}% (stages: {scores})")
    print(f"\n{DISCLAIMER}\n{SYNTHETIC}")
