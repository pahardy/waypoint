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

## Update: judge calibration and rubric fix (issue #15)

**Haiku 5.5 as a cheaper judge.** Re-grading the 52 stored answers with
Claude Haiku 5.5 (same rubric, same passages) agreed with Opus on only
69% of pass verdicts. All disagreement was in the grounding check: Haiku
missed real errors Opus caught (twilight, CAR 602.77(4), winds aloft) and
flagged trivia (spelling out "VNC", "ask your instructor").

**What it revealed about Opus.** Haiku flagged claims about exams that
Opus had passed ("For your PPAER exam, the pilot answer is 12 hours";
"a common exam question") while Opus failed the same kind of claim
elsewhere. Cause: the rubric did not name exam claims, and did not say
what clearly is not a claim.

**Rubric fix** (`judge.py`): unsupported claims now explicitly include
official definitions and statements about what an exam asks, emphasises
or expects; spelling out abbreviations, general explanation, the answer's
own arithmetic, and suggestions to ask an instructor or check an official
publication or flight manual are explicitly not claims.

**Re-graded baseline (Opus, new rubric): pass 0.74** (95% CI 0.62 to
0.86), down from 0.81. Six verdicts moved, all as the rubric intended:
four exam claims now fail (alcohol, speed limit, Class C, Vne), one
unsupported definition fails (overfly aerodrome), and the advice-only ELT
answer now passes. Previous grades: `baseline/results.before-regrade.jsonl`.

**Haiku with the new rubric: 65% agreement**, worse. It failed 30 answers
to Opus's 14, reading the rules too literally (for example treating
"for the exam, can you name..." quiz prompts as exam claims). Haiku is not
a usable judge for this eval. Results: `calibration-haiku/results.jsonl`.

**Open:** whether a study tip ("For the exam, remember the pairing:
2,000 ft and 3 miles") counts as a claim about what an exam emphasises is
still ambiguous; Opus passes it, Haiku fails it.

The hill-climb loop was stopped before round 1 on cost: with Opus as the
only trustworthy judge, a full run is $2.89, about two-thirds of it the
judge. The four planned changes (shorter web-page citation labels, prompt
rules on exam claims and advice, effort medium, retrieval across page
splits) remain to do.

Another finding: Voyage query embeddings vary slightly between calls, so
near-tied passages can swap between runs. The runner now records each
case's passage ids so re-grading uses exactly what the instructor saw.
