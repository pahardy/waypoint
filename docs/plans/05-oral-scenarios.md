# Phase 5: Oral and Scenario Exercises

Goal: interactive exercises in which the student explains concepts or
makes decisions, with feedback against a defined rubric.

Spec MVP step 5.

## Exercise types

- **Oral question:** for example, "Explain the effects of a blocked
  static port." The student answers in free text, and Waypoint asks
  follow-up questions.
- **Scenario:** a staged situation, such as a weather deterioration
  en route or a diversion. Each stage reveals new information and asks
  for a decision.

## Design

- **Authoring:** exercises are YAML files in `content/exercises/`.
  Each has a prompt, stages, rubric criteria and source references.
  Exercises are written by people, possibly with LLM drafts, and then
  reviewed.
- **Rubric:** each criterion has an id, a description, a weight and
  the expected key points.
- **Grading:** the LLM marks each criterion as met, partly met or not
  met, and must quote evidence from the student's answer. The total
  score is calculated in code from the weights.
- **State:** the scenario stage and its revealed facts are held in
  code, not in the LLM's context alone. A `session` table stores the
  state.
- Weather data in scenarios is synthetic and clearly labelled. No live
  NAV CANADA data is used.

## Tests

Unit (CI):
- Exercise YAML validation: every exercise has a prompt, stages,
  rubric criteria with weights, and source references.
- Score calculation from criterion marks and weights, including all
  met, none met and mixed.
- Scenario state machine: stages advance in order, revealed facts
  accumulate, and a finished scenario cannot advance.
- Grading response parsing (stub LLM): a valid response maps to
  criterion marks. A response that is missing a criterion, or that
  gives no evidence quote, is rejected and retried once.

API and database (CI, stub LLM):
- Start a session, answer each stage, and get the graded result.
- Session state survives a reload.

End-to-end (CI, stub LLM):
- Complete one scenario and see the rubric feedback and disclaimer.

Eval (on demand, real model):
- Grading consistency: 10 sample answers graded 3 times each. Agreement
  is recorded in `docs/evals/`.
- Grading against expected marks: sample answers with known grades.

## Steps

1. Build one oral question with a three-criterion rubric, end to end,
   in the CLI.
2. Check grading consistency: grade 10 sample answers 3 times each and
   measure agreement.
3. Build one two-stage scenario.
4. Add the web pages.
5. Write 5 oral questions and 3 scenarios per pathway.

## Progress

Step 1 (one oral question in the CLI), issue #26:
- `content/exercises/static-port.yaml`: a blocked static port, three
  criteria (altimeter 1, VSI 1, airspeed 2), key points from the cited
  passage (FAA PHAK p.213; instrument behaviour is not Canada-specific).
- `exercises.py` validates the format and checks that sources are in the
  knowledge base; the score is calculated in code (met full weight, partly
  met half, not met none; halves rounded up).
- `grading.py`: one structured call (Claude Sonnet 5.5, server-side
  fallback). Code rejects a response with a missing or repeated criterion,
  a met or partly met mark without a quote, or a quote not in the answer,
  and retries once.
- `uv run oral static-port`, answer on stdin. Shows the "Educational
  simulation. Not operational guidance." banner before and after.
- Three hand-written answers, graded once each (2026-11-23):

  | Answer | Altimeter | VSI | Airspeed | Score |
  |---|---|---|---|---|
  | Strong | met | met | met | 100% |
  | Partial | partly met | not met | partly met | 38% |
  | Weak | not met | not met | not met | 0% |

  Lenient mark: the partial answer said the airspeed "reads too high when
  you climb" (wrong direction) and still got partly met, for saying the
  reading is wrong. The rubric says a wrongly stated point is not met.
  Left for the step 2 consistency eval to measure, not tuned here.
- The flight-instructor review gate before this phase was skipped: owner
  decision, 2026-11-23.

Step 2 (grading consistency), issue #28:
- `api/eval/oral.yaml`: 10 answers to `static-port`, strong to weak,
  including vague, wrong-direction, reversed, pitot/static mix-up and
  grader-instruction answers; expected marks written from the rubric and
  its cited passage.
- `uv run oral-eval` grades each answer 3 times (resumes if interrupted);
  consistency, agreement, the confusion table and score spread are
  calculated in code.
- Result (2026-11-24, Sonnet 5.5, effort low, $0.23):
  [docs/evals/oral-2026-11-24.md](../evals/oral-2026-11-24.md).
  - **Consistency 27/30 (90%): the 90% target is met**, with no margin.
  - Agreement with expected marks 83/90 (92%); 6 of the 7 wrong marks are
    partly met where a wrongly stated point should give not met: the
    step 1 leniency, confirmed.
  - Proposed follow-up: state in the grading prompt that any wrongly
    stated key point gives not met.
- Follow-up, issue #30: the prompt now says a wrongly stated key point
  gives not met. Re-run (`--variant wrong-point-not-met`, $0.23):
  consistency 30/30 (100%), agreement 90/90 (100%), no score varies.
  [Report](../evals/oral-2026-11-24-wrong-point-not-met.md). Checked on
  the same 10 answers the rule was written from, so new exercises need
  their own eval answers.

Step 3 (one two-stage scenario in the CLI), issue #32:
- `content/exercises/deteriorating-weather.yaml`: a day VFR cross-country
  between fictional aerodromes. Stage 1, before departure: a synthetic
  METAR and TAF (ceiling, TEMPO, control-zone VFR minima). Stage 2, en
  route: visibility below the minima ahead in uncontrolled airspace below
  1,000 ft AGL. Key points from CAR 602.114, 602.115 and TC AIM MET 7.3
  and 8.2. The student explains the rules and options; no go/no-go call.
