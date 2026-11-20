"""Instructor eval: `uv run instructor-eval [--cases a,b] [--reps N]`.

Runs each case in api/eval/instructor.yaml through the real instructor,
grades it with code checks and a model judge, and writes per-case results
to .claude/hillclimb/instructor/<variant>/ (results.jsonl, traces/,
errors.jsonl). Re-running skips (case, rep) pairs already written.
"""

import argparse
import hashlib
import json
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic
import psycopg
import yaml

from waypoint_api import llm
from waypoint_api.ask import database_search
from waypoint_api.instructor import NOT_FOUND, SYSTEM_PROMPT, Answer, ask, prompt
from waypoint_api.judge import JUDGE_MODEL, JudgeError, Judgement, judge
from waypoint_api.regrade import regrade_variant

REPO = Path(__file__).resolve().parents[3]
CASES_FILE = REPO / "api" / "eval" / "instructor.yaml"
FLOW_DIR = REPO / ".claude" / "hillclimb" / "instructor"

# USD per million tokens: (input, output). Cache reads 0.1x, writes 1.25x input.
PRICES = {
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-opus-5-5": (4.0, 20.0),
    "claude-haiku-5-5": (0.10, 0.50),
}

METRICS = [
    {"id": "pass", "label": "Pass", "kind": "binary"},
    {"id": "key_facts", "label": "Key facts", "kind": "float", "scale": 1},
    {"id": "grounded", "label": "Grounded", "kind": "binary"},
    {"id": "behaviour", "label": "Behaviour", "kind": "binary"},
    {"id": "citations_valid", "label": "Valid cites", "kind": "binary"},
    {"id": "cites_expected", "label": "Expected cite", "kind": "binary"},
]
PERF_FIELDS = ["latency_s", "cost_usd", "top_score"]
HARNESS_PATHS = [
    "api/src/waypoint_api/instructor_eval.py",
    "api/src/waypoint_api/judge.py",
    "api/eval/instructor.yaml",
    "api/src/waypoint_api/regrade.py",
]


def load_cases(path: Path = CASES_FILE) -> list[dict]:
    """The eval cases. Ids must be unique."""
    cases = yaml.safe_load(path.read_text())
    ids = [c["id"] for c in cases]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        raise ValueError(f"duplicate case ids: {sorted(duplicates)}")
    return cases


def cost(model: str, usage: dict) -> float:
    """Dollars for one call, from its model and token counts."""
    price_in, price_out = PRICES[model]
    return (
        usage["input_tokens"] * price_in
        + usage["output_tokens"] * price_out
        + usage.get("cache_read_input_tokens", 0) * price_in * 0.1
        + usage.get("cache_creation_input_tokens", 0) * price_in * 1.25
    ) / 1_000_000


def grade(case: dict, answer: Answer, judgement: Judgement | None) -> tuple[dict, dict]:
    """Scores per metric (None where a metric does not apply) and reasons."""
    if case["kind"] == "not_found":
        ok = float(not answer.found and answer.text == NOT_FOUND)
        scores = dict.fromkeys(m["id"] for m in METRICS)
        scores.update(passed=None, behaviour=ok)
        scores["pass"] = ok
        del scores["passed"]
        return scores, {
            "behaviour": "Not-found path taken." if ok else "Model was called."
        }
    verdict = judgement.verdict
    grounded = float(not verdict.unsupported_claims and not verdict.faa_as_canadian)
    valid = float(not answer.unknown_references)
    scores = {
        "grounded": grounded,
        "behaviour": float(verdict.behaviour_ok),
        "citations_valid": valid,
        "key_facts": None,
        "cites_expected": None,
    }
    if case["kind"] == "answer":
        stated = [f.stated for f in verdict.facts]
        scores["key_facts"] = sum(stated) / len(case["key_facts"])
        cited = {f"{p.document_id}:{p.section_ref}" for p in answer.citations}
        scores["cites_expected"] = float(bool(cited & set(case["expected_sections"])))
        complete = scores["key_facts"] == 1.0 and len(stated) == len(case["key_facts"])
        scores["pass"] = float(complete and grounded and valid)
    else:
        scores["pass"] = float(verdict.behaviour_ok and grounded and valid)
    reasons = {
        "key_facts": "; ".join(
            f"{'OK' if f.stated else 'MISSING'}: {f.fact} ({f.reason})"
            for f in verdict.facts
        ),
        "grounded": "; ".join(verdict.unsupported_claims)
        or "No unsupported claims."
        + (
            f" FAA as Canadian: {verdict.faa_reason}" if verdict.faa_as_canadian else ""
        ),
        "behaviour": verdict.behaviour_reason,
        "citations_valid": ", ".join(answer.unknown_references)
        or "All citations valid.",
    }
    return {m["id"]: scores[m["id"]] for m in METRICS}, reasons


