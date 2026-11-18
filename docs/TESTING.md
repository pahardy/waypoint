# Testing Approach

Addresses GitHub issue #4. Applies to every phase in
`docs/TECHNICAL_PLAN.md`. Each phase plan in `docs/plans/` has a
"Tests" section that lists its concrete tests.

## Rule

An increment is done only when its tests are written and pass in CI.
Bugs are fixed by first writing a test that reproduces them.

## Layers

| Layer | What it covers | Tools | Runs |
|---|---|---|---|
| Unit | Pure functions: parsing, chunking, scoring, timing, mastery rules | pytest (Python), Vitest (web) | CI, every push |
| API and database | FastAPI endpoints against a real local PostgreSQL with pgvector; migrations | pytest with FastAPI `TestClient`, Supabase local stack | CI, every push |
| Component | React components in isolation | Vitest with React Testing Library | CI, every push |
| End-to-end | Main user flows in a real browser | Playwright | CI, from phase 3 onward |
| LLM evals | Answer quality, citations, grading consistency with real models | Eval scripts in `api/evals/` and `ingest/eval/` | On demand, and before changing a model or prompt |

## LLM-dependent code

- CI never calls a real LLM or embedding API.
- Unit and API tests use a stub client that returns fixed responses,
  injected through the same small client modules that wrap the
  provider SDKs (`api/llm.py`, `ingest/embeddings.py`).
- Stubs let us test the code around the model: prompt assembly,
  citation parsing, refusals, timeouts and malformed responses.
- Quality is measured separately by the eval sets. Each eval run
  records the model id, prompt version, date and scores in
  `docs/evals/` so results can be compared over time.

## Test data

- Tests use small fixture files in `tests/fixtures/` that we write
  ourselves, for example a two-page PDF and a short regulation XML
  excerpt. They are committed.
- Real acquired documents in `data/` are never needed for CI.
- API tests run against a freshly migrated database, and each test
  rolls back its transaction.

## CI

GitHub Actions on every push and pull request:
1. ruff (lint and format check) and pytest for `api/` and `ingest/`
2. ESLint, TypeScript check, Vitest and `next build` for `web/`
3. Migrations applied to an empty database
4. Playwright, once phase 3 adds the first page with data

## Coverage

There is no coverage percentage target. Every deterministic rule
(scoring, timing, pass marks, mastery) must have tests for its
boundaries, for example a score of exactly 60%, one second over the
time limit, and an empty attempt.
