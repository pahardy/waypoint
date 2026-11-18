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

## Project documents

- `CLAUDE.md` -- product specification and development sequence
- `docs/RESEARCH_PLAN.md` -- plan for identifying knowledge-base sources
- `docs/RESEARCH.md` -- source research results and decisions
- `docs/TECHNICAL_PLAN.md` -- architecture and phased development plan
  (phase details in `docs/plans/`)
- `docs/TESTING.md` -- testing approach (per-phase tests in each plan)
- `docs/BRANDING.md` -- brand, look and feel

## Running locally

Requires Docker, [uv](https://docs.astral.sh/uv/) and Node.js 24.

```
docker compose up -d                       # PostgreSQL + pgvector on :5432

cd api
cp .env.example .env
export $(cat .env)
uv run migrate
uv run fastapi dev src/waypoint_api/main.py   # http://localhost:8000

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

## Status

Phase 0 (project skeleton) and phase 1 (document acquisition and
curriculum) in place. See `docs/TECHNICAL_PLAN.md`.
