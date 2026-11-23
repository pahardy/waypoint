"""Load objectives, official questions and drafted practice questions from
db/seed into the database."""

import os
from pathlib import Path

import psycopg
import yaml
from psycopg.types.json import Jsonb

from waypoint_api.drafting import GeneratedQuestion

SEED_DIR = Path(__file__).resolve().parents[3] / "db" / "seed"


def load_objectives(conn: psycopg.Connection, path: Path) -> int:
    """Upsert the learning objectives and return how many there are."""
    objectives = yaml.safe_load(path.read_text())
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO objective (id, exam, subject, area, topic, text, ref,
                                   source, page)
            VALUES (%(id)s, %(exam)s, %(subject)s, %(area)s, %(topic)s, %(text)s,
                    %(ref)s, %(source)s, %(page)s)
            ON CONFLICT (id) DO UPDATE SET
                exam = EXCLUDED.exam, subject = EXCLUDED.subject,
                area = EXCLUDED.area, topic = EXCLUDED.topic, text = EXCLUDED.text,
                ref = EXCLUDED.ref, source = EXCLUDED.source, page = EXCLUDED.page
            """,
            [{"ref": None, **o} for o in objectives],
        )
    return len(objectives)


def load_pstar_questions(conn: psycopg.Connection, path: Path) -> int:
    """Upsert the official TP 11919 questions and return how many there are."""
    questions = yaml.safe_load(path.read_text())
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO question (id, exam, objective_id, number, stem, choices,
                                  answer_index, source, page, source_refs, origin,
                                  status)
            VALUES (%(id)s, 'PSTAR', %(objective_id)s, %(number)s, %(stem)s,
                    %(choices)s, %(answer_index)s, %(source)s, %(page)s,
                    %(references)s, 'official', 'reviewed')
            ON CONFLICT (id) DO UPDATE SET
                objective_id = EXCLUDED.objective_id, number = EXCLUDED.number,
                stem = EXCLUDED.stem, choices = EXCLUDED.choices,
                answer_index = EXCLUDED.answer_index, page = EXCLUDED.page,
                source_refs = EXCLUDED.source_refs
            """,
            [{**q, "choices": Jsonb(q["choices"])} for q in questions],
        )
    return len(questions)


def load_generated_questions(conn: psycopg.Connection, path: Path) -> int:
    """Upsert drafted practice questions, validating each one first, and
    return how many there are."""
    if not path.exists():
        return 0
    questions = [GeneratedQuestion(**q) for q in yaml.safe_load(path.read_text())]
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO question (id, exam, objective_id, stem, choices,
                                  answer_index, explanation, source,
                                  source_chunk_id, origin, status)
            VALUES (%(id)s, %(exam)s, %(objective_id)s, %(stem)s, %(choices)s,
                    %(answer_index)s, %(explanation)s, %(source)s,
                    %(source_chunk_id)s, 'generated', %(status)s)
            ON CONFLICT (id) DO UPDATE SET
                objective_id = EXCLUDED.objective_id, stem = EXCLUDED.stem,
                choices = EXCLUDED.choices, answer_index = EXCLUDED.answer_index,
                explanation = EXCLUDED.explanation, source = EXCLUDED.source,
                source_chunk_id = EXCLUDED.source_chunk_id, status = EXCLUDED.status
            """,
            [
                {**q.model_dump(), "choices": Jsonb(q.choices), "source": q.source}
                for q in questions
            ],
        )
    return len(questions)


def seed(database_url: str, seed_dir: Path = SEED_DIR) -> dict[str, int]:
    """Load objectives and questions; return their counts."""
    with psycopg.connect(database_url) as conn:
        return {
            "objectives": load_objectives(conn, seed_dir / "objectives.yaml"),
            "PSTAR questions": load_pstar_questions(
                conn, seed_dir / "pstar-questions.yaml"
            ),
            "PPAER questions": load_generated_questions(
                conn, seed_dir / "ppaer-questions.yaml"
            ),
        }


def main() -> None:
    """Seed the database in DATABASE_URL."""
    counts = seed(os.environ["DATABASE_URL"])
    print(", ".join(f"{name} {count}" for name, count in counts.items()))
