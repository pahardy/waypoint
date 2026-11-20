import json
import os

import psycopg
import pytest
from fastapi.testclient import TestClient

from waypoint_api.llm import LLMError, Reply
from waypoint_api.main import (
    app,
    database,
    knowledge_search,
    model_complete,
    model_stream,
)
from waypoint_api.migrate import apply_migrations
from waypoint_api.retrieval import Passage

CAR = Passage(
    chunk_id="cars:CAR 602.03:0",
    document_id="cars",
    document_title="Canadian Aviation Regulations",
    edition="2026-10-01",
    jurisdiction="CA",
    section_ref="CAR 602.03",
    heading_path=["Part VI", "CAR 602.03"],
    page=None,
    subject="air-law",
    text="No person shall act as a crew member within 12 hours after drinking.",
    score=0.7,
)


def stub_search(question, level, jurisdiction, limit):
    return [CAR] if jurisdiction == "CA" else []


def answer_stream(*pieces):
    def stream(system, messages):
        yield from pieces
        yield Reply("".join(pieces), "stub", 10, 5)

    return stream


def failing_stream(system, messages):
    yield "Twelve"
    raise LLMError("The language model timed out.")


def rewrite(system, messages):
    return Reply("rewritten query", "stub", 1, 1)


@pytest.fixture
def client():
    """A client with stub retrieval and model, saving to a test database."""
    admin_url = os.environ["DATABASE_URL"]
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute("DROP DATABASE IF EXISTS waypoint_chat_test")
        admin.execute("CREATE DATABASE waypoint_chat_test")
    url = psycopg.conninfo.make_conninfo(admin_url, dbname="waypoint_chat_test")
    apply_migrations(url)

    def test_database():
        with psycopg.connect(url) as conn:
            yield conn

    app.dependency_overrides[database] = test_database
    app.dependency_overrides[knowledge_search] = lambda: stub_search
    app.dependency_overrides[model_complete] = lambda: rewrite
    app.dependency_overrides[model_stream] = lambda: answer_stream(
        "Twelve hours ", "[CAR 602.03]."
    )
    yield TestClient(app)
    app.dependency_overrides.clear()
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute("DROP DATABASE waypoint_chat_test WITH (FORCE)")


QUESTION = {"role": "user", "content": "How long after drinking can I fly?"}


def chat(client, messages=(QUESTION,), **body):
    response = client.post(
        "/chat", json={"level": "PSTAR", "messages": list(messages), **body}
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/jsonl")
    return [json.loads(line) for line in response.text.splitlines()]


def test_chat_streams_the_answer_then_the_citations(client):
    events = chat(client)
    assert [e["type"] for e in events] == ["delta", "delta", "done"]
    assert "".join(e["text"] for e in events[:2]) == "Twelve hours [CAR 602.03]."
    done = events[-1]
    assert done["found"] is True
    assert done["unknown_references"] == []
    [citation] = done["citations"]
    assert citation["label"] == "CAR 602.03"
    assert citation["document_title"] == "Canadian Aviation Regulations"
    assert citation["edition"] == "2026-10-01"
    assert citation["section_ref"] == "CAR 602.03"
    assert citation["page"] is None
    assert citation["text"].startswith("No person shall act")


def test_a_conversation_is_saved_and_can_be_read_back(client):
    done = chat(client)[-1]
    response = client.get(f"/conversations/{done['conversation_id']}")
    assert response.status_code == 200
    saved = response.json()
    assert saved["level"] == "PSTAR"
    assert saved["messages"] == [
        {**QUESTION, "citations": [], "unknown_references": []},
        {
            "role": "assistant",
            "content": "Twelve hours [CAR 602.03].",
            "citations": ["cars:CAR 602.03:0"],
            "unknown_references": [],
        },
    ]


def test_a_follow_up_updates_the_same_conversation(client):
    first = chat(client)[-1]
    follow_up = [
        QUESTION,
        {"role": "assistant", "content": "Twelve hours [CAR 602.03]."},
        {"role": "user", "content": "Does that apply to passengers?"},
    ]
    second = chat(client, follow_up, conversation_id=first["conversation_id"])[-1]
    assert second["conversation_id"] == first["conversation_id"]
    saved = client.get(f"/conversations/{first['conversation_id']}").json()
    assert len(saved["messages"]) == 4


def test_a_model_error_ends_the_stream_with_an_error_and_saves_nothing(client):
    app.dependency_overrides[model_stream] = lambda: failing_stream
    events = chat(client)
    assert events == [
        {"type": "delta", "text": "Twelve"},
        {"type": "error", "message": "The language model timed out."},
    ]
    with psycopg.connect(
        psycopg.conninfo.make_conninfo(
            os.environ["DATABASE_URL"], dbname="waypoint_chat_test"
        )
    ) as conn:
        assert conn.execute("SELECT count(*) FROM conversation").fetchone()[0] == 0


def test_an_unknown_conversation_is_not_found(client):
    response = client.get("/conversations/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.parametrize(
    "body",
    [
        {"level": "PSTAR", "messages": []},
        {"level": "CPL", "messages": [QUESTION]},
        {"level": "PSTAR", "messages": [{"role": "assistant", "content": "Hi"}]},
        {"level": "PSTAR", "messages": [{"role": "user", "content": ""}]},
    ],
)
def test_invalid_chat_requests_are_rejected(client, body):
    assert client.post("/chat", json=body).status_code == 422
