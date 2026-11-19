"""Source manifest: the documents Waypoint acquires."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, HttpUrl, field_validator, model_validator

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCES_FILE = REPO_ROOT / "ingest" / "sources.yaml"
EXCLUDED_PUBLISHERS = {"nav canada"}

Subject = Literal["air-law", "navigation", "meteorology", "aeronautics", "flight-test"]


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
    columns: Literal[1, 2] = 1
    subjects: dict[str, Subject] = {}

    def subject_for(self, section_ref: str) -> Subject | None:
        """The subject of a section: the longest `subjects` key that is the
        section reference or a whole leading part of it (`COM 4` matches
        `COM 4.5` but not `COM 10.1`), else the `*` default, else None."""
        matches = [
            key
            for key in self.subjects
            if section_ref == key or section_ref.startswith((f"{key} ", f"{key}."))
        ]
        if matches:
            return self.subjects[max(matches, key=len)]
        return self.subjects.get("*")

    @field_validator("publisher")
    @classmethod
    def publisher_not_excluded(cls, value: str) -> str:
        """Reject publishers excluded by decision (see docs/RESEARCH.md)."""
        if value.strip().lower() in EXCLUDED_PUBLISHERS:
            raise ValueError(f"{value} documents are excluded")
        return value

    @model_validator(mode="after")
    def has_section_prefix(self) -> Source:
        """XML and HTML sections are cited with a prefix, for example `CAR`."""
        if self.format in ("xml", "html") and not self.section_prefix:
            raise ValueError(f"{self.id}: {self.format} sources need a section_prefix")
        return self


def load_sources(path: Path = SOURCES_FILE) -> list[Source]:
    """Load and validate the manifest. Ids must be unique."""
    sources = [Source(**item) for item in yaml.safe_load(path.read_text())]
    ids = [source.id for source in sources]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        raise ValueError(f"duplicate source ids: {sorted(duplicates)}")
    return sources
