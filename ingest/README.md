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
uv run ingest eval               # score retrieval; report to docs/evals/
uv run ingest eval --jurisdiction CA  # search Canadian sources only
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
- `chunk` splits a source into sections, then into chunks that stay
  within one section and are at most 800 tokens. Each carries its section
  reference, heading path, page and edition.
  - PDFs with numbered section bookmarks: one section per bookmark
    (`RAC 4.5.8.3`). Bookmarks whose heading is not found are reported.
  - Other PDFs: one section per page (`TP 12880 p.7`). Set `columns: 2`
    for two-column pages, which are then read in the PDF's block order.
  - Justice Laws XML: one section per numbered section (`CAR 602.14`).
  - Web pages: one section per h2 to h4 heading, cited by heading path
    (`STD 421 Division I - General / 421.05 Recency Requirements`).
  The manifest's `section_prefix` names the prefix for all but the first.
- `knowledge_base: false` in the manifest keeps a source out of the
  retrieval index (question banks, answer keys); `load` refuses it.
- `load` embeds each chunk with its heading path, and only embeds chunks
  that are new or changed (or were embedded with another model).
  Re-running it costs nothing and creates no duplicates.
- `eval` runs the questions in `eval/retrieval.yaml` and reports recall@5
  and MRR@10, overall and by subject, with every miss. Each question lists
  the sections (`source:section`) that answer it, confirmed by reading the
  source. When a source is loaded, judge its chunks that reach a
  question's top 5 and add those that state the answer (pooling). FAA
  pages count only for facts that are not Canada-specific.
