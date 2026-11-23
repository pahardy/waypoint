import os
import random
from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from fastapi.testclient import TestClient

from waypoint_api.exams import PSTAR
from waypoint_api.main import app, clock, database, question_rng
from waypoint_api.migrate import apply_migrations
from waypoint_api.seed import seed

START = datetime(2026, 11, 23, 12, 0, tzinfo=UTC)


class Clock:
    """A clock the test moves by hand."""

    def __init__(self):
        self.now = START

    def __call__(self):
        return self.now


@pytest.fixture
def db_url():
    """A migrated, seeded test database."""
    admin_url = os.environ["DATABASE_URL"]
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute("DROP DATABASE IF EXISTS waypoint_attempts_test")
        admin.execute("CREATE DATABASE waypoint_attempts_test")
    url = psycopg.conninfo.make_conninfo(admin_url, dbname="waypoint_attempts_test")
    apply_migrations(url)
    seed(url)
    yield url
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute("DROP DATABASE waypoint_attempts_test WITH (FORCE)")


@pytest.fixture
def time():
    return Clock()


@pytest.fixture
def client(db_url, time):
    def test_database():
        with psycopg.connect(db_url) as conn:
            yield conn

    app.dependency_overrides[database] = test_database
    app.dependency_overrides[clock] = lambda: time()
    app.dependency_overrides[question_rng] = lambda: random.Random(0)
    yield TestClient(app)
    app.dependency_overrides.clear()


def answer_key(db_url, attempt):
    """The correct choice for each position, read from the database."""
    with psycopg.connect(db_url) as conn:
        answers = dict(conn.execute("SELECT id, answer_index FROM question"))
    return [answers[q["question_id"]] for q in attempt["questions"]]


def start(client, kind, objective_id=None):
    return start_exam(client, "PSTAR", kind, objective_id)


def start_exam(client, exam, kind, objective_id=None):
    body = {"exam": exam, "kind": kind, "objective_id": objective_id}
    response = client.post("/attempts", json=body)
    assert response.status_code == 201
    return response.json()


def answer(client, attempt, position, chosen_index):
    return client.post(
        f"/attempts/{attempt['id']}/answers",
        json={"position": position, "chosen_index": chosen_index},
    )


# Exam info


def test_exam_info_names_unverified_facts_and_lists_topics(client):
    info = client.get("/exams/PSTAR").json()
    assert (info["question_count"], info["pass_percent"]) == (50, 90)
    assert info["unverified"] == ["time_limit_s"]
    assert len(info["topics"]) == 14
    assert sum(t["question_count"] for t in info["topics"]) == 185


# Starting


def test_quiz_has_ten_official_questions_and_no_answers(client):
    response = client.post("/attempts", json={"exam": "PSTAR", "kind": "quiz"})
    attempt = response.json()
    assert len(attempt["questions"]) == 10
    assert attempt["deadline"] is None
    assert {q["origin"] for q in attempt["questions"]} == {"official"}
    assert "answer_index" not in response.text


def test_topic_quiz_uses_only_that_topic(client):
    attempt = start(client, "quiz", "pstar.regulations.014")
    assert len(attempt["questions"]) == 5
    assert {q["objective_id"] for q in attempt["questions"]} == {
        "pstar.regulations.014"
    }


def test_mock_has_fifty_distinct_questions_and_a_deadline(client):
    attempt = start(client, "mock")
    ids = [q["question_id"] for q in attempt["questions"]]
    assert len(ids) == len(set(ids)) == 50
    deadline = datetime.fromisoformat(attempt["deadline"])
    assert deadline == START + timedelta(seconds=PSTAR.time_limit_s)


def test_retired_questions_are_never_chosen(client, db_url):
    with psycopg.connect(db_url) as conn:
        conn.execute(
            "UPDATE question SET status = 'retired'"
            " WHERE objective_id = 'pstar.regulations.014'"
        )
    body = {"exam": "PSTAR", "kind": "quiz", "objective_id": "pstar.regulations.014"}
    assert client.post("/attempts", json=body).status_code == 422


# Answering and submitting


def test_round_trip_scores_a_perfect_quiz(client, db_url):
    attempt = start(client, "quiz")
    for position, correct in enumerate(answer_key(db_url, attempt)):
        assert answer(client, attempt, position, correct).status_code == 204
    submitted = client.post(f"/attempts/{attempt['id']}/submit").json()
    assert (submitted["correct"], submitted["total"], submitted["passed"]) == (
        10,
        10,
        True,
    )
    assert sum(t["total"] for t in submitted["topics"]) == 10
    assert all(item["correct"] for item in submitted["review"])
    assert client.get(f"/attempts/{attempt['id']}/results").json() == submitted


def test_answers_can_be_changed_before_submission(client, db_url):
    attempt = start(client, "quiz")
    correct = answer_key(db_url, attempt)[0]
    answer(client, attempt, 0, (correct + 1) % 4)
    answer(client, attempt, 0, correct)
    results = client.post(f"/attempts/{attempt['id']}/submit").json()
    assert results["correct"] == 1


def test_answer_one_second_after_the_limit_is_refused(client, db_url, time):
    attempt = start(client, "mock")
    key = answer_key(db_url, attempt)
    time.now = START + timedelta(seconds=PSTAR.time_limit_s - 1)
    assert answer(client, attempt, 0, key[0]).status_code == 204
    time.now = START + timedelta(seconds=PSTAR.time_limit_s + 1)
    assert answer(client, attempt, 1, key[1]).status_code == 409
    results = client.post(f"/attempts/{attempt['id']}/submit").json()
    assert results["correct"] == 1


