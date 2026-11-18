"""Download manifest sources into data/raw/<id>/ with recorded metadata."""

import hashlib
import json
import logging
from datetime import date
from pathlib import Path
from typing import Literal

import httpx

from waypoint_ingest.sources import REPO_ROOT, Source

RAW_DIR = REPO_ROOT / "data" / "raw"
USER_AGENT = "Waypoint/0.1 (non-commercial study project)"

Status = Literal["downloaded", "unchanged", "changed", "failed"]
log = logging.getLogger(__name__)


def fetch_source(source: Source, client: httpx.Client, raw_dir: Path) -> Status:
    """Download one source.

    A source already on disk is never overwritten: if the upstream copy has
    a different hash it is reported as "changed" so a person can review the
    new edition.
    """
    target_dir = raw_dir / source.id
    meta_path = target_dir / "meta.json"
    try:
        response = client.get(str(source.url))
        response.raise_for_status()
    except httpx.HTTPError as error:
        log.error("%s: download failed: %s", source.id, error)
        return "failed"

    sha256 = hashlib.sha256(response.content).hexdigest()
    if meta_path.exists():
        previous = json.loads(meta_path.read_text())
        if previous["sha256"] == sha256:
            return "unchanged"
        log.warning("%s: upstream changed, kept previous copy", source.id)
        return "changed"

    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{source.id}.{source.format}"
    (target_dir / filename).write_bytes(response.content)
    meta = {
        "id": source.id,
        "url": str(source.url),
        "filename": filename,
        "sha256": sha256,
        "bytes": len(response.content),
        "retrieved_on": date.today().isoformat(),
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    return "downloaded"


def fetch_all(sources: list[Source], raw_dir: Path = RAW_DIR) -> dict[str, Status]:
    """Download every source, continuing past failures."""
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(headers=headers, follow_redirects=True, timeout=120) as client:
        return {s.id: fetch_source(s, client, raw_dir) for s in sources}
