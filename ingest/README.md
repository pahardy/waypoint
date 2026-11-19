# Waypoint Ingest

Acquires source documents, extracts the curriculum, and splits sources into
citable chunks.

```
uv run ingest fetch              # download sources.yaml into data/raw/ (git-ignored)
uv run ingest fetch --priority 1 # only priority 1 sources
uv run ingest objectives         # write db/seed/objectives.yaml from the study guides
uv run ingest chunk tc-aim       # write data/text/ and data/chunks/ for one source
uv run pytest
```

- `sources.yaml`: the document manifest (metadata only).
- `fetch` never overwrites a downloaded file. A different upstream copy is
  reported as `changed` for review.
- `objectives` reports anything that needs checking, such as numbering gaps
  in the source guides.
- `chunk` uses the PDF's bookmarks as the section list. Each chunk stays
  within one section, is at most 800 tokens, and carries its section
  reference (for example `RAC 4.5.8.3`), heading path, page and edition.
  Bookmarks whose heading is not found in the text are reported.
