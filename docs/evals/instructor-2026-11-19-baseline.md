# Instructor Eval: 2026-11-19 baseline

- Instructor: `claude-sonnet-5-5`, effort `low`; retrieval as in plan 03 step 1
- Judge: `claude-opus-5-5`, effort `high`, structured verdicts
- Cases: 54 (`api/eval/instructor.yaml`, reviewed in `api/eval/instructor-cases.md`), 1 rep
- Run: `uv run instructor-eval` in `api/`; 2 min 50 s; $2.89 including the judge; no errors

| Measure | Result |
|---|---|
| **Pass** | **0.81** (44/54; 95% CI 0.71 to 0.92) |
| Key facts stated (answer cases) | 0.99 |
| Grounded (no unsupported claim, no FAA as Canadian) | 0.87 |
| Expected behaviour | 1.00 |
| Valid citations | 0.94 |
| Cites an expected section (diagnostic) | 0.98 |
| Latency per answer | median 5.5 s, max 9.3 s |
| Cost per judged case | median $0.055 |

By kind: answer 36/45, decline 4/5, not covered 2/2, off-topic 2/2.
By level: PSTAR 10/13, PPAER 33/38, flight test 1/3.

## Judge checks

- Before the run: a correct answer passed; an empty answer, "I don't
  know" and a confident answer to another question all failed.
- Pilot of six cases reviewed by the project owner; the strict rule on
  unsupported claims (including claims about what exams test) was kept.
- All ten baseline failures were read. Nine are real faults; one
  (pstar-elt-accidental, failed for advising an inspection after a hard
  landing) is borderline, since it is advice rather than a rule.

## Failures

| Pattern | Cases |
|---|---|
| Unsupported or misstated claim (scope of a rule, a missing condition, a misread table, a procedure not in the passages) | pstar-radio-failure, air-law-arrival-report-content, navigation-twilight, meteorology-gfa-times, meteorology-winds-aloft |
| Claim about what an exam tests | pstar-vfr-fuel |
| Advice stated as a procedure (borderline) | pstar-elt-accidental |
| Cited a rule that was not retrieved | decline-evade-rules (CAR 602.14) |
| Shortened a long web-page label, so the citation cannot be matched | flight-test-steep-turn, flight-test-partial-retest |
| Retrieval: the steep turn tolerances are on the next page (TP 13723 p.23) and were not retrieved | flight-test-steep-turn |

## What to try next

1. Shorter citation labels for web-page sections (code change).
2. Prompt: no claims about what exams test unless a passage says so;
   advice and general procedure clearly marked as not from the sources.
3. Effort `medium` against `low` for the misread and misstated cases.
4. Retrieval for exercises split across pages (flight-test guide).

The system prompt (about 450 tokens) is below the 512-token minimum for
prompt caching, so no cache reads occurred. Pass rate noise at 54 cases
and one rep is about plus or minus 12 points; compare variants over
several reps.
