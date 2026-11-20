"""Re-grade a variant's stored answers with the current judge, without asking
the instructor again: `uv run instructor-eval --regrade [--into DIR]`."""

import json
import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psycopg

from waypoint_api.instructor import Answer, cited, label
from waypoint_api.judge import judge
from waypoint_api.retrieval import Passage

PASSAGE = re.compile(
    r'<passage label="([^"]*)" source="[^"]*" jurisdiction="[^"]*">\n(.*?)\n</passage>',
    re.DOTALL,
)
COLUMNS = (
    "SELECT c.id, d.id, d.title, d.edition, d.jurisdiction, c.section_ref,"
    " c.heading_path, c.page, c.subject, c.text, 0.0"
    " FROM chunk c JOIN document d ON d.id = c.document_id"
)


def passage_rows(conn: psycopg.Connection, where: str, params: tuple) -> list[Passage]:
    """Chunks matching a condition, as passages (score not kept)."""
    rows = conn.execute(f"{COLUMNS} WHERE {where}", params).fetchall()
    return [Passage(**dict(zip(Passage.model_fields, r, strict=True))) for r in rows]


def passages_seen(
    conn: psycopg.Connection, row: dict, trace: list[dict]
) -> list[Passage]:
    """The exact passages the instructor was given for this answer.

    Newer rows record their chunk ids. Older rows are rebuilt from the
    prompt in the trace, matching both label and text, since some chunks
    share their text.
    """
    ids = row["meta"].get("passages")
    if ids:
        by_id = {p.chunk_id: p for p in passage_rows(conn, "c.id = ANY(%s)", (ids,))}
        return [by_id[i] for i in ids]
    found = []
    for block_label, text in PASSAGE.findall(trace[1]["content"]):
        matches = [
            p
            for p in passage_rows(conn, "c.text = %s", (text,))
            if label(p) == block_label
        ]
        if len(matches) != 1:
            raise LookupError(f"passage {block_label!r} matched {len(matches)} chunks")
        found.append(matches[0])
    return found


def regrade_variant(
    variant_dir: Path,
    out_dir: Path,
    cases: dict[str, dict],
    judge_model: str,
    grade,
    cost,
    workers: int = 6,
) -> list[dict]:
    """Re-judge every judged row in `variant_dir` and write the new rows to
    `out_dir/results.jsonl`. Replacing in place keeps the previous file as
    `results.before-regrade.jsonl`."""
    lines = (variant_dir / "results.jsonl").read_text().splitlines()
    rows = [json.loads(line) for line in lines if line]

    def regrade(row: dict) -> dict:
        case = cases[row["prompt_id"]]
        if row["model"] is None:
            return row
        path = variant_dir / "traces" / f"{row['prompt_id']}_rep{row['rep']}.json"
        trace = json.loads(path.read_text())
        with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
            passages = passages_seen(conn, row, trace)
        text = trace[-1]["content"]
        citations, unknown = cited(text, passages)
        judgement = judge(case, passages, text, judge_model)
        if not judgement.model.startswith(judge_model):
            raise RuntimeError(f"judge served {judgement.model}")
        judge_usage = {
            "input_tokens": judgement.input_tokens,
            "output_tokens": judgement.output_tokens,
        }
        scores, reasons = grade(
            case, Answer(text, passages, citations, unknown), judgement
        )
        return row | {
            "grade": scores,
            "explanation": reasons,
            "judge_model": judgement.model,
            "judge_usage": judge_usage,
            "cost_usd": round(
                cost(row["model"], row["usage"]) + cost(judge_model, judge_usage), 5
            ),
        }

    with ThreadPoolExecutor(max_workers=workers) as pool:
        regraded = list(pool.map(regrade, rows))
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "results.jsonl"
    if target.exists():
        shutil.copy(target, out_dir / "results.before-regrade.jsonl")
    target.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in regraded)
    )
    return regraded
