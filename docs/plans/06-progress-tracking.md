# Phase 6: Progress Tracking and Personalization

Goal: record what the student has done and recommend what to study
next, in a way the student can understand.

Spec MVP step 6.

## Data

Most of the data already exists from phases 3–5: attempts, attempt
items, exercise sessions and conversations. Phase 6 adds:

```
objective_mastery(user_id, objective_id, correct, seen,
                  last_seen_at, self_confidence)
```

## Mastery rules (deterministic)

- Mastery per objective is a recency-weighted correct rate. Defined in
  `api/progress.py`.
- Weak areas are objectives below a threshold that have been seen at
  least N times, or that the student rated low in confidence.
- Recommendations: the 3–5 weakest objectives in the student's chosen
  exam, each with a reason, for example "4 of 6 wrong in the last
  week", and a link to a quiz or reading.

## Steps

1. Update `objective_mastery` whenever a quiz or exam is submitted.
   Cover this with tests.
2. Dashboard: progress per subject and a list of weak objectives.
3. Recommendations, with their reasons shown.
4. Self-rated confidence per topic.

## Progress

Step 1 (record mastery on submit), issue #42:
- Migration 0010: `objective_mastery(objective_id, correct, seen,
  last_seen_at, self_confidence)`, backfilled from attempts already
  submitted. On the dev database: 134 attempts, 114 objectives, 2,500
  items seen, 259 correct, matching the attempt items exactly.
- `attempts.submit` calls `progress.record` in the same transaction as
  the score; a second submit is still a no-op, so nothing counts twice.
- `progress.mastery`: correct / seen, or none when unseen.
- Tests: 3 unit (unseen, all correct, all wrong), 4 API and database
  (only the objectives covered, submit twice, counts add up across
  attempts, a mock), 1 migration (backfill counts only submitted
  attempts; an unanswered item is seen and wrong). With the `record` call
  removed, the API tests fail.
- Decisions (simplest option, owner's call):
  - One student: no `user_id` until accounts exist, so the "users see
    only their own progress" test waits too.
  - An unanswered item counts as seen and wrong, as in scoring.
  - Recency weighting is left to step 2: counts can't be weighted, but
    `attempt_item.answered_at` keeps the history.
  - Oral exercises and scenarios don't update mastery; their rubric marks
    don't map to one objective as right or wrong.

## Tests

Unit (CI):
- Mastery: a new objective, all correct, all wrong, and recent answers
  outweighing old ones.
- Weak areas: an objective below the threshold but seen fewer than N
  times is not flagged. A low self-rating is flagged.
- Recommendations: return at most 5, only from the chosen exam, each
  with a reason string. Ties are ordered predictably.

API and database (CI):
- Submitting a quiz updates `objective_mastery` for exactly the
  objectives it covered.
- Users see only their own progress.

End-to-end (CI):
- After a quiz with deliberate wrong answers, the dashboard shows the
  related objectives as weak, with the reason.

## Done when

- Every recommendation shows the reason for it.
- No "readiness" claim appears without the underlying numbers next to
  it.
