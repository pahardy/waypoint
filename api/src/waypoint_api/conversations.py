"""Save and read instructor conversations (the `conversation` table)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

import psycopg
from psycopg.types.json import Jsonb
from pydantic import BaseModel

from waypoint_api.instructor import Level


class SavedMessage(BaseModel):
    """One turn. Assistant turns keep the chunk ids they cite, and any
    reference that matched no passage."""

    role: Literal["user", "assistant"]
    content: str
    citations: list[str] = []
    unknown_references: list[str] = []


class Conversation(BaseModel):
    """A saved conversation, oldest turn first."""

    id: UUID
    level: Level
    messages: list[SavedMessage]
    created_at: datetime
    updated_at: datetime


def save(
    conn: psycopg.Connection,
    conversation_id: UUID | None,
    level: Level,
    messages: list[SavedMessage],
) -> UUID:
    """Store the conversation, replacing an earlier save with the same id,
    and return its id."""
    row = conn.execute(
        """
        INSERT INTO conversation (id, level, messages)
        VALUES (coalesce(%s, gen_random_uuid()), %s, %s)
        ON CONFLICT (id) DO UPDATE
        SET level = EXCLUDED.level, messages = EXCLUDED.messages, updated_at = now()
        RETURNING id
        """,
        (conversation_id, level, Jsonb([m.model_dump() for m in messages])),
    ).fetchone()
    conn.commit()
    return row[0]


def load(conn: psycopg.Connection, conversation_id: UUID) -> Conversation | None:
    """The saved conversation, or None if there is none with this id."""
    row = conn.execute(
        "SELECT id, level, messages, created_at, updated_at"
        " FROM conversation WHERE id = %s",
        (conversation_id,),
    ).fetchone()
    return Conversation(**dict(zip(Conversation.model_fields, row))) if row else None
