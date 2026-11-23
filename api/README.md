# Waypoint API

FastAPI backend.

```
uv run migrate                                # apply db/migrations
uv run seed                                   # load objectives and PSTAR questions
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

- `POST /chat`: the instructor. Body: `level` (`PSTAR`, `PPAER`,
  `FLIGHT_TEST`), `messages` (the conversation so far, `{role, content}`,
  ending with the student's) and optional `conversation_id`. A follow-up is
  rewritten into a standalone search query using the conversation. Streams
  JSON Lines: `delta` events with the answer text, then `done` with the
  citations (document, edition, section, page, passage text) and the
  `conversation_id`. A model error, timeout or refusal ends the stream with
  `error` instead; text already sent is then incomplete and nothing is saved.
- `GET /conversations/{id}`: a saved conversation.

```
curl -N -X POST localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"level": "PSTAR", "messages": [{"role": "user", "content": "How long after drinking can I fly?"}]}'
```

- `GET /exams/{PSTAR|PPAER}`: the exam rules (50 questions, 90% pass mark, a
  90-minute limit listed in `unverified`), whether it has a mock exam and
  the topics to quiz on.
- `POST /attempts`: start a `quiz` (10 questions, untimed, optional
  `objective_id`) or a `mock` exam (50 questions drawn from each TP 11919
  section in proportion to its size, timed). Correct answers are never
  sent before submission.
- `POST /attempts/{id}/answers`: `{position, chosen_index}`. Refused with
  409 after submission or after the time limit (server clock).
- `POST /attempts/{id}/submit`, `GET /attempts/{id}/results`: the score,
  the outcome (`pass`, `partial`, `fail`), per-subject and per-topic
  breakdowns and each question with its answer, its explanation and cited
  passage (practice questions) or its TP 11919 references (PSTAR). A PPAER mock with a
  subject under 60% is a partial pass and names the supplementary exam.

Exam rules live in `exams.py` and are deterministic code.

```
uv run draft-questions --subject navigation --count 25   # about $1 per 20; both API keys
```

Drafts PPAER practice questions until the subject has `count` in
`db/seed/ppaer-questions.yaml`, one per essential objective (evenly spaced
first). Sources are the CAR section an objective names, or else the nearest
Canadian passages plus a little FAA background, usable only for facts that
are the same everywhere. The Opus judge answers each draft from its cited
section alone; only drafts it agrees with, without FAA rules presented as
Canadian, are kept, as `status: draft`. Review each (`reviewed` or
`retired`); only reviewed questions are used. Choices are shuffled in code.
Model calls use server-side fallback, and a refusal is reported as one.

`uv run python tests/stub_server.py` serves the API with a stub model and
stub retrieval, for the web end-to-end tests (run `uv run seed` first).