def test_an_empty_attempt_scores_zero(client):
    attempt = start(client, "mock")
    results = client.post(f"/attempts/{attempt['id']}/submit").json()
    assert (results["correct"], results["total"], results["passed"]) == (0, 50, False)
    assert results["outcome"] == "fail"


def test_no_answers_after_submission(client):
    attempt = start(client, "quiz")
    client.post(f"/attempts/{attempt['id']}/submit")
    assert answer(client, attempt, 0, 0).status_code == 409


def test_a_choice_outside_the_question_is_refused(client):
    attempt = start(client, "quiz")
    assert answer(client, attempt, 0, 4).status_code == 409
    assert answer(client, attempt, 10, 0).status_code == 409


def test_results_wait_for_submission(client):
    attempt = start(client, "quiz")
    assert client.get(f"/attempts/{attempt['id']}/results").status_code == 409


def test_unknown_attempt_is_not_found(client):
    unknown = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"/attempts/{unknown}").status_code == 404
    assert client.post(f"/attempts/{unknown}/submit").status_code == 404


# PPAER practice questions (generated)


def review_all_generated(db_url):
    with psycopg.connect(db_url) as conn:
        conn.execute("UPDATE question SET status = 'reviewed' WHERE exam = 'PPAER'")


def test_drafts_are_not_used_until_reviewed(client, db_url):
    with psycopg.connect(db_url) as conn:
        conn.execute("UPDATE question SET status = 'draft' WHERE exam = 'PPAER'")
    assert client.get("/exams/PPAER").json()["topics"] == []
    body = {"exam": "PPAER", "kind": "quiz"}
    assert client.post("/attempts", json=body).status_code == 422


def test_generated_questions_come_back_as_generated(client, db_url):
    review_all_generated(db_url)
    response = client.post("/attempts", json={"exam": "PPAER", "kind": "quiz"})
    attempt = response.json()
    assert len(attempt["questions"]) == 10
    assert {q["origin"] for q in attempt["questions"]} == {"generated"}
    assert "answer_index" not in response.text
    results = client.post(f"/attempts/{attempt['id']}/submit").json()
    assert {item["origin"] for item in results["review"]} == {"generated"}


def add_ppaer_bank(db_url, per_subject=25):
    """Reviewed practice questions, `per_subject` for each PPAER subject;
    the correct answer is always choice 0."""
    with psycopg.connect(db_url) as conn:
        conn.execute("UPDATE question SET status = 'retired' WHERE exam = 'PPAER'")
        conn.execute(
            """
            INSERT INTO question (id, exam, objective_id, stem, choices,
                                  answer_index, explanation, source,
                                  source_chunk_id, origin, status)
            SELECT 'test.' || o.id, 'PPAER', o.id, 'Stem', '["a","b","c","d"]',
                   0, 'Because.', 'tc-aim', 'tc-aim:x:0', 'generated', 'reviewed'
            FROM (SELECT o.*, row_number() OVER (PARTITION BY subject ORDER BY id) n
                  FROM objective o WHERE exam = 'PPAER') o
            WHERE n <= %s
            """,
            (per_subject,),
        )


def subject_of(db_url, attempt):
    with psycopg.connect(db_url) as conn:
        subjects = dict(conn.execute("SELECT id, subject FROM objective"))
    return [subjects[q["objective_id"]] for q in attempt["questions"]]


def test_ppaer_mock_round_trip_gives_a_partial_pass(client, db_url):
    add_ppaer_bank(db_url)
    attempt = start_exam(client, "PPAER", "mock")
    subjects = subject_of(db_url, attempt)
    assert len(subjects) == 100
    assert {s: subjects.count(s) for s in set(subjects)} == {
        "air-law": 25,
        "navigation": 25,
        "meteorology": 25,
        "aeronautics": 25,
    }
    deadline = datetime.fromisoformat(attempt["deadline"])
    assert deadline == START + timedelta(hours=3)
    for position, subject in enumerate(subjects):
        answer(client, attempt, position, 1 if subject == "meteorology" else 0)

    results = client.post(f"/attempts/{attempt['id']}/submit").json()
    assert (results["correct"], results["outcome"], results["passed"]) == (
        75,
        "partial",
        False,
    )
    by_subject = {s["subject"]: s for s in results["subjects"]}
    assert by_subject["meteorology"]["supplementary"] == "PAMET"
    assert not by_subject["meteorology"]["passed"]
    assert by_subject["navigation"] == {
        "subject": "navigation",
        "correct": 25,
        "total": 25,
        "passed": True,
        "supplementary": None,
    }


def test_ppaer_mock_needs_25_reviewed_questions_per_subject(client, db_url):
    add_ppaer_bank(db_url, per_subject=24)
    body = {"exam": "PPAER", "kind": "mock"}
    assert client.post("/attempts", json=body).status_code == 422


def test_a_quiz_has_no_partial_pass(client, db_url):
    add_ppaer_bank(db_url)
    attempt = start_exam(client, "PPAER", "quiz")
    for position in range(len(attempt["questions"])):
        answer(client, attempt, position, 0)
    results = client.post(f"/attempts/{attempt['id']}/submit").json()
    assert results["outcome"] == "pass"
    assert all(s["supplementary"] is None for s in results["subjects"])
