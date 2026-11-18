# Waypoint Ingest

Acquires source documents and extracts the curriculum.

```
uv run ingest fetch              # download sources.yaml into data/raw/ (git-ignored)
uv run ingest fetch --priority 1 # only priority 1 sources
uv run ingest objectives         # write db/seed/objectives.yaml from the study guides
uv run pytest
```

- `sources.yaml`: the document manifest (metadata only).
- `fetch` never overwrites a downloaded file. A different upstream copy is
  reported as `changed` for review.
- `objectives` reports anything that needs checking, such as numbering gaps
  in the source guides.
