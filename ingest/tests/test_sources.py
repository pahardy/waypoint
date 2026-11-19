import pytest
import yaml
from pydantic import ValidationError

from waypoint_ingest.sources import load_sources

VALID = {
    "id": "doc",
    "title": "A document",
    "publisher": "Transport Canada",
    "edition": "First",
    "published": "2025-01",
    "url": "https://example.gc.ca/doc.pdf",
    "jurisdiction": "CA",
    "format": "pdf",
    "priority": 1,
    "exams": ["PPAER"],
    "licence": "TC",
}


def write_manifest(tmp_path, items):
    path = tmp_path / "sources.yaml"
    path.write_text(yaml.safe_dump(items))
    return path


def test_repository_manifest_is_valid():
    sources = load_sources()
    assert {"tp11919", "tp12880", "tp13723", "tc-aim", "cars"} <= {
        s.id for s in sources
    }


def test_missing_field_is_rejected(tmp_path):
    item = {k: v for k, v in VALID.items() if k != "url"}
    with pytest.raises(ValidationError):
        load_sources(write_manifest(tmp_path, [item]))


def test_duplicate_ids_are_rejected(tmp_path):
    with pytest.raises(ValueError, match="duplicate"):
        load_sources(write_manifest(tmp_path, [VALID, VALID]))


@pytest.mark.parametrize("publisher", ["NAV CANADA", "Nav Canada"])
def test_nav_canada_is_rejected(tmp_path, publisher):
    with pytest.raises(ValidationError, match="excluded"):
        load_sources(write_manifest(tmp_path, [{**VALID, "publisher": publisher}]))


def test_question_banks_are_kept_out_of_the_knowledge_base():
    excluded = {s.id for s in load_sources() if not s.knowledge_base}
    assert excluded == {"tp11919", "tp11919-answers", "tp13014"}
