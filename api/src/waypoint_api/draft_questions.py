"""Command line: `uv run draft-questions --subject air-law --count 20`.

Drafts one question per picked objective, checks that each can be answered
from its cited passage, and adds it to db/seed/ppaer-questions.yaml.
Objectives that already have a question in the file are skipped.
"""

import argparse
import os
from pathlib import Path

import psycopg
import yaml

from waypoint_api.drafting import (
    GeneratedQuestion,
    check,
    cited_passages,
    draft,
    pick_objectives,
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
    parser.add_argument("--count", type=int, default=20)
    args = parser.parse_args()

    objectives = yaml.safe_load((SEED_DIR / "objectives.yaml").read_text())
    questions = load_generated()
    done = {q.objective_id for q in questions}
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        for objective in pick_objectives(objectives, args.subject, args.count):
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
            questions.append(question)
            write_generated(questions)
            agrees = question.check.answer_index == question.answer_index
            print(f"{'ok' if agrees else 'CHECK':<7} {question.id}")
