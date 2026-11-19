import math
import os

import psycopg
import pytest
from fastapi.testclient import TestClient

from waypoint_api.main import app, database, query_embedder
from waypoint_api.migrate import apply_migrations
from waypoint_api.retrieval import DIMENSIONS, MODEL

DOCUMENTS = [
    ("aim", "TC AIM", "2026-2", "CA", ["PSTAR", "PPAER", "FLIGHT_TEST"]),
    ("awh", "Aviation Weather Handbook", "B", "non-CA", ["PPAER"]),
    ("ftg", "Flight Test Guide", "2021", "CA", ["FLIGHT_TEST"]),
]


def unit(*weights):
    """A 1,024-dimension vector with the given leading weights, normalized."""
    norm = math.sqrt(sum(w * w for w in weights))
    return [w / norm for w in weights] + [0.0] * (DIMENSIONS - len(weights))


# (chunk id, document, section, subject, model, vector); the query is unit(1).
CHUNKS = [
    ("aim:MET 2.4:0", "aim", "MET 2.4", "meteorology", MODEL, unit(1)),
    ("awh:AWH p.9:0", "awh", "AWH p.9", "meteorology", MODEL, unit(0.95, 0.31)),
    ("aim:RAC 1.8:0", "aim", "RAC 1.8", "air-law", MODEL, unit(1, 1)),
    ("ftg:FTG p.3:0", "ftg", "FTG p.3", "flight-test", MODEL, unit(0, 1)),
    ("aim:OLD 1.1:0", "aim", "OLD 1.1", "air-law", "older-model", unit(1)),
]


@pytest.fixture
def client():
    """A client whose API searches a seeded test database with a stub embedder."""
    admin_url = os.environ["DATABASE_URL"]
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute("DROP DATABASE IF EXISTS waypoint_retrieve_test")
        admin.execute("CREATE DATABASE waypoint_retrieve_test")
    url = psycopg.conninfo.make_conninfo(admin_url, dbname="waypoint_retrieve_test")
    apply_migrations(url)
    with psycopg.connect(url) as conn:
        seed(conn)
    questions = []

    def test_database():
        with psycopg.connect(url) as conn:
            yield conn

    def stub_embed(question):
        questions.append(question)
        return unit(1)

    app.dependency_overrides[database] = test_database
    app.dependency_overrides[query_embedder] = lambda: stub_embed
    test_client = TestClient(app)
    test_client.questions = questions
    yield test_client
    app.dependency_overrides.clear()
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute("DROP DATABASE waypoint_retrieve_test WITH (FORCE)")


def seed(conn):
    for doc_id, title, edition, jurisdiction, exams in DOCUMENTS:
        conn.execute(
            "INSERT INTO document (id, title, publisher, edition, published,"
            " retrieved_on, jurisdiction, url, sha256, exams)"
            " VALUES (%s, %s, 'TC', %s, '2026', '2026-11-19', %s, 'u', 'h', %s)",
            (doc_id, title, edition, jurisdiction, exams),
        )
    for chunk_id, doc_id, ref, subject, model, vector in CHUNKS:
        conn.execute(
            "INSERT INTO chunk (id, document_id, section_ref, heading_path, page,"
            " text, token_count, subject, embedding_model, embedding)"
            " VALUES (%s, %s, %s, %s, 4, %s, 3, %s, %s, %s::vector)",
            (
                chunk_id,
                doc_id,
                ref,
                ["Part", ref],
                f"Text of {ref}.",
                subject,
                model,
                vector,
            ),
        )


def ask(client, **body):
    response = client.post("/retrieve", json={"question": "Icing?", **body})
    assert response.status_code == 200
    return response.json()["results"]


def ids(results):
    return [r["chunk_id"] for r in results]


def test_results_are_ordered_by_score(client):
    results = ask(client)
    assert ids(results) == [
        "aim:MET 2.4:0",
        "awh:AWH p.9:0",
        "aim:RAC 1.8:0",
        "ftg:FTG p.3:0",
    ]
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] == pytest.approx(1.0)


def test_results_carry_everything_a_citation_needs(client):
    first = ask(client)[0]
    assert first == {
        "chunk_id": "aim:MET 2.4:0",
        "document_id": "aim",
        "document_title": "TC AIM",
        "edition": "2026-2",
        "jurisdiction": "CA",
        "section_ref": "MET 2.4",
        "heading_path": ["Part", "MET 2.4"],
        "page": 4,
        "subject": "meteorology",
        "text": "Text of MET 2.4.",
        "score": pytest.approx(1.0),
    }


def test_the_question_is_embedded(client):
    ask(client)
    assert client.questions == ["Icing?"]


def test_chunks_embedded_with_another_model_are_never_returned(client):
    assert "aim:OLD 1.1:0" not in ids(ask(client, limit=20))


def test_limit_is_respected(client):
    assert ids(ask(client, limit=2)) == ["aim:MET 2.4:0", "awh:AWH p.9:0"]


def test_jurisdiction_filter(client):
    assert "awh:AWH p.9:0" not in ids(ask(client, jurisdiction="CA"))
    assert ids(ask(client, jurisdiction="non-CA")) == ["awh:AWH p.9:0"]


def test_subject_filter(client):
    assert ids(ask(client, subject="meteorology")) == ["aim:MET 2.4:0", "awh:AWH p.9:0"]


def test_exam_filter(client):
    assert ids(ask(client, exam="FLIGHT_TEST")) == [
        "aim:MET 2.4:0",
        "aim:RAC 1.8:0",
        "ftg:FTG p.3:0",
    ]


def test_filters_combine(client):
    results = ask(client, exam="PPAER", subject="meteorology", jurisdiction="CA")
    assert ids(results) == ["aim:MET 2.4:0"]


def test_no_match_returns_an_empty_list(client):
    assert ask(client, subject="flight-test", jurisdiction="non-CA") == []


@pytest.mark.parametrize(
    "body",
    [
        {"question": ""},
        {"question": "Icing?", "limit": 21},
        {"question": "Icing?", "subject": "weather"},
        {"question": "Icing?", "jurisdiction": "US"},
    ],
)
def test_invalid_requests_are_rejected(client, body):
    assert client.post("/retrieve", json=body).status_code == 422
