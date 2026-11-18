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

## Done when

- Scoring and timing are covered by unit tests.
- At least 25 reviewed questions per PPAER subject.
- All generated questions are labelled as practice questions, never
  official.

## Review gate

A Canadian flight instructor reviews a sample of questions before
phase 5 starts (spec MVP step 7).
