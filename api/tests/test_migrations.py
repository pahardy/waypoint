import os

import psycopg
import pytest

from waypoint_api.migrate import apply_migrations


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
