import os
import re
from datetime import UTC, datetime

import psycopg
import pytest
from fastapi.testclient import TestClient

from waypoint_api import llm
from waypoint_api.grading import CriterionMark, Grading
from waypoint_api.main import app, clock, database, exercise_passages, model_parse
from waypoint_api.migrate import apply_migrations
from waypoint_api.sessions import exercise_ids

NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)


@pytest.fixture
def db_url():
    """A migrated test database."""
    admin_url = os.environ["DATABASE_URL"]
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute("DROP DATABASE IF EXISTS waypoint_sessions_test")
        admin.execute("CREATE DATABASE waypoint_sessions_test")
    url = psycopg.conninfo.make_conninfo(admin_url, dbname="waypoint_sessions_test")
    apply_migrations(url)
    yield url
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute("DROP DATABASE waypoint_sessions_test WITH (FORCE)")


class StubGrader:
    """Marks every criterion met, quoting the whole answer; or fails."""

    def __init__(self):
        self.failure = None
        self.calls = 0

    def __call__(self, model, effort, system, prompt, schema):
        self.calls += 1
        if self.failure:
            raise self.failure
        answer = re.search(r"<answer>\n(.*)\n</answer>", prompt, re.DOTALL).group(1)
        ids = re.findall(r'<criterion id="([^"]+)"', prompt)
        if answer == "skip a criterion":
            ids = ids[1:]
        return Grading(
            marks=[
                CriterionMark(criterion_id=i, mark="met", evidence=answer, reason=".")
                for i in ids
            ]
        )


@pytest.fixture
def grader():
    return StubGrader()


@pytest.fixture
def client(db_url, grader):
    def test_database():
        with psycopg.connect(db_url) as conn:
            yield conn

    app.dependency_overrides[database] = test_database
    app.dependency_overrides[clock] = lambda: NOW
    app.dependency_overrides[exercise_passages] = lambda: lambda conn, e: []
    app.dependency_overrides[model_parse] = lambda: grader
    yield TestClient(app)
    app.dependency_overrides.clear()


def start(client, exercise_id):
    response = client.post("/sessions", json={"exercise_id": exercise_id})
    assert response.status_code == 201
    return response.json()


def answer(client, session, text):
    return client.post(f"/sessions/{session['id']}/answers", json={"answer": text})


def reload(client, session):
    response = client.get(f"/sessions/{session['id']}")
    assert response.status_code == 200
    return response.json()


def test_the_exercises_are_listed_with_their_kind(client):
    listed = {e["id"]: e["kind"] for e in client.get("/exercises").json()}
    assert sorted(listed) == exercise_ids()
    assert listed["static-port"] == "oral"
    assert listed["deteriorating-weather"] == "scenario"


def test_a_scenario_starts_at_its_first_stage(client):
    session = start(client, "deteriorating-weather")
    assert session["current"]["id"] == "before-departure"
    assert session["revealed"] == session["current"]["facts"]
    assert "synthetic" in session["synthetic_notice"]
    assert session["graded"] == []
    assert session["overall_score"] is None


def test_each_stage_is_graded_and_the_state_survives_a_reload(client):
    session = start(client, "deteriorating-weather")
    first_facts = session["revealed"]

    after_one = answer(client, session, "Ceiling 3,000 ft.")
    assert after_one.status_code == 200
    state = reload(client, session)
    assert state == after_one.json()
    assert state["current"]["id"] == "en-route"
    assert state["revealed"][: len(first_facts)] == first_facts
    assert len(state["revealed"]) > len(first_facts)
    assert [g["score"] for g in state["graded"]] == [100]
    assert state["graded"][0]["marks"][0]["evidence"] == "Ceiling 3,000 ft."
    assert state["graded"][0]["marks"][2]["weight"] == 2

    answer(client, session, "Below the 2-mile minimum.")
    state = reload(client, session)
    assert state["current"] is None
    assert [g["id"] for g in state["graded"]] == ["before-departure", "en-route"]
    assert state["overall_score"] == 100


def test_an_oral_exercise_is_one_stage(client):
    session = start(client, "static-port")
    assert session["stage_count"] == 1
    assert session["intro"] is None
    assert session["synthetic_notice"] is None
    assert "static port" in session["current"]["question"]
    answer(client, session, "The altimeter freezes.")
    state = reload(client, session)
    assert state["current"] is None
    assert state["overall_score"] == 100


def test_a_finished_session_refuses_answers(client, grader):
    session = start(client, "static-port")
    answer(client, session, "The altimeter freezes.")
    response = answer(client, session, "Another answer.")
    assert response.status_code == 409
    assert grader.calls == 1


@pytest.mark.parametrize(
    "failure", [llm.LLMError("The language model timed out."), None]
)
def test_a_grading_failure_stores_nothing(client, grader, failure):
    session = start(client, "deteriorating-weather")
    grader.failure = failure
    text = "Ceiling 3,000 ft." if failure else "skip a criterion"
    response = answer(client, session, text)
    assert response.status_code == 502
    assert reload(client, session) == session


def test_an_unknown_exercise_or_session_is_not_found(client):
    response = client.post("/sessions", json={"exercise_id": "no-such-exercise"})
    assert response.status_code == 404
    unknown = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"/sessions/{unknown}").status_code == 404
    response = client.post(f"/sessions/{unknown}/answers", json={"answer": "x"})
    assert response.status_code == 404


def test_an_exercise_id_cannot_name_another_path(client):
    response = client.post("/sessions", json={"exercise_id": "../secrets"})
    assert response.status_code == 422
