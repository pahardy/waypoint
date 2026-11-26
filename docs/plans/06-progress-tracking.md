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

Step 2 (dashboard), issue #44:
- `GET /progress/{PSTAR|PPAER}`: per subject, correct, seen and percent;
  then the weak objectives with their reasons, for example "2 of 5
  correct (40%), below the 90% pass mark". Calculated in `progress.py`.
- Weak rule: seen at least 5 times (`MIN_SEEN`) and below the exam's
  pass mark (`exams.meets`, so exactly at the mark is not weak). Lowest
  first; ties by objective id. Percentages are rounded down, so 59.9%
  shows as 59%, never as "60%, below the 60% pass mark".
- `/dashboard`: an exam choice, the subject table (correct, seen,
  percent as text), the weak objectives with reasons, an empty state and
  the disclaimer. Linked from the home page. No readiness wording.
- Tests: 6 more unit (seen 4 times, exactly at the mark, the reason's
  numbers, ordering and ties, subject totals, rounding), 3 API and
  database (a weak objective and its reason, per exam, FLIGHT_TEST
  refused), 3 web unit (numbers, empty state, no weak objectives), 3
  end-to-end on desktop and phone (an unanswered topic quiz makes
  Aviation Occurrences weak with its reason; axe clean in both themes).
  The end-to-end tests submit unanswered quizzes so the wrong answers are
  certain on the shared dev database.
- Decisions (simplest option, owner's call): threshold is the exam's pass
  mark, N is 5; plain correct / seen, no recency weighting; one exam at a
  time.
- Seen on the dev database (history almost all from end-to-end runs):
  PSTAR 22% with all 14 objectives weak; PPAER 1-3% per subject with 100
  weak objectives. A long list; step 3's 3-5 recommendations are the
  short view.

Step 3 (recommendations), issue #46:
- `GET /progress/{exam}` adds `recommendations`: the first 5
  (`MAX_RECOMMENDATIONS`) of the weak list, with the same reasons.
- `/dashboard`: "Study next" at the top, each recommendation with its
  topic, reason and a Start quiz button that starts a topic quiz on that
  objective and opens it. The full weak list is collapsed below as "All
  weak objectives (N)". With nothing weak, Study next links to a mixed
  quiz on /practice.
- Tests: 2 more unit (the five weakest in order with reasons, fewer weak
  gives fewer), 2 API assertions (recommendations per exam), 5 web unit
  (reason and the quiz request, the collapsed count, nothing weak, no
  answers, subject numbers), 2 more end-to-end on desktop and phone (a
  failed objective is in the weak list and Study next has reasons;
  Start quiz on the first recommendation gives a quiz on that objective
  only). The end-to-end tests take the first recommendation, not a named
  one, because the shared dev database decides which five come first.
- Decisions (simplest option, owner's call): the top 5 of the weak list,
  no second ranking; a quiz button, no reading link; unseen objectives
  are not recommended.

Step 4 (self-rated confidence), issue #48:
- Migration 0011: `self_confidence` is text, `low`, `medium` or `high`,
  or null.
- `PUT /objectives/{id}/confidence` sets or clears a rating; 404 until
  the objective has been answered, 422 for an unknown value. Results
  carry each topic's rating, and the "By topic" table has a rating
  control that saves on change.
- Weak rule: (seen at least 5 and below the pass mark) or rated low.
  Reasons: "2 of 5 correct (40%), below the 90% pass mark; rated low
  confidence", "4 of 4 correct (100%); rated low confidence", or "Rated
  low confidence" with no answers. Order and recommendations unchanged.
- Tests: 5 more unit (low flagged whatever the counts, medium and high
  change nothing, both reasons, no answers, order), 5 API (set, change
  and clear; low shows on /progress; 404; 422; the CORS preflight for
  PUT), 1 web unit (shows the saved rating and sends the change), 1
  end-to-end on desktop and phone (rate low on results, then "rated low
  confidence" on the dashboard).
- Found by the end-to-end test, both fixed: CORS allowed only GET and
  POST, so the browser's PUT preflight got "400 Disallowed CORS method";
  and the dev database lacked migration 0011 ("invalid input syntax for
  type smallint"), which the API tests miss because they build a fresh
  database. Run `uv run migrate` after pulling a migration.
- Decisions (simplest option, owner's call): per objective; rated on the
  results page only; three words, not a number.

Phase 6 is done, except the "users see only their own progress" test,
which waits for accounts (plan 07).

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
