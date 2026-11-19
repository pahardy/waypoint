"""Source manifest: the documents Waypoint acquires."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, HttpUrl, field_validator, model_validator

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCES_FILE = REPO_ROOT / "ingest" / "sources.yaml"
EXCLUDED_PUBLISHERS = {"nav canada"}


class Source(BaseModel):
    """One document listed in the manifest."""

    id: str
    title: str
    publisher: str
    tp_number: str | None = None
    edition: str
    published: str
    url: HttpUrl
    jurisdiction: Literal["CA", "non-CA"]
    format: Literal["pdf", "xml", "html"]
    priority: Literal[1, 2, 3]
    exams: list[Literal["PSTAR", "PPAER", "FLIGHT_TEST"]]
    licence: str
    section_prefix: str | None = None
    knowledge_base: bool = True

    @field_validator("publisher")
    @classmethod
    def publisher_not_excluded(cls, value: str) -> str:
        """Reject publishers excluded by decision (see docs/RESEARCH.md)."""
        if value.strip().lower() in EXCLUDED_PUBLISHERS:
            raise ValueError(f"{value} documents are excluded")
        return value

    @model_validator(mode="after")
    def xml_has_section_prefix(self) -> Source:
        """Regulation sections are cited with a prefix, for example `CAR`."""
        if self.format == "xml" and not self.section_prefix:
            raise ValueError(f"{self.id}: xml sources need a section_prefix")
        return self


def load_sources(path: Path = SOURCES_FILE) -> list[Source]:
    """Load and validate the manifest. Ids must be unique."""
    sources = [Source(**item) for item in yaml.safe_load(path.read_text())]
    ids = [source.id for source in sources]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        raise ValueError(f"duplicate source ids: {sorted(duplicates)}")
    return sources
