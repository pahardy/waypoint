"""Oral grading eval: `uv run oral-eval [--reps N]`.

Grades every answer in api/eval/oral.yaml N times (default 3) with the real
grader and writes one row per grading to .claude/hillclimb/oral/results.jsonl
(errors to errors.jsonl). Re-running skips (answer, rep) pairs already
written. The metrics are calculated in code and written to report.md there.
"""

import argparse
import json
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import psycopg
import yaml
from pydantic import BaseModel, Field

from waypoint_api import llm
from waypoint_api.exercises import Exercise, Mark, load_exercise, source_passages
from waypoint_api.grading import GradingError, grade
from waypoint_api.instructor_eval import ServedModelError, append, cost

REPO = Path(__file__).resolve().parents[3]
EVAL_FILE = REPO / "api" / "eval" / "oral.yaml"
OUT_DIR = REPO / ".claude" / "hillclimb" / "oral"
MARKS: list[Mark] = ["met", "partly_met", "not_met"]


class EvalAnswer(BaseModel):
    """A sample answer and the marks the rubric should give it."""

    id: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    expected: dict[str, Mark]


class EvalSet(BaseModel):
    """Sample answers to one exercise."""

    exercise: str = Field(min_length=1)
    answers: list[EvalAnswer] = Field(min_length=1)


def check_eval_set(eval_set: EvalSet, exercise: Exercise) -> None:
    """Raise ValueError on a repeated answer id, or expected marks that do
    not name every rubric criterion exactly once."""
    ids = [a.id for a in eval_set.answers]
    if len(set(ids)) != len(ids):
        raise ValueError(f"repeated answer ids: {sorted(ids)}")
    criteria = {c.id for c in exercise.rubric}
    for a in eval_set.answers:
        if set(a.expected) != criteria:
            raise ValueError(f"{a.id}: expected marks {sorted(a.expected)}")


def load_eval_set(path: Path = EVAL_FILE) -> tuple[EvalSet, Exercise]:
    """The checked eval set and its exercise."""
    eval_set = EvalSet(**yaml.safe_load(path.read_text()))
    exercise = load_exercise(eval_set.exercise)
    check_eval_set(eval_set, exercise)
    return eval_set, exercise


# Metrics. A row is one grading: {"answer_id", "rep", "marks": {criterion:
# {"mark", "evidence", "reason"}}, "score", ...}.


def marks_by_pair(rows: list[dict]) -> dict[tuple[str, str], list[Mark]]:
    """Every mark given to each (answer, criterion) pair, in rep order."""
    pairs: dict[tuple[str, str], list[Mark]] = {}
    for row in sorted(rows, key=lambda r: r["rep"]):
        for criterion, given in row["marks"].items():
            pairs.setdefault((row["answer_id"], criterion), []).append(given["mark"])
    return pairs


def consistency(rows: list[dict]) -> tuple[int, int]:
    """(answer-criterion pairs whose marks are all identical, all pairs)."""
    pairs = marks_by_pair(rows)
    return sum(len(set(m)) == 1 for m in pairs.values()), len(pairs)


def confusion(rows: list[dict], expected: dict[str, dict[str, Mark]]) -> Counter:
    """Counts of (expected mark, given mark) over every mark given."""
    return Counter(
        (expected[row["answer_id"]][criterion], given["mark"])
        for row in rows
        for criterion, given in row["marks"].items()
    )


def agreement(
    rows: list[dict], expected: dict[str, dict[str, Mark]]
) -> tuple[int, int]:
    """(marks that match the expected mark, all marks)."""
    table = confusion(rows, expected)
    return sum(n for (want, got), n in table.items() if want == got), table.total()


def spread(rows: list[dict]) -> dict[str, int]:
    """The range (highest minus lowest) of each answer's scores."""
    scores: dict[str, list[int]] = {}
    for row in rows:
        scores.setdefault(row["answer_id"], []).append(row["score"])
    return {a: max(s) - min(s) for a, s in scores.items()}


# Running


def recording_parse(usage: list[dict]) -> llm.Parse:
    """llm.parse that also records each call's token usage, and refuses a
    reply from a model other than the one asked for."""

    def parse(model, effort, system, prompt, schema):
        reply = llm.structured(model, effort, system, prompt, schema)
        if not reply.model.startswith(model):
            raise ServedModelError(f"asked for {model}, served {reply.model}")
        usage.append(
            {
                "input_tokens": reply.input_tokens,
                "output_tokens": reply.output_tokens,
                "cache_read_input_tokens": reply.cache_read_tokens,
                "cache_creation_input_tokens": reply.cache_creation_tokens,
            }
        )
        return schema.model_validate_json(reply.text)

    return parse


def run_one(exercise: Exercise, passages, sample: EvalAnswer, rep: int) -> dict:
    """Grade one answer once; the result row."""
    usage: list[dict] = []
    graded = grade(exercise, passages, sample.answer, recording_parse(usage))
    return {
        "answer_id": sample.id,
        "rep": rep,
        "marks": {
            m.criterion_id: {"mark": m.mark, "evidence": m.evidence, "reason": m.reason}
            for m in graded.marks
        },
        "score": graded.score,
        "model": llm.MODEL,
        "effort": llm.EFFORT,
        "calls": len(usage),
        "cost_usd": round(sum(cost(llm.MODEL, u) for u in usage), 5),
    }


