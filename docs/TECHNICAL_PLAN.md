# Technical Plan

Addresses GitHub issue #3. This document gives the overall plan. Each
phase has its own document in `docs/plans/`.

Inputs: `CLAUDE.md` (product specification) and `docs/RESEARCH.md`
(sources and decisions).

## Constraints

- **Non-commercial test project.** Keep it simple and cheap to run.
- **Sources:** Transport Canada and other federal government documents
  only. No NAV CANADA documents and no commercial textbooks.
- **Public repository.** Acquired documents and derived chunks never go
  into git. They live in a git-ignored `data/` directory and in the
  database.
- **Deterministic code** handles scoring, exam timing and eligibility
  rules. The LLM is used for explanation, question drafting and rubric
  feedback only.
- **Incremental delivery.** Each phase ends with something that runs
  and is verified before the next phase starts.

## Architecture

```
            Browser
               |
    Next.js frontend (web/)
               |  HTTPS, JSON
    FastAPI backend (api/)
     |        |          |
     |        |      LLM provider
     |        |
     |   PostgreSQL + pgvector (Supabase)
     |     - documents, chunks, embeddings
     |     - curriculum objectives
     |     - questions, attempts, progress
     |
  Ingestion CLI (ingest/)
     - reads data/raw/, writes chunks + embeddings
```

| Component | Choice | Notes |
|---|---|---|
| Frontend | Next.js (App Router), TypeScript, Tailwind CSS | Current stable versions, pinned at setup |
| Backend | Python, FastAPI, managed with `uv` | One service |
| Database | Supabase PostgreSQL with pgvector | Also provides auth (Supabase Auth) |
| LLM | Evaluated in phase 3. The default candidate is the latest Claude Sonnet model. | Behind one small client module |
| Embeddings | Evaluated in phase 2 | Behind the same kind of module |
| Ingestion | Python CLI in the same `uv` workspace | Run locally |
| Hosting | Local first. A hosted deployment is optional and decided after phase 3. | |

## Repository layout

```
api/          FastAPI app
ingest/       document acquisition and ingestion CLI
web/          Next.js app
db/           SQL migrations
data/         git-ignored: raw documents, extracted text
docs/         plans and decisions
```

## Phases

| # | Phase | Plan | Delivers | Spec MVP step |
|---|---|---|---|---|
| 0 | Project skeleton | This document, section below | Repo layout, tooling, CI lint and test, empty API and web app talking to each other | — |
| 1 | Document acquisition | [plans/01-document-acquisition.md](plans/01-document-acquisition.md) | Source manifest, downloaded documents, curriculum objectives from TP 11919 and TP 12880 | 1 |
| 2 | Ingestion and retrieval | [plans/02-ingestion-retrieval.md](plans/02-ingestion-retrieval.md) | Chunked, embedded, citable knowledge base and a measured retrieval quality | 2 |
| 3 | AI instructor | [plans/03-ai-instructor.md](plans/03-ai-instructor.md) | Grounded chat with citations | 3 |
| 4 | Practice assessments | [plans/04-practice-assessments.md](plans/04-practice-assessments.md) | Question bank, quizzes, timed mock exams, scoring | 4 |
| 5 | Oral and scenario exercises | [plans/05-oral-scenarios.md](plans/05-oral-scenarios.md) | Rubric-based oral questioning and scenarios | 5 |
| 6 | Progress tracking | [plans/06-progress-tracking.md](plans/06-progress-tracking.md) | Student records, weak areas, study recommendations | 6 |
| 7 | Web application | [plans/07-web-application.md](plans/07-web-application.md) | The site itself, built up alongside phases 3–6 | — |

Phase 7 is not a separate step at the end. Each of phases 3–6 adds
its own pages, following `docs/BRANDING.md`. Plan 07 holds the shared
site structure, design system and accounts.

The spec's MVP step 7, validation with aviation professionals, is a
review gate at the end of phases 4 and 5. It is not a build phase.

## Phase 0: project skeleton

Steps, each verified before the next:
1. Create the directory layout and a root `.gitignore` that covers
   `data/`, `.env` files and build output.
2. Set up `api/` with `uv init`, FastAPI and a `GET /health` endpoint,
   with a pytest test for it.
3. Set up `web/` with `create-next-app` (TypeScript, Tailwind, App
   Router), and a home page that calls `/health`.
4. Set up a local Supabase stack with the Supabase CLI and enable
   pgvector in the first migration in `db/`.
5. Add GitHub Actions to run ruff and pytest for `api/` and `ingest/`,
   and lint and build for `web/`.

Done when a fresh clone can run the API, the web app and the database
locally from README instructions, and CI is green.

### Tests

The testing approach is in `docs/TESTING.md`.
- `GET /health` returns 200 (pytest, `TestClient`).
- The migration test applies all of `db/` to an empty database and
  checks that the `vector` extension exists.
- The home page renders (Vitest), and `next build` succeeds.
- `git check-ignore data/x .env` succeeds, so documents and secrets
  cannot be committed by accident.
- CI runs all of the above on every push. A deliberately failing test
  is pushed once on a branch to confirm that CI catches it.

## Cross-cutting rules

- **Citations:** every regulatory or technical answer cites a chunk
  that carries its document, edition and section.
- **Jurisdiction:** every chunk is tagged `CA` or `non-CA`. FAA
  material is never cited for Canadian rules.
- **Disclaimers:** state on every page that Waypoint is an educational
  aid and not an operational authority.
- **Secrets:** API keys live in `.env` files that are never committed.
- **Tests:** see `docs/TESTING.md`. Each phase plan has a "Tests"
  section.
