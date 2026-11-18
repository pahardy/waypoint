"""Apply SQL migrations from db/migrations in filename order."""

import os
from pathlib import Path

import psycopg

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "db" / "migrations"


def apply_migrations(
    database_url: str, migrations_dir: Path = MIGRATIONS_DIR
) -> list[str]:
    """Apply migrations not yet recorded, and return the names applied."""
    applied = []
    with psycopg.connect(database_url) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migration ("
            "name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        done = {row[0] for row in conn.execute("SELECT name FROM schema_migration")}
        for path in sorted(migrations_dir.glob("*.sql")):
            if path.name in done:
                continue
            conn.execute(path.read_text())
            conn.execute(
                "INSERT INTO schema_migration (name) VALUES (%s)", (path.name,)
            )
            applied.append(path.name)
    return applied


def main() -> None:
    """Apply migrations to the database in DATABASE_URL."""
    for name in apply_migrations(os.environ["DATABASE_URL"]):
        print(f"applied {name}")