def read_rows(path: Path) -> list[dict]:
    """The JSON lines in path, or none if it does not exist."""
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


FAILURES = (GradingError, llm.LLMError, ServedModelError)


def run(eval_set: EvalSet, exercise: Exercise, reps: int, workers: int) -> None:
    """Grade the (answer, rep) pairs not yet in results.jsonl."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    done = {(r["answer_id"], r["rep"]) for r in read_rows(OUT_DIR / "results.jsonl")}
    todo = [
        (a, rep)
        for a in eval_set.answers
        for rep in range(reps)
        if (a.id, rep) not in done
    ]
    print(f"{len(todo)} gradings to run ({len(done)} already done)")
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        passages = source_passages(conn, exercise)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(run_one, exercise, passages, a, rep): (a, rep)
            for a, rep in todo
        }
        for future in as_completed(futures):
            sample, rep = futures[future]
            try:
                row = future.result()
            except FAILURES as error:
                failure = {"answer_id": sample.id, "rep": rep, "error": repr(error)}
                append(OUT_DIR / "errors.jsonl", failure)
                print(f"  error  {sample.id} rep {rep}: {error!r}")
                continue
            append(OUT_DIR / "results.jsonl", row)
            print(f"  {row['score']:>3}%  {sample.id} rep {rep}")


# Report

LABELS = {"met": "met", "partly_met": "partly met", "not_met": "not met"}


def percent(part: int, whole: int) -> str:
    """'27/30 (90%)'."""
    return f"{part}/{whole} ({100 * part / whole:.0f}%)"


def mark_line(row: dict, criterion: str) -> str:
    """One given mark with its evidence and reason, as a list item."""
    given = row["marks"][criterion]
    evidence = f' "{given["evidence"]}"' if given["evidence"] else " (no evidence)"
    return (
        f"  - rep {row['rep']}: {LABELS[given['mark']]};{evidence}; {given['reason']}"
    )


def report(rows: list[dict], eval_set: EvalSet, errors: int) -> str:
    """The metrics, then every inconsistent pair and every wrong mark."""
    expected = {a.id: a.expected for a in eval_set.answers}
    same, pairs = consistency(rows)
    right, total = agreement(rows, expected)
    table = confusion(rows, expected)
    ranges = spread(rows)
    calls = sum(r["calls"] for r in rows)
    varied = sum(r > 0 for r in ranges.values())
    lines = [
        f"- Grader: `{rows[0]['model']}`, effort `{rows[0]['effort']}`",
        f"- Exercise: `{eval_set.exercise}`; {len(eval_set.answers)} answers; "
        + f"{len(rows)} gradings; {calls} model calls; {errors} errors",
        f"- Cost: ${sum(r['cost_usd'] for r in rows):.2f}",
        "",
        "| Measure | Result |",
        "|---|---|",
        f"| Consistency (identical marks; target 90%) | {percent(same, pairs)} |",
        f"| Agreement with expected marks | {percent(right, total)} |",
        f"| Answers whose score varies | {varied}/{len(ranges)} |",
        "",
        "Confusion (rows expected, columns given):",
        "",
        "| Expected | " + " | ".join(LABELS[m] for m in MARKS) + " |",
        "|---|---|---|---|",
        *(
            f"| {LABELS[want]} | "
            + " | ".join(str(table[want, got]) for got in MARKS)
            + " |"
            for want in MARKS
        ),
        "",
        "Scores per answer:",
        "",
        "| Answer | Scores | Range |",
        "|---|---|---|",
    ]
    by_answer: dict[str, list[dict]] = {}
    for row in sorted(rows, key=lambda r: r["rep"]):
        by_answer.setdefault(row["answer_id"], []).append(row)
    for a in eval_set.answers:
        scores = ", ".join(f"{r['score']}%" for r in by_answer.get(a.id, []))
        lines.append(f"| {a.id} | {scores} | {ranges.get(a.id, '')} |")
    lines += ["", "## Inconsistent or wrong marks", ""]
    for a in eval_set.answers:
        for criterion, want in a.expected.items():
            graded = by_answer.get(a.id, [])
            given = [r["marks"][criterion]["mark"] for r in graded]
            if len(set(given)) > 1 or any(g != want for g in given):
                lines.append(f"- **{a.id} / {criterion}**: expected {LABELS[want]}")
                lines += [mark_line(r, criterion) for r in graded]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Run the gradings not yet done, then write and print the report."""
    parser = argparse.ArgumentParser(prog="oral-eval")
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    eval_set, exercise = load_eval_set()
    run(eval_set, exercise, args.reps, args.workers)
    rows = read_rows(OUT_DIR / "results.jsonl")
    errors = len(read_rows(OUT_DIR / "errors.jsonl"))
    text = report(rows, eval_set, errors)
    (OUT_DIR / "report.md").write_text(text)
    print(text)
