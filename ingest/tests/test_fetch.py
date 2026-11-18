import hashlib
import json
from datetime import date

import httpx

from waypoint_ingest.fetch import fetch_source
from waypoint_ingest.sources import Source

SOURCE = Source(
    id="doc",
    title="A document",
    publisher="Transport Canada",
    edition="First",
    published="2025-01",
    url="https://example.gc.ca/doc.pdf",
    jurisdiction="CA",
    format="pdf",
    priority=1,
    exams=["PPAER"],
    licence="TC",
)


def client_returning(status: int, content: bytes = b"") -> httpx.Client:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(status, content=content)
    )
    return httpx.Client(transport=transport)


def test_download_writes_file_and_metadata(tmp_path):
    status = fetch_source(SOURCE, client_returning(200, b"%PDF-1"), tmp_path)

    assert status == "downloaded"
    assert (tmp_path / "doc" / "doc.pdf").read_bytes() == b"%PDF-1"
    meta = json.loads((tmp_path / "doc" / "meta.json").read_text())
    assert meta["sha256"] == hashlib.sha256(b"%PDF-1").hexdigest()
    assert meta["retrieved_on"] == date.today().isoformat()
    assert meta["url"] == "https://example.gc.ca/doc.pdf"


def test_same_content_is_unchanged(tmp_path):
    fetch_source(SOURCE, client_returning(200, b"v1"), tmp_path)
    assert fetch_source(SOURCE, client_returning(200, b"v1"), tmp_path) == "unchanged"


def test_changed_upstream_keeps_previous_copy(tmp_path):
    fetch_source(SOURCE, client_returning(200, b"v1"), tmp_path)

    status = fetch_source(SOURCE, client_returning(200, b"v2"), tmp_path)

    assert status == "changed"
    assert (tmp_path / "doc" / "doc.pdf").read_bytes() == b"v1"


def test_http_error_fails_without_writing(tmp_path):
    assert fetch_source(SOURCE, client_returning(404), tmp_path) == "failed"
    assert not (tmp_path / "doc").exists()


def test_network_error_fails(tmp_path):
    def refuse(request):
        raise httpx.ConnectError("refused")

    client = httpx.Client(transport=httpx.MockTransport(refuse))
    assert fetch_source(SOURCE, client, tmp_path) == "failed"
