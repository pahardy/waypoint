# Waypoint Ingest

Acquires source documents, extracts the curriculum, and splits sources into
citable chunks.

```
uv run ingest fetch              # download sources.yaml into data/raw/ (git-ignored)
uv run ingest fetch --priority 1 # only priority 1 sources
uv run ingest objectives         # write db/seed/objectives.yaml from the study guides
uv run ingest chunk tc-aim       # write data/text/ and data/chunks/ for one source
uv run ingest load tc-aim        # embed new or changed chunks into the database
uv run ingest search "question"  # show the nearest chunks
uv run pytest                    # needs DATABASE_URL
```

`load` and `search` need `DATABASE_URL` and `VOYAGE_API_KEY` (see
`.env.example`). Embeddings use `voyage-4-large` at 1,024 dimensions
(`docs/EMBEDDINGS.md`). The Voyage account needs a payment method on
file, or its rate limits are too low for a load; the free tokens still
apply. Behind a TLS-inspecting proxy, also set `SSL_CERT_FILE` and
`REQUESTS_CA_BUNDLE` to a CA bundle that includes the proxy's
certificate.

- `sources.yaml`: the document manifest (metadata only).
- `fetch` never overwrites a downloaded file. A different upstream copy is
  reported as `changed` for review.
- `objectives` reports anything that needs checking, such as numbering gaps
  in the source guides.
- `chunk` uses the PDF's bookmarks as the section list. Each chunk stays
  within one section, is at most 800 tokens, and carries its section
  reference (for example `RAC 4.5.8.3`), heading path, page and edition.
  Bookmarks whose heading is not found in the text are reported.
- `load` embeds each chunk with its heading path, and only embeds chunks
  that are new or changed (or were embedded with another model).
  Re-running it costs nothing and creates no duplicates.
