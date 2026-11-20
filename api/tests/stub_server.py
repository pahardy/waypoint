"""The API with a stub model and stub retrieval, for the web end-to-end tests:
`uv run python tests/stub_server.py` (needs a migrated DATABASE_URL)."""

import time

import uvicorn

from waypoint_api.llm import Reply
from waypoint_api.main import app, knowledge_search, model_complete, model_stream
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
PHAK = Passage(
    chunk_id="faa-phak:PHAK p.437:0",
    document_id="faa-phak",
    document_title="Pilot's Handbook of Aeronautical Knowledge",
    edition="FAA-H-8083-25C",
    jurisdiction="non-CA",
    section_ref="PHAK p.437",
    heading_path=["Aeromedical Factors"],
    page=437,
    subject="aeronautics",
    text="Alcohol impairs judgment and coordination.",
    score=0.5,
)
ANSWER = [
    "You must not fly within 12 hours ",
    "after drinking alcohol [CAR 602.03]. ",
    "An FAA handbook explains that alcohol impairs judgment [PHAK p.437].",
]


def search(question, level, jurisdiction, limit):
    return [CAR] if jurisdiction == "CA" else [PHAK]


def stream(system, messages):
    for piece in ANSWER:
        time.sleep(0.2)
        yield piece
    yield Reply("".join(ANSWER), "stub", 1, 1)


def complete(system, messages):
    return Reply(messages[-1]["content"], "stub", 1, 1)


app.dependency_overrides[knowledge_search] = lambda: search
app.dependency_overrides[model_stream] = lambda: stream
app.dependency_overrides[model_complete] = lambda: complete

if __name__ == "__main__":
    uvicorn.run(app, port=8000)
