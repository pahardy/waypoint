"""Load objectives and official questions from db/seed into the database."""

import os
from pathlib import Path

import psycopg
import yaml
from psycopg.types.json import Jsonb

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
                                  answer_index, source, page, origin, status)
            VALUES (%(id)s, 'PSTAR', %(objective_id)s, %(number)s, %(stem)s,
                    %(choices)s, %(answer_index)s, %(source)s, %(page)s,
                    'official', 'reviewed')
            ON CONFLICT (id) DO UPDATE SET
                objective_id = EXCLUDED.objective_id, number = EXCLUDED.number,
                stem = EXCLUDED.stem, choices = EXCLUDED.choices,
                answer_index = EXCLUDED.answer_index, page = EXCLUDED.page
            """,
            [{**q, "choices": Jsonb(q["choices"])} for q in questions],
        )
    return len(questions)


def seed(database_url: str, seed_dir: Path = SEED_DIR) -> tuple[int, int]:
    """Load objectives and PSTAR questions; return their counts."""
    with psycopg.connect(database_url) as conn:
        objectives = load_objectives(conn, seed_dir / "objectives.yaml")
        questions = load_pstar_questions(conn, seed_dir / "pstar-questions.yaml")
    return objectives, questions


def main() -> None:
    """Seed the database in DATABASE_URL."""
    objectives, questions = seed(os.environ["DATABASE_URL"])
    print(f"objectives {objectives}, PSTAR questions {questions}")