def run_case(
    case: dict, rep: int, judge_model: str = JUDGE_MODEL
) -> tuple[dict, list[dict]]:
    """Answer and grade one case; return the result row and its trace."""
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        start = time.monotonic()
        answer = ask(
            case["question"], case["level"], database_search(conn), llm.complete
        )
        latency = time.monotonic() - start
    row = {
        "prompt_id": case["id"],
        "rep": rep,
        "prompt": case["question"],
        "tags": [case["kind"], case["level"]],
        "status": "ok",
        "latency_s": round(latency, 2),
        "top_score": round(max((p.score for p in answer.passages), default=0.0), 3),
        "meta": {
            "passages": [p.chunk_id for p in answer.passages],
            "citations": [p.chunk_id for p in answer.citations],
            "effort": llm.EFFORT,
        },
    }
    trace = [{"role": "system", "content": SYSTEM_PROMPT}]
    judgement = None
    if answer.reply is not None:
        reply = answer.reply
        if not reply.model.startswith(llm.MODEL):
            raise ServedModelError(f"asked for {llm.MODEL}, served {reply.model}")
        judgement = judge(case, answer.passages, answer.text, judge_model)
        if not judgement.model.startswith(judge_model):
            raise ServedModelError(f"judge served {judgement.model}")
        usage = {
            "input_tokens": reply.input_tokens,
            "output_tokens": reply.output_tokens,
            "cache_read_input_tokens": reply.cache_read_tokens,
            "cache_creation_input_tokens": reply.cache_creation_tokens,
        }
        judge_usage = {
            "input_tokens": judgement.input_tokens,
            "output_tokens": judgement.output_tokens,
        }
        row |= {
            "model": reply.model,
            "stop_reason": "end_turn",
            "usage": usage,
            "judge_model": judgement.model,
            "judge_usage": judge_usage,
            "cost_usd": round(
                cost(llm.MODEL, usage) + cost(judge_model, judge_usage), 5
            ),
        }
        trace.append(
            {
                "role": "user",
                "content": prompt(case["question"], case["level"], answer.passages)[0][
                    "content"
                ],
            }
        )
    else:
        row |= {"model": None, "stop_reason": None, "cost_usd": 0.0}
        trace.append({"role": "user", "content": case["question"]})
    trace.append({"role": "assistant", "content": answer.text})
    row["grade"], row["explanation"] = grade(case, answer, judgement)
    return row, trace


class ServedModelError(Exception):
    """The response came from a different model than requested."""


# Failures that end a case without a scorable answer; logged, never scored.
CASE_FAILURES = (
    llm.LLMError,
    ServedModelError,
    JudgeError,
    anthropic.APIError,
    psycopg.Error,
)


def done_keys(variant_dir: Path) -> set[tuple[str, int]]:
    """(case, rep) pairs already in results.jsonl."""
    path = variant_dir / "results.jsonl"
    if not path.exists():
        return set()
    rows = (json.loads(line) for line in path.read_text().splitlines() if line)
    return {(r["prompt_id"], r["rep"]) for r in rows}


def read_state() -> dict:
    """Loop state (goal, harness fingerprint, ...) kept across runs."""
    path = FLOW_DIR / "_state.json"
    return json.loads(path.read_text()) if path.exists() else {}


def write_state(state: dict) -> None:
    """Save loop state, always with the current metric declarations."""
    FLOW_DIR.mkdir(parents=True, exist_ok=True)
    state |= {"metrics": METRICS, "perf_fields": PERF_FIELDS}
    (FLOW_DIR / "_state.json").write_text(json.dumps(state, indent=2) + "\n")


