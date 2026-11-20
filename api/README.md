# Waypoint API

FastAPI backend.

```
uv run fastapi dev src/waypoint_api/main.py   # http://localhost:8000
uv run pytest                                 # needs DATABASE_URL
uv run ruff check . && uv run ruff format --check .
```

Needs `DATABASE_URL`, `VOYAGE_API_KEY` for `/retrieve`, and
`ANTHROPIC_API_KEY` for the instructor (see `.env.example`).

```
uv run instructor "How long after drinking alcohol can I fly?" --level PSTAR
```

The instructor answers from retrieved passages and cites them as
`[TC AIM AIR 3.9]` or `[CAR 602.03]`; references to passages it was not
given are flagged. `WAYPOINT_LLM_MODEL` (default `claude-sonnet-5-5`) and
`WAYPOINT_LLM_EFFORT` (default `low`) select the model.

```
uv run instructor-eval                      # all cases; resumes if interrupted
uv run instructor-eval --cases id1,id2      # a subset
uv run instructor-eval --variant v1 --reps 3
```

The eval (`eval/instructor.yaml`) grades each answer with code checks and
a Claude Opus 5.5 judge, and writes results to
`.claude/hillclimb/instructor/<variant>/`. One full run costs about $3.

- `GET /health`: liveness check.
- `POST /retrieve`: knowledge-base passages that best answer a question,
  with their citations. Body: `question`, optional `limit` (1 to 20,
  default 5), `exam` (`PSTAR`, `PPAER`, `FLIGHT_TEST`), `subject`
  (`air-law`, `navigation`, `meteorology`, `aeronautics`, `flight-test`)
  and `jurisdiction` (`CA`, `non-CA`). Use `jurisdiction: CA` for
  Canadian rules; FAA material is `non-CA`.

```
curl -X POST localhost:8000/retrieve -H 'Content-Type: application/json' \
  -d '{"question": "What are the VFR fuel requirements?", "jurisdiction": "CA"}'
```