- `Scenario` and `Stage` validate the format (at least two stages, unique
  ids, a question and rubric each). `ScenarioState` advances stages in
  order, accumulates the revealed facts and refuses to advance once
  finished. State is in memory; the session table comes with step 4.
- Each stage is graded by the oral grader, unchanged, with the facts
  revealed so far in the question. Overall score: the mean of the stage
  scores, halves rounded up.
- `uv run scenario deteriorating-weather`; piped answers are separated by
  a line holding only `---`. The disclaimer and "All weather in this
  scenario is synthetic" show before and after.
- Two sets of answers, graded once each (2026-11-24):

  | Answers | Stage 1 (ceiling, TEMPO, minima) | Stage 2 (minima, ahead, conclusion) | Overall |
  |---|---|---|---|
  | Strong | met, met, met: 100% | met, met, met: 100% | 100% |
  | Weak | not met, not met, partly met: 25% | not met, not met, not met: 0% | 13% |

  Borderline mark: the weak stage 1 answer ("Visibility is 5 miles, so
  it's fine to go") got partly met on minima for the 5 SM meeting the
  3-mile minimum, though it ignored the TEMPO. Defensible under the rule;
  no consistency eval yet for scenarios.

Step 4 (web pages), issue #34:
- Migration 0009: `exercise_session` (current stage, start and finish
  times) and `stage_answer` (answer, marks with evidence and reasons,
  score). An oral exercise is a one-stage session, so both kinds share
  one table, one API and one page.
- API (`sessions.py`): `GET /exercises`, `POST /sessions`,
  `GET /sessions/{id}`, `POST /sessions/{id}/answers` (409 once
  finished; 502 with nothing stored when grading fails). The grader and
  the cited passages are dependencies, stubbed in the tests and the
  end-to-end stub server.
- Web: `/exercises` lists both exercises; `/exercises/[sessionId]` shows
  the revealed facts, the current question, each graded stage and the
  overall score, with the simulation disclaimer and the synthetic-weather
  label. Plan 07 updated: the URL holds the session id.
- Tests: 9 API and database tests (a deliberately broken version that
  stored before grading failed the "stores nothing" test), 3 web unit
  tests, 1 end-to-end test that reloads between stages (desktop and
  phone, axe clean).
- Checked in the real app with the real grader (2026-11-24, 3 grading
  calls, about $0.03), driven in a browser:

  | Exercise | Answers | Marks | Score |
  |---|---|---|---|
  | Scenario | Strong stage 1 | met, met, met | 100% |
  | | Weak stage 2 ("the minimum is 1 mile ... I can keep going") | not met, not met, not met | 0% |
  | | Overall, with a reload between stages | | 50% |
  | Oral | Wrong airspeed direction | met, met, not met | 50% |

  The oral mark confirms the #30 rule in the app. Cosmetic: a one-stage
  exercise shows both the stage score and the same overall score.
- Seen while checking: after a client-side navigation the previous page
  stays mounted but hidden (`cacheComponents` in next.config), on the
  practice pages too. Not a defect; a test locator on `main` must
  allow for it.

Step 5a (PPAER content), issue #36:
- `uv run check-exercises`: every exercise loads, its sources are in the
  knowledge base, and the Opus judge decides from the cited passages
  alone whether each key point is supported (code checks every point got
  a verdict). Calibrated on 2026-11-24: static-port passed; two planted
  errors (a reversed airspeed direction, an invented 6-to-9-second VSI
  lag) were both caught.
- It found a gap in step 3's scenario: `-RA` and `BR` were decoded
  without a source. TC AIM MET 8.2:2 is now cited.
- Six new PPAER exercises; PPAER now has 5 oral questions and 3
  scenarios:

  | Exercise | Kind | Subject | Sources |
  |---|---|---|---|
  | static-port | oral | aeronautics | PHAK p.213 |
  | carburettor-ice | oral | aeronautics | PHAK pp.169-170 |
  | right-of-way | oral | air law | CAR 602.19 |
  | compass-heading | oral | navigation | PHAK pp.393-394 |
  | thunderstorm-life-cycle | oral | meteorology | FAA AWH pp.257-258 |
  | deteriorating-weather | scenario | meteorology | CAR 602.114, 602.115; TC AIM MET 7.3, 8.2 |
  | fuel-reserve | scenario | navigation | CAR 602.88 |
  | radio-failure | scenario | air law | CAR 602.138; TC AIM RAC 4.4.7 |

  FAA sources are used only for facts that are the same in Canada.
- `check-exercises` (2026-11-24): all 8 pass. Its one finding on the new
  content, fixed: fuel-reserve's change-of-destination key point gave
  only the 30-minute reserve, but CAR 602.88(2) also requires the
  subsection (5) allowances.
- Smoke test, one strong and one weak answer per new exercise, graded
  once: every strong answer 100% (all met), every weak answer 0% (all not
  met). The answers sit close to the key points, so this shows each
  rubric can be met and failed, not how it grades answers in between.
- Fixed along the way: the exercise list repeated "Scenario (PPAER)" as
  a heading; each exercise is now headed by its name.
- Cost: estimated under $2 (13 judge calls, 16 grading calls).
- Review: the judge checked the content; the owner may approve it
  without a read-through. The instructor review gate below stays open.

## Done when

- Grading agrees with itself on at least 90% of criteria across
  repeat runs.
- Every exercise shows the "educational simulation" disclaimer.

## Review gate

An instructor reviews the scenarios and rubrics.
