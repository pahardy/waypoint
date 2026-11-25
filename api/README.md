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

Exam rules live in `exams.py` and are deterministic code. Submitting an
attempt also adds its items to `objective_mastery` (correct and seen per
objective; an unanswered item is seen and wrong); see `progress.py`.

- `GET /progress/{PSTAR|PPAER}`: correct, seen and percent per subject,
  and the weak objectives (seen at least 5 times, below the pass mark),
  lowest first, each with a reason giving the numbers.

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

```
uv run oral static-port < answer.txt   # or type the answer, then Ctrl-D
```

Oral exercises live in `content/exercises/` (prompt, sources, weighted
rubric). The model marks each criterion met, partly met or not met with a
quote from the answer; code checks the quotes and calculates the score.

```
uv run oral-eval                # 10 answers in eval/oral.yaml, 3 reps; resumes; about $0.25
uv run oral-eval --variant v1   # a new results directory, to compare with baseline
```

Measures grading consistency and agreement with expected marks; results
and `report.md` go to `.claude/hillclimb/oral/<variant>/` (default `baseline`).

```
uv run scenario deteriorating-weather < answers.txt   # answers separated by ---
```

A scenario has stages; each reveals facts (synthetic weather) and asks a
question graded on its own rubric. Stages advance in code; the overall
score is the mean of the stage scores.

- `GET /exercises`: oral exercises and scenarios (`kind`).
- `POST /sessions` `{exercise_id}`: start a session. `GET /sessions/{id}`:
  revealed facts, current stage, graded stages and, once finished, the
  overall score. `POST /sessions/{id}/answers` `{answer}`: grade the
  current stage and advance; 409 once finished, 502 with nothing stored
  if grading fails. An oral exercise is a one-stage session.

```
uv run check-exercises             # all; or name exercise ids
```

Checks every file in `content/exercises/`: it loads, its sources are in
the knowledge base, and the Opus judge finds every key point supported by
the cited passages. Run it after writing or changing an exercise.

`uv run python tests/stub_server.py` serves the API with a stub model and
stub retrieval, for the web end-to-end tests (run `uv run seed` first).
