"""The flight-test study companion: TP 13723 items as a personal checklist."""

from datetime import datetime

import psycopg
from psycopg.rows import namedtuple_row
from pydantic import BaseModel, Field

from waypoint_api.instructor import Citation, cite
from waypoint_api.retrieval import Passage
from waypoint_api.sessions import exercise_ids, load_any

ITEMS = """
    SELECT o.id, o.topic, o.text, o.detail, o.ref,
           c.id AS chunk_id, d.id AS document_id, d.title AS document_title,
           d.edition, d.jurisdiction, c.section_ref, c.heading_path, c.page,
           c.subject, c.text AS passage,
           coalesce(f.reviewed, false) AS reviewed, coalesce(f.note, '') AS note
    FROM objective o
    LEFT JOIN chunk c ON c.id = 'tp13723:TP 13723 p.' || o.page || ':0'
    LEFT JOIN document d ON d.id = c.document_id
    LEFT JOIN flight_test_checklist f ON f.objective_id = o.id
    WHERE o.exam = 'FLIGHT_TEST' ORDER BY o.id
"""

SAVE = """
    INSERT INTO flight_test_checklist (objective_id, reviewed, note, updated_at)
    SELECT id, %s, %s, %s FROM objective WHERE id = %s AND exam = 'FLIGHT_TEST'
    ON CONFLICT (objective_id) DO UPDATE SET
        reviewed = EXCLUDED.reviewed, note = EXCLUDED.note,
        updated_at = EXCLUDED.updated_at
"""


class ChecklistEntry(BaseModel):
    """The student's mark and note for one item."""

    reviewed: bool
    note: str = Field(max_length=500)


class ChecklistItem(ChecklistEntry):
    """A TP 13723 item: its exercise, title, aim and guide page, the
    exercises that practise it, and the student's entry."""

    objective_id: str
    exercise: str
    title: str
    aim: str | None
    reference: str | None
    source: Citation | None
    exercise_ids: list[str]


def practised_by() -> dict[str, list[str]]:
    """The exercise ids for each objective that has exercises."""
    found: dict[str, list[str]] = {}
    for exercise_id in exercise_ids():
        found.setdefault(load_any(exercise_id).objective_id, []).append(exercise_id)
    return found


def source(row) -> Citation | None:
    """The item's guide page as a citation, if it is in the knowledge base."""
    if row.chunk_id is None:
        return None
    return cite(
        Passage(
            chunk_id=row.chunk_id,
            document_id=row.document_id,
            document_title=row.document_title,
            edition=row.edition,
            jurisdiction=row.jurisdiction,
            section_ref=row.section_ref,
            heading_path=row.heading_path,
            page=row.page,
            subject=row.subject,
            text=row.passage,
            score=1.0,
        )
    )


def load(conn: psycopg.Connection) -> list[ChecklistItem]:
    """Every flight-test item in guide order, with the student's entry."""
    exercises = practised_by()
    rows = conn.cursor(row_factory=namedtuple_row).execute(ITEMS).fetchall()
    return [
        ChecklistItem(
            objective_id=r.id,
            exercise=r.topic,
            title=r.text,
            aim=r.detail,
            reference=r.ref,
            source=source(r),
            exercise_ids=exercises.get(r.id, []),
            reviewed=r.reviewed,
            note=r.note,
        )
        for r in rows
    ]


def save(
    conn: psycopg.Connection, objective_id: str, entry: ChecklistEntry, now: datetime
) -> bool:
    """Store the entry. False if the objective is not a flight-test item."""
    saved = conn.execute(SAVE, (entry.reviewed, entry.note, now, objective_id)).rowcount
    conn.commit()
    return saved == 1
