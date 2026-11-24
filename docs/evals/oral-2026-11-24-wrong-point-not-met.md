# Oral Grading Eval: 2026-11-24, wrong point gives not met

Issue #30. One change from the
[baseline](oral-2026-11-24.md): the grading prompt adds "If any key point
is stated wrongly, the mark is not_met, even if other key points are
right." Same answers, grader (Sonnet 5.5, effort low) and 3 reps.

- Run: `uv run oral-eval --variant wrong-point-not-met` in `api/`
- Raw results: `.claude/hillclimb/oral/wrong-point-not-met/results.jsonl`

## Before and after

| Measure | Baseline | This run |
|---|---|---|
| Consistency (target 90%) | 27/30 (90%) | 30/30 (100%) |
| Agreement with expected marks | 83/90 (92%) | 90/90 (100%) |
| Answers whose score varies | 3/10 | 0/10 |
| Cost | $0.23 | $0.23 |

- The 6 lenient marks are now not met: `airspeed-wrong-direction` 75% to
  50% on every rep; `reversed-effects` and `pitot-static-mixup` 0% on
  every rep.
- No mark that matched before stopped matching.
- The one strict mark (`airspeed-climb-only / vsi`, partly met for missing
  the criterion description) did not recur: met on all 3 reps.

## Limits

The rule was written after seeing these 10 answers, and this run checks
it on the same 10. A perfect score here shows the rule fixes the cases it
was aimed at, not that it holds for other answers or other exercises.
New exercises (plan 05 step 5) should get their own eval answers.

## Run output

- Grader: `claude-sonnet-5-5`, effort `low`
- Exercise: `static-port`; 10 answers; 30 gradings; 30 model calls; 0 errors
- Cost: $0.23

| Measure | Result |
|---|---|
| Consistency (identical marks; target 90%) | 30/30 (100%) |
| Agreement with expected marks | 90/90 (100%) |
| Answers whose score varies | 0/10 |

Confusion (rows expected, columns given):

| Expected | met | partly met | not met |
|---|---|---|---|
| met | 39 | 0 | 0 |
| partly met | 0 | 15 | 0 |
| not met | 0 | 0 | 36 |

Scores per answer:

| Answer | Scores | Range |
|---|---|---|
| strong-full | 100%, 100%, 100% | 0 |
| strong-terse | 100%, 100%, 100% | 0 |
| vague | 50%, 50%, 50% | 0 |
| airspeed-wrong-direction | 50%, 50%, 50% | 0 |
| reversed-effects | 0%, 0%, 0% | 0 |
| airspeed-climb-only | 75%, 75%, 75% | 0 |
| pitot-static-mixup | 0%, 0%, 0% | 0 |
| altimeter-only | 25%, 25%, 25% | 0 |
| vsi-wrong | 50%, 50%, 50% | 0 |
| grader-instruction | 25%, 25%, 25% | 0 |

## Inconsistent or wrong marks

None.
