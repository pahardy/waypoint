import os

import psycopg
import pytest

from waypoint_api.migrate import MIGRATIONS_DIR, apply_migrations
from waypoint_api.seed import seed


@pytest.fixture
def empty_database():
    """Recreate a dedicated test database and yield its URL."""
    admin_url = os.environ["DATABASE_URL"]
    with psycopg.connect(admin_url, autocommit=True) as conn:
        conn.execute("DROP DATABASE IF EXISTS waypoint_migration_test")
        conn.execute("CREATE DATABASE waypoint_migration_test")
    yield psycopg.conninfo.make_conninfo(admin_url, dbname="waypoint_migration_test")
    with psycopg.connect(admin_url, autocommit=True) as conn:
        conn.execute("DROP DATABASE waypoint_migration_test WITH (FORCE)")


def test_migrations_apply_to_empty_database(empty_database):
    applied = apply_migrations(empty_database)
    assert applied[0] == "0001_enable_pgvector.sql"
    with psycopg.connect(empty_database) as conn:
        row = conn.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        assert row.fetchone() is not None


def test_migrations_are_not_reapplied(empty_database):
    apply_migrations(empty_database)
    assert apply_migrations(empty_database) == []


def test_objective_mastery_is_backfilled_from_submitted_attempts(
    empty_database, tmp_path
):
    for path in sorted(MIGRATIONS_DIR.glob("*.sql"))[:9]:
        (tmp_path / path.name).write_text(path.read_text())
    apply_migrations(empty_database, tmp_path)
    seed(empty_database)
    with psycopg.connect(empty_database) as conn:
        questions = conn.execute(
            "SELECT id, answer_index FROM question"
            " WHERE objective_id = 'pstar.regulations.014' ORDER BY id LIMIT 2"
        ).fetchall()
        for submitted_at in ("2026-11-24T12:00Z", None):
            (attempt_id,) = conn.execute(
                "INSERT INTO attempt (kind, exam, started_at, submitted_at, total)"
                " VALUES ('quiz', 'PSTAR', '2026-11-24T11:00Z', %s, 2) RETURNING id",
                (submitted_at,),
            ).fetchone()
            for position, (question_id, answer_index) in enumerate(questions):
                conn.execute(
                    "INSERT INTO attempt_item (attempt_id, position, question_id,"
                    " chosen_index) VALUES (%s, %s, %s, %s)",
                    (
                        attempt_id,
                        position,
                        question_id,
                        answer_index if position else None,
                    ),
                )
    apply_migrations(empty_database)
    with psycopg.connect(empty_database) as conn:
        rows = conn.execute(
            "SELECT objective_id, correct, seen FROM objective_mastery"
        ).fetchall()
    assert rows == [("pstar.regulations.014", 1, 2)]
