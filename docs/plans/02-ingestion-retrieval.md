# Phase 2: Ingestion and Retrieval

Goal: turn the raw documents into citable chunks with embeddings, and
measure how well retrieval finds the right passage.

Spec MVP step 2: "Build the knowledge base."

## Pipeline

```
data/raw/<id>  ->  extract  ->  normalize  ->  chunk  ->  embed  ->  database
```

1. **Extract:** pull text out of each format. PDFs use a PDF text
   library; the regulations come from the Justice Laws XML; web pages
   are parsed from HTML. The extracted text is saved to
   `data/text/<id>.jsonl`, one record per section.
2. **Normalize:** remove headers, footers and page numbers, fix
   hyphenation, and keep the section numbers and headings.
3. **Chunk:** split along section boundaries first, then by size
   (about 300–800 tokens). Each chunk carries its heading path.
4. **Embed:** call the embedding model through `ingest/embeddings.py`.
5. **Load:** write the documents and chunks to the database.

## Data model

```
document(id, source_id, title, publisher, tp_number, edition,
         published_on, retrieved_on, jurisdiction, url, sha256)
chunk(id, document_id, section_ref, heading_path, page,
      text, token_count, embedding vector)
objective(id, exam, subject, topic, text, source_ref)
chunk_objective(chunk_id, objective_id)
```

## Retrieval

- Hybrid search: pgvector similarity plus PostgreSQL full-text
  search, merged with reciprocal rank fusion.
- Optional filters: exam, subject and jurisdiction.
- Returns chunks with everything a citation needs.
- Exposed as `POST /retrieve` in the API.

## Evaluation

- **Eval set:** about 60 questions, written by hand, spread across
  PSTAR and the four PPAER subjects, each with its expected section
  reference. Stored as `ingest/eval/retrieval.yaml`.
- **Metrics:** recall@5 and MRR.
- **Embedding choice:** compare 2–3 embedding models on the eval set.
  Pick the best one that is affordable.

## Tests

Unit (CI), using fixture files in `tests/fixtures/`:
- PDF extraction of a two-page fixture keeps headings and section
  numbers, and records the page.
- XML extraction of a regulation excerpt produces one record per
  section with the correct reference, for example `602.14(2)(a)`.
- Normalization removes repeated headers, footers and page numbers,
  and rejoins hyphenated words.
- Chunking never crosses a section boundary, keeps every chunk within
  the size limits, and keeps the heading path.
- Every chunk carries the fields needed for a citation: document id,
  edition and section reference.
- Jurisdiction tags: chunks from an FAA document are `non-CA`.

API and database (CI, stub embeddings that return fixed vectors):
- Loading the fixtures writes the expected documents and chunks, and
  re-running the load does not create duplicates.
- `POST /retrieve` returns chunks ordered by score, respects the exam,
  subject and jurisdiction filters, and returns an empty list (not an
  error) when nothing matches.
- Hybrid search: a query that matches a chunk only by keyword is still
  returned.

Eval (on demand, real embeddings):
- Retrieval eval set: recall@5 and MRR, recorded in `docs/evals/`.

## Steps

1. Ingest only the TC AIM. Inspect the chunks by hand.
2. Add the embedding call and the database load. Query them manually.
3. Build the eval set and the evaluation script, and record a baseline.
4. Add the regulations (XML) and the PPAER guide. Re-run the
   evaluation.
5. Add hybrid search. Re-run the evaluation and keep it only if it
   improves the scores.
6. Ingest the remaining sources.

## Progress

Step 1 (TC AIM 2026-2), done:
- Sections come from the PDF bookmarks. All 1,452 numbered headings are
  found on their bookmark page, and each matches its bookmark title.
- 1,477 chunks from 1,275 sections with text (the other 177 are parent
  headings with no text of their own). Median 206 tokens, max 800.
- Many sections are short, so many chunks are under 300 tokens. They are
  kept, because chunks never cross a section boundary.
- Line-end hyphens in the AIM are real compound hyphens
  (`radio-equipped`), so they are kept when lines are joined.
- Known limits: tables come out as row text, and a table spanning both
  columns is read column by column. Token counts are an estimate (words
  and punctuation) until the embedding model is chosen in step 2.

Step 2 (embeddings and database load), done:
- Model: `voyage-4-large`, 1,024 dimensions (issue #9,
  `docs/EMBEDDINGS.md`). Documents use input type `document` and are
  embedded with their heading path; questions use `query`.
- Tables `document` and `chunk` (migration 0002) with an HNSW cosine
  index. Each chunk records the model that embedded it.
- `ingest load` embeds only new or changed chunks. `ingest search`
  queries by hand.
- Measured with Voyage's tokenizer: the TC AIM is about 0.50 million
  tokens (about USD 0.06, inside the free allowance). The estimate
  undercounts: the median real-to-estimate ratio is 1.35, and the
  largest chunk is 1,796 real tokens. Embedding is unaffected (32,000
  token context). Consider switching the chunker to the real tokenizer
  after the baseline eval.
- All 1,477 TC AIM chunks loaded in about 20 seconds. Re-running embeds
  nothing.
- Manual check: five student questions (icing reports, VFR cruising
  altitudes, wake turbulence, mandatory frequency procedures, METAR and
  SPECI) each returned the matching AIM section first. The step 3 eval
  set will measure this properly.

## Done when

- All acquired sources are ingested, and chunks link back to section
  references.
- recall@5 is at least 0.8 on the eval set. The target will be
  adjusted after the baseline.
- `POST /retrieve` is covered by tests.
