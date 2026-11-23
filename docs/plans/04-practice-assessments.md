# Phase 4: Practice Assessments

Goal: topic quizzes and timed mock exams with deterministic scoring and
per-subject results.

Spec MVP step 4.

## Question bank

- **PSTAR:** the official questions from TP 11919, imported as written
  and marked `official`.
- **PPAER and flight test:** questions drafted by the LLM from chunks
  and objectives, then reviewed by a person before they are published.
  They are marked `practice`.
- Every question records its objective, source chunk, explanation,
  status (`draft`, `reviewed` or `retired`) and origin (`official` or
  `generated`).

```
question(id, exam, subject, objective_id, stem, choices jsonb,
         answer_index, explanation, source_chunk_id, origin, status)
attempt(id, user_id, kind, exam, started_at, submitted_at,
        time_limit_s, score, subject_scores jsonb)
attempt_item(attempt_id, question_id, chosen_index, correct)
```

## Exam rules (deterministic code)

- Configured in `api/exams.py`: question count, time limit, overall
  pass mark and per-subject pass mark.
- Values come from the confirmed facts in `RESEARCH.md`. Until those
  are confirmed, the UI shows them as "unverified".
- The timer is enforced on the server: answers after the time limit
  are not scored.
- PPAER result is pass, partial pass or fail, following TP 12880.

## Tests

Unit (CI):
- Scoring: all correct, none correct, exactly at the pass mark, and
  just below the pass mark.
- PPAER result: pass, partial pass (60% overall but under 60% in one
  subject) and fail.
- Timing: an answer submitted one second before the limit is scored,
  and one second after is not. An attempt with no answers scores 0.
- Mock exam assembly: the right question count and subject mix, no
  duplicates, and only `reviewed` questions.
- PSTAR import: the question count matches TP 11919, and every
  question has exactly one correct answer.
- Question validation: rejects questions without an objective, a
  source chunk or an explanation.

API and database (CI):
- Start an attempt, answer, submit, and fetch the results. The results
  match the unit-level scoring.
- A user cannot read or submit another user's attempt.
- Generated questions are always returned with origin `generated` and
  shown as practice questions.

Component and end-to-end (CI):
- The timer counts down and the exam auto-submits at zero (with the
  clock mocked).
- Complete a 10-question quiz and see the results page with a
  per-subject breakdown.

Eval (on demand, real model):
- Question drafting: a sample of drafted questions is checked for
  answerability from the cited chunk before human review.

## Steps

1. Import the PSTAR questions. Build a 10-question topic quiz with
   scoring and tests.
2. Build the timed PSTAR mock exam (50 questions).
3. Write the question-drafting script and the review flow: a review
   page or a YAML file review. Draft 20 Air Law questions and review
   them.
4. Expand to all four PPAER subjects. Build the PPAER mock exam with
   per-subject scoring.
5. Results page: per-subject breakdown and a review of each question
   with its explanation and source.

## Progress

Steps 1 and 2 (PSTAR quiz and mock exam), done (issue #18):
- `uv run ingest pstar-questions` parses TP 11919 (7th ed.) and its
  answer key into `db/seed/pstar-questions.yaml`: 185 questions. The
  guide has 186 numbers, but 7.07 is "Intentionally removed" (the key
  still lists an answer). Table questions read "in flight: ... on the
  ground: ...". `uv run seed` loads objectives and questions as
  `official`, `reviewed`.
- Exam rules (`api/exams.py`): 50 questions and a 90% pass mark from
  TP 11919. TC publishes no time limit; 90 minutes comes from a third
  party and is shown as unverified. Owner decision, 2026-11-23.
- Mock selection: each section in proportion to its size (largest
  remainder), labelled as Waypoint's rule, not TC's. Owner decision,
  2026-11-23.
- Quizzes: 10 questions, untimed, one section or all.
- The server clock times attempts. Answers after the deadline are
  refused (409); the page submits when its timer reaches zero.
- Pages: `/practice`, `/practice/[attemptId]`, `/results/[attemptId]`
  (score, pass mark, per-topic table, each question with its answer).
- No accounts yet: attempts are reached by an unguessable id, so the
  "another user's attempt" test waits for accounts (phase 6).
- The light theme's amber failed contrast with Night text (3.5:1).
  Buttons and the OFFICIAL badge now use `--on-accent` (white in light).

Step 3 (drafting and review), issue #20:
- `uv run draft-questions` drafts with Claude Sonnet 5.5 from the CAR
  section an objective names (or the nearest TC AIM passages) and checks
  each draft with Claude Opus 5.5, which answers it from the cited
  section alone. Validation (objective, source chunk, explanation, four
  distinct choices) is in `GeneratedQuestion`, used by drafting and seed.
- Review is a YAML file: `db/seed/ppaer-questions.yaml`, reviewed in the
  PR. The 20 Air Law questions come from every third essential objective.
  Owner decision, 2026-11-23: choose the simplest option.
- First run found two problems, both fixed in code: a long CAR section is
  split into chunks with one label, so the check saw the wrong chunk (CAR
  401.05); and the model put 10 of 20 answers first and none last, so
  choices are now shuffled, seeded by question id.
- After the fixes the judge agrees with all 20 answers. For the reviewer:
  089 has a negative stem ("NOT required"), and the correct choice is the
  longest in 8 of 20.
- All 20 marked `reviewed` without a question-by-question read: owner
  decision, 2026-11-23, since Waypoint is a test app. They still need the
  flight-instructor review gate below.
- PPAER quizzes are available (Air Law only). The PPAER mock exam waits
  for step 4. Generated questions show the PRACTICE badge.

## Done when

- Scoring and timing are covered by unit tests.
- At least 25 reviewed questions per PPAER subject.
- All generated questions are labelled as practice questions, never
  official.

## Review gate

A Canadian flight instructor reviews a sample of questions before
phase 5 starts (spec MVP step 7).
