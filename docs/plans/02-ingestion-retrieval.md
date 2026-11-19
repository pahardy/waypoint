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

Step 3 (eval set and baseline), done (issue #10):
- `ingest/eval/retrieval.yaml`: 65 questions, written in a student's
  words, across PSTAR (13), air law (15), navigation (12), meteorology
  (12) and aeronautics (13). Each expected section was confirmed by
  reading the AIM text, not by searching. The five topics seen during
  the step 2 hand check are left out.
- `uv run ingest eval` writes a report to `docs/evals/`.
- Baseline (`docs/evals/retrieval-2026-11-19-tc-aim.md`), vector search only:
  **recall@5 0.98, MRR@10 0.93**. The one miss (Class G services)
  ranked 7th.
- The baseline is probably optimistic. Only the AIM is loaded; the
  questions were written by someone who had read the sections; and with
  65 questions, one miss moves recall by about 1.5 points. Expect lower
  scores once the CARs and guides compete for the same questions. Their
  sections must then be added to `expected`, or correct answers will
  count as misses.
- Suggested target change: keep recall@5 at or above 0.9 as sources are
  added, and add harder questions (numbers, two-part, scenario wording)
  before comparing search methods in step 5.

Step 4 (CARs and PPAER guide), done (issue #11):
- CARs: `justice_xml.py` reads the Justice Laws XML into one section per
  numbered section (`CAR 602.14`), with the Part, Subpart, Division and
  rule title as heading path. Repealed and reserved provisions, history
  notes and the schedules are left out. 1,543 chunks from 1,496 sections.
- TP 12880 has no bookmarks, so `pages.py` splits it by page
  (`TP 12880 p.7`). 32 chunks.
- Paragraph fixes found on the way: a bold line at least 2 points larger
  than its neighbour now starts its own paragraph, and dot leaders are
  shortened to "...". No word of the AIM changed; only paragraph breaks
  and dot runs did.
- Eval labels: 17 CAR sections were added to existing questions, found
  by keyword search and read before re-running the eval. Seven exam
  questions were written from TP 12880 pages 4 to 9.
- Results (`docs/evals/retrieval-2026-11-19-cars-tc-aim-tp12880.md`):
  **recall@5 0.97, MRR@10 0.92** over 72 questions. The original 65
  scored as before. A CAR ranks first for 11 questions, and loading the
  CARs moved AIM answers down a place but not out of the top 5 (AIM-only
  MRR 0.87).
- New miss: exam-02 ("failed the meteorology part") retrieves weather
  sections instead of the guide's supplementary exam page.
- The guide's topic-list pages (pages 10 to 27) appear in 7 of 325 top-5
  slots for non-exam questions, never first. They add little and could
  be excluded if the instructor finds them unhelpful.

Step 5 (hybrid search), done (issue #12): **not kept**.
- Tried: PostgreSQL full-text search on chunk text and heading path (any
  word of the question may match), merged with vector search by
  reciprocal rank fusion over the top 50 of each.
- Results over the same 72 questions and data (reports in `docs/evals/`):

  | Method | Recall@5 | MRR@10 |
  |---|---|---|
  | Vector only | **0.99** | **0.92** |
  | Keyword only | 0.50 | 0.32 |
  | Keyword only, length-normalized | 0.54 | 0.37 |
  | Hybrid | 0.89 | 0.71 |
  | Hybrid, length-normalized | 0.90 | 0.75 |

- Why it lost: keyword matches favour long chunks that share common
  words ("part", "aircraft", "operate"), and fusion lets them push good
  vector results out of the top 5. Hybrid did find all seven exam
  questions, but missed eight others that vector search finds.
- The code is in the git history (commit "Phase 2 step 5: hybrid search
  experiment") and was then removed. Revisit if the eval later shows
  misses on exact terms such as regulation numbers or abbreviations.
- Run-to-run check: query embeddings are identical across calls, and the
  HNSW index returns the same top 10 as an exact search (checked against
  numpy) for all 72 questions. The step 4 run's exam-02 miss could not be
  reproduced; at about 3,000 chunks the planner now chooses exact search.
  Approximate HNSW search is the likely cause; re-check index and exact
  results as the corpus grows.

Step 6 (remaining sources), done (issue #12):
- Loaded: TP 13723 and TP 975 (split by page); Standards 421 and 428,
  TP 14277 and RIC-21 (`html_sections.py`, split at h2 to h4 and cited
  by heading path); the FAA PHAK (two columns, read in the PDF's block
  order) and Aviation Weather Handbook, tagged `non-CA`. 4,817 chunks in
  all.
- Kept out (`knowledge_base: false` in `sources.yaml`): TP 11919 is a
  bank of PSTAR multiple-choice questions without answers; loading it
  lowered MRR@10 from 0.92 to 0.88 because questions rank above real
  answers. It belongs to phase 4 with its answer key. The answer key and
  TP 13014 (question style only) are also kept out.
- New sources were judged by pooling: unlabelled chunks that reached a
  question's top 5 were read and added to `expected` only if they state
  the answer. FAA pages count only for facts that are not Canada-specific.
  18 FAA pages were added; US rules, products and publications were not.
- Results (`docs/evals/`):

  | Search | Recall@5 | MRR@10 |
  |---|---|---|
  | Canadian sources only | 0.97 | 0.92 |
  | All sources, FAA included | 0.96 | 0.88 |

- FAA pages rank above Canadian answers for many meteorology, navigation
  and aeronautics questions, and for one (winds aloft, true or magnetic)
  US forecast products push the Canadian answer out of the top 10.
  Recommendation for phase 3: search Canadian sources first and use the
  FAA handbooks only as labelled supplementary theory, never for rules.
  `nearest` and `ingest eval` take a jurisdiction filter for this.
- exam-02 now ranks 6th: sections on failing a flight test outrank the
  guide's page on failing part of the written exam.

## Done when

- All acquired sources are ingested, and chunks link back to section
  references.
- recall@5 is at least 0.8 on the eval set. The target will be
  adjusted after the baseline.
- `POST /retrieve` is covered by tests.
