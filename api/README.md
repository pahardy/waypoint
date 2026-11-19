# Waypoint API

FastAPI backend.

```
uv run fastapi dev src/waypoint_api/main.py   # http://localhost:8000
uv run pytest                                 # needs DATABASE_URL
uv run ruff check . && uv run ruff format --check .
```

Needs `DATABASE_URL` and, for `/retrieve`, `VOYAGE_API_KEY` (see
`.env.example`).

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
