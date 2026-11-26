import os
from datetime import UTC, datetime

import psycopg
import pytest
from fastapi.testclient import TestClient

from waypoint_api.main import app, clock, database
from waypoint_api.migrate import apply_migrations
from waypoint_api.seed import seed
from waypoint_api.sessions import exercise_ids, load_any

NOW = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)


@pytest.fixture
def db_url():
    """A migrated, seeded test database with one TP 13723 page."""
    admin_url = os.environ["DATABASE_URL"]
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute("DROP DATABASE IF EXISTS waypoint_flight_test_test")
        admin.execute("CREATE DATABASE waypoint_flight_test_test")
    url = psycopg.conninfo.make_conninfo(admin_url, dbname="waypoint_flight_test_test")
    apply_migrations(url)
    seed(url)
    with psycopg.connect(url) as conn:
        conn.execute(
            "INSERT INTO document (id, title, publisher, edition, published,"
            " retrieved_on, jurisdiction, url, sha256) VALUES ('tp13723',"
            " 'Flight Test Guide', 'TC', 'Sixth edition', '2021', '2026-11-01',"
            " 'CA', 'https://tc.canada.ca', 'x')"
        )
        conn.execute(
            "INSERT INTO chunk (id, document_id, section_ref, heading_path, page,"
            " text, token_count, embedding_model, embedding) VALUES"
            " ('tp13723:TP 13723 p.33:0', 'tp13723', 'TP 13723 p.33', '{}', 33,"
            " 'Ex. 22 Forced Landing.', 4, 'voyage-4-large',"
            " array_fill(0, ARRAY[1024])::vector)"
        )
    yield url
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute("DROP DATABASE waypoint_flight_test_test WITH (FORCE)")


@pytest.fixture
def client(db_url):
    def test_database():
        with psycopg.connect(db_url) as conn:
            yield conn

    app.dependency_overrides[database] = test_database
    app.dependency_overrides[clock] = lambda: NOW
    yield TestClient(app)
    app.dependency_overrides.clear()


def item(client, objective_id):
    items = client.get("/flight-test").json()
    return next(i for i in items if i["objective_id"] == objective_id)


def save(client, objective_id, reviewed, note):
    return client.put(
        f"/flight-test/{objective_id}", json={"reviewed": reviewed, "note": note}
    )


def test_the_32_items_come_in_guide_order_with_aims(client):
    items = client.get("/flight-test").json()
    assert len(items) == 32
    assert [i["objective_id"] for i in items][:3] == [
        "flight-test.ex02a",
        "flight-test.ex02b",
        "flight-test.ex02c",
    ]
    assert items[-1]["objective_id"] == "flight-test.ex30"
    first = items[0]
    assert (
        first["exercise"]
        == "Ex. 2 Aeroplane Familiarization and Preparation for Flight"
    )
    assert first["title"] == "Documents and Airworthiness (Ground Item)"
    assert first["aim"].startswith("To correctly assess the validity of documents")
    assert first["reference"] == "TP 13723 Ex. 2 A"
    assert (first["reviewed"], first["note"]) == (False, "")


def test_an_item_cites_its_guide_page(client):
    forced = item(client, "flight-test.ex22a")
    assert forced["source"]["chunk_id"] == "tp13723:TP 13723 p.33:0"
    assert forced["source"]["text"] == "Ex. 22 Forced Landing."
    assert item(client, "flight-test.ex02a")["source"] is None


def test_related_exercises_match_the_exercise_files(client):
    expected = {}
    for exercise_id in exercise_ids():
        exercise = load_any(exercise_id)
        if exercise.exam == "FLIGHT_TEST":
            expected.setdefault(exercise.objective_id, []).append(exercise_id)
    items = client.get("/flight-test").json()
    found = {i["objective_id"]: i["exercise_ids"] for i in items if i["exercise_ids"]}
    assert found == expected
    assert item(client, "flight-test.ex22a")["exercise_ids"] == ["forced-landing"]


def test_the_mark_and_note_are_saved_and_changed(client):
    assert (
        save(client, "flight-test.ex22a", True, "Best glide for our C172?").status_code
        == 204
    )
    saved = item(client, "flight-test.ex22a")
    assert (saved["reviewed"], saved["note"]) == (True, "Best glide for our C172?")
    save(client, "flight-test.ex22a", False, "")
    changed = item(client, "flight-test.ex22a")
    assert (changed["reviewed"], changed["note"]) == (False, "")


def test_a_long_note_is_refused(client):
    assert save(client, "flight-test.ex22a", True, "x" * 501).status_code == 422
    assert save(client, "flight-test.ex22a", True, "x" * 500).status_code == 204


def test_a_pstar_objective_is_not_a_flight_test_item(client):
    assert save(client, "pstar.regulations.014", True, "").status_code == 404
