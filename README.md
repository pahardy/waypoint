# Waypoint

**Canadian Pilot Training & Exam Preparation**

Waypoint is an AI-powered study companion for people working toward a
Canadian Private Pilot Licence -- Aeroplane (PPL-A). It helps students
prepare for:

- **PSTAR** -- the Student Pilot Permit examination
- **PPAER** -- the PPL-A written examination (Air Law, Navigation,
  Meteorology, Aeronautics -- General Knowledge)
- **The PPL-A flight test** -- its knowledge and procedural components

Planned capabilities include a source-cited knowledge base built from
Transport Canada material, an AI instructor, practice quizzes and mock
exams, scenario-based oral questioning, a flight-test study companion,
and progress tracking.

Waypoint is an educational aid. It does not replace flight instruction,
an authorized flight examiner, current Transport Canada publications, or
a pilot's operational responsibilities.

## Built with Claude

This project is being created with **Claude** (Anthropic's AI model),
using Claude Code. Claude writes code, documentation and research plans
from the project specification and tracked issues.

## How it is built

```
Browser ── Next.js web app (web/)
               │ JSON over HTTPS
           FastAPI backend (api/) ──── LLM provider
               │
           PostgreSQL + pgvector
               ▲
           Ingestion CLI (ingest/) ◄── Transport Canada and other
                                       federal documents (data/, not in git)
```

| Part | Technology |
|---|---|
| Web app | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4 |
| API | Python 3.14, FastAPI, managed with `uv` |
| Database | PostgreSQL 18 with pgvector, run locally with Docker Compose |
| Ingestion | Python CLI: httpx for downloads, PyMuPDF for PDF parsing |
| AI | An LLM for explanation, question drafting and rubric feedback. The latest Claude Sonnet model is the default candidate, chosen by evaluation in phase 3. |
| Tests and CI | pytest, Vitest, Playwright (planned); GitHub Actions on every push |

Design principles:
- **Grounded answers.** Documents are split into chunks that keep their
  edition and section number. The instructor answers from retrieved
  chunks and cites them. FAA material is tagged non-Canadian and never
  cited for Canadian rules.
- **Deterministic rules in code.** Scoring, exam timing, pass marks and
  progress calculations are plain code with tests, never left to the
  LLM.
- **Curriculum from official guides.** Learning objectives are
  extracted from TP 11919 (PSTAR), TP 12880 (PPAER) and TP 13723
  (flight test), and every quiz, exercise and recommendation links back
  to them.
- **Sources stay out of git.** The repository is public, so downloaded
  documents live only in `data/` and the database. No NAV CANADA
  documents or commercial textbooks are used.
- **Small, tested increments.** Each step ends with passing tests in CI.

Build phases:

| Phase | Delivers | Status |
|---|---|---|
| 0 | Project skeleton: API, web app, database, CI | Done |
| 1 | Document acquisition and 650 curriculum objectives | Done |
| 2 | Chunking, embeddings and hybrid search, with measured retrieval quality | In progress |
| 3 | AI instructor with citations | Planned |
| 4 | Practice quizzes and timed mock exams | Planned |
| 5 | Oral questioning and scenario exercises | Planned |
| 6 | Progress tracking and study recommendations | Planned |
| 7 | The website, built alongside phases 3 to 6 | Planned |

## Project documents

- `CLAUDE.md` -- product specification and development sequence
- `docs/RESEARCH_PLAN.md` -- plan for identifying knowledge-base sources
- `docs/RESEARCH.md` -- source research results and decisions
- `docs/TECHNICAL_PLAN.md` -- architecture and phased development plan
  (phase details in `docs/plans/`)
- `docs/EMBEDDINGS.md` -- embedding model candidates for retrieval
- `docs/TESTING.md` -- testing approach (per-phase tests in each plan)
- `docs/BRANDING.md` -- brand, look and feel

## Running locally

Requires Docker, [uv](https://docs.astral.sh/uv/) and Node.js 24.

```
docker compose up -d                       # PostgreSQL + pgvector on :5432
```

In one terminal:

```
cd api
cp .env.example .env
export $(cat .env)
uv run migrate
uv run fastapi dev src/waypoint_api/main.py   # http://localhost:8000
```

In another:

```
cd web
cp .env.example .env.local
npm install
npm run dev                                # http://localhost:3000
```

Source documents and curriculum (downloads about 140 MB into `data/`):

```
cd ingest
uv run ingest fetch
uv run ingest objectives
```

Tests: `uv run pytest` in `api/` and `ingest/` (`api/` needs the database and `DATABASE_URL`),
`npm test` in `web/`. CI runs these on every push.
