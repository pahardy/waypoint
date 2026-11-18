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

## Done when

- Every recommendation shows the reason for it.
- No "readiness" claim appears without the underlying numbers next to
  it.
