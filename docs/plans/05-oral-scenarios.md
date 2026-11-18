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

## Done when

- Grading agrees with itself on at least 90% of criteria across
  repeat runs.
- Every exercise shows the "educational simulation" disclaimer.

## Review gate

An instructor reviews the scenarios and rubrics.