def harness_sha(paths: list[str]) -> str:
    """Fingerprint of the grading files: the runner, judge and cases."""
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.encode())
        digest.update(hashlib.sha256((REPO / path).read_bytes()).digest())
    return digest.hexdigest()


def check_harness(state: dict, approve: bool) -> None:
    """Refuse to run if a grading file changed since the user approved it."""
    current = harness_sha(state.setdefault("harness_paths", HARNESS_PATHS))
    if approve:
        state["harness_sha"] = current
    elif state.get("harness_sha") != current:
        raise SystemExit(
            "Grading files changed since last approval "
            f"({', '.join(state['harness_paths'])}). Review the diff, then "
            "re-run with --approve-harness."
        )


def append(path: Path, record: dict) -> None:
    """Append one JSON line."""
    with path.open("a") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def summarize(variant_dir: Path) -> str:
    """Headline pass rate with a 95% interval, mean key facts, and cost."""
    rows = [
        json.loads(line)
        for line in (variant_dir / "results.jsonl").read_text().splitlines()
        if line
    ]
    n = len(rows)
    p = sum(r["grade"]["pass"] for r in rows) / n
    half = 1.96 * math.sqrt(p * (1 - p) / n)
    facts = [
        r["grade"]["key_facts"] for r in rows if r["grade"]["key_facts"] is not None
    ]
    spend = sum(r["cost_usd"] for r in rows)
    errors = variant_dir / "errors.jsonl"
    n_errors = len(errors.read_text().splitlines()) if errors.exists() else 0
    return (
        f"pass {p:.2f} (95% CI {max(0, p - half):.2f}-{min(1, p + half):.2f}) over {n} "
        f"case-reps; key facts {sum(facts) / len(facts):.2f}; "
        f"cost ${spend:.2f}; errors {n_errors}"
    )


def main() -> None:
    """Run the eval cases not yet done, then print the summary."""
    parser = argparse.ArgumentParser(prog="instructor-eval")
    parser.add_argument("--variant", default="baseline")
    parser.add_argument("--cases", help="comma-separated case ids (default: all)")
    parser.add_argument("--reps", type=int, default=1)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--judge-model", default=JUDGE_MODEL)
    parser.add_argument(
        "--regrade",
        action="store_true",
        help="re-judge the variant's stored answers instead of running cases",
    )
    parser.add_argument("--into", help="variant directory for --regrade output")
    parser.add_argument(
        "--approve-harness",
        action="store_true",
        help="record the current grading files as approved (the user's call)",
    )
    args = parser.parse_args()
    state = read_state()
    check_harness(state, args.approve_harness)
    write_state(state)

    cases = load_cases()
    if args.cases:
        wanted = args.cases.split(",")
        cases = [c for c in cases if c["id"] in wanted]
    variant_dir = FLOW_DIR / args.variant
    if args.regrade:
        out_dir = FLOW_DIR / (args.into or args.variant)
        by_id = {c["id"]: c for c in load_cases()}
        regrade_variant(variant_dir, out_dir, by_id, args.judge_model, grade, cost)
        print(summarize(out_dir))
        return
    (variant_dir / "traces").mkdir(parents=True, exist_ok=True)
    done = done_keys(variant_dir)
    todo = [(c, r) for c in cases for r in range(args.reps) if (c["id"], r) not in done]
    print(f"{len(todo)} case-reps to run ({len(done)} already done)")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(run_case, c, r, args.judge_model): (c, r) for c, r in todo
        }
        for future in as_completed(futures):
            case, rep = futures[future]
            try:
                row, trace = future.result()
            except CASE_FAILURES as error:
                failure = type(error).__name__
                append(
                    variant_dir / "errors.jsonl",
                    {
                        "prompt_id": case["id"],
                        "rep": rep,
                        "failure": failure,
                        "message": str(error),
                    },
                )
                print(f"  error  {case['id']}: {failure}: {error}")
                continue
            trace_path = variant_dir / "traces" / f"{case['id']}_rep{rep}.json"
            trace_path.write_text(json.dumps(trace, indent=2, ensure_ascii=False))
            append(variant_dir / "results.jsonl", row)
            print(f"  {'pass' if row['grade']['pass'] else 'FAIL'}   {case['id']}")
    print(summarize(variant_dir))
