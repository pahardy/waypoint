"""Command line: `uv run draft-questions --subject navigation --count 25`.

Drafts questions until the subject has `count` in
db/seed/ppaer-questions.yaml, one per objective, keeping only drafts the
judge can answer from the cited passage. Objectives that already have a
question are skipped.
"""

import argparse
import os
from pathlib import Path

import psycopg
import yaml

from waypoint_api.drafting import (
    GeneratedQuestion,
    candidate_objectives,
    check,
    cited_passages,
    draft,
    source_passages,
)
from waypoint_api.llm import LLMError
from waypoint_api.retrieval import embed_query
from waypoint_api.seed import SEED_DIR

QUESTIONS_FILE = SEED_DIR / "ppaer-questions.yaml"
HEADER = (
    "# Practice questions drafted by `uv run draft-questions`. Not official\n"
    "# Transport Canada questions. Review each one: set status to reviewed\n"
    "# (edit the text if needed) or retired. Only reviewed questions are used.\n"
)


def load_generated(path: Path = QUESTIONS_FILE) -> list[GeneratedQuestion]:
    """The drafted questions, validated."""
    if not path.exists():
        return []
    return [GeneratedQuestion(**item) for item in yaml.safe_load(path.read_text())]


def write_generated(
    questions: list[GeneratedQuestion], path: Path = QUESTIONS_FILE
) -> None:
    """Write the questions, in objective order."""
    data = [q.model_dump() for q in sorted(questions, key=lambda q: q.id)]
    path.write_text(
        HEADER + yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=88)
    )


def main() -> None:
    """Draft and check questions for the picked objectives."""
    parser = argparse.ArgumentParser(prog="draft-questions")
    parser.add_argument("--subject", default="air-law")
    parser.add_argument("--count", type=int, default=25, help="questions wanted")
    args = parser.parse_args()

    objectives = yaml.safe_load((SEED_DIR / "objectives.yaml").read_text())
    subjects = {o["id"]: o["subject"] for o in objectives}
    questions = load_generated()
    done = {q.objective_id for q in questions}
    have = sum(subjects[q.objective_id] == args.subject for q in questions)
    candidates = candidate_objectives(objectives, args.subject, args.count)
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        for objective in candidates:
            if have >= args.count:
                break
            if objective["id"] in done:
                continue
            passages = source_passages(conn, objective, embed_query)
            if not passages:
                print(f"skip    {objective['id']}: no source passages")
                continue
            try:
                question = draft(objective, passages)
                question.check = check(question, cited_passages(question, passages))
            except (ValueError, LLMError) as error:
                print(f"failed  {objective['id']}: {error}")
                continue
            if not question.passes_check:
                print(f"dropped {question.id}: {question.check.reason}")
                continue
            questions.append(question)
            write_generated(questions)
            have += 1
            print(f"ok      {question.id}")
    print(f"{args.subject}: {have} questions")
