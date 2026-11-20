# Phase 3: AI Instructor

Goal: a conversational instructor that explains concepts at the
student's level and grounds every regulatory or technical claim in
retrieved sources.

Spec MVP step 3.

## Behaviour

- Answers use only retrieved chunks for facts and cite them inline,
  for example "[TC AIM RAC 2.8.1]".
- When retrieval finds nothing relevant, the instructor says so, and
  directs the student to their instructor or the official publication.
- Separates Canadian rules from FAA or ICAO material.
- Adjusts to the student's level (PSTAR, PPAER or flight test), which
  the student chooses at the start.
- May end an answer with a check-for-understanding question.
- Refuses to give operational go/no-go decisions.

## Design

- **Endpoint:** `POST /chat` takes the conversation and returns a
  streamed answer with a list of citations.
- **Flow:** rewrite the latest message into a search query, call
  retrieve (phase 2), then call the LLM with the system prompt, the
  chunks and the conversation, and return the answer and citations.
- **Tool use:** a later step can expose `retrieve` as a tool the model
  calls itself. Start with the fixed flow above, because it is simpler
  to test.
- **LLM client:** `api/llm.py` wraps the provider SDK. Model ids live
  in config.
- **Conversations:** stored in a `conversation` table so phase 6 can
  use them.

## Tests

Unit (CI, stub LLM):
- Prompt assembly includes the system prompt, the retrieved chunks
  with their references, and the conversation, in that order.
- Citation parsing extracts references from the answer and maps them
  to chunk ids. A reference to a chunk that was not retrieved is
  flagged.
- When retrieval returns nothing, the "not found in sources" path runs
  without calling the LLM for facts.
- `non-CA` chunks are labelled as such in the prompt.
- LLM errors and timeouts return a clear error to the client, not a
  partial answer presented as complete.

API (CI, stub LLM and stub retrieval):
- `POST /chat` streams an answer and then sends the citation list.
- A conversation is saved and can be read back.
- Requests without a valid session are rejected (once accounts exist,
  see plan 07).

End-to-end (CI, stub LLM):
- Ask a question on the chat page, see the streamed answer and a
  citation chip that opens the source detail.

Eval (on demand, real model): see Evaluation below.

## Evaluation

- **Eval set:** about 40 questions with expected key facts and
  expected citations, plus about 10 out-of-scope or unsafe questions.
- **Automated checks:** the answer cites at least one retrieved chunk,
  the cited sections match the expected ones, and refusals happen
  where expected.
- **Model comparison:** compare candidate models on this eval set.
  The default is the latest Claude Sonnet model.

## Steps

1. Build the CLI version first: question in, answer and citations out.
2. Write the eval set and run it.
3. Add the `/chat` endpoint with streaming.
4. Add the chat page in the web app (see plan 07).
5. Compare models, and record the choice in this document.

## Progress

Step 1 (CLI), done (issue #14): `uv run instructor "question" --level PPAER`.
- `instructor.py`: retrieves up to 6 Canadian passages for the student's
  exam level and at most 2 FAA passages, labelled as background only.
  Passages scoring under 0.35 are dropped: in-scope eval questions all
  score 0.395 or more, off-topic questions 0.307 or less. If nothing is
  left, the instructor says it cannot answer, without calling the model.
- The system prompt is fixed (cacheable); the user turn carries the
  level, the labelled passages and the question.
- Citations are labels in brackets, parsed by code and matched to the
  passages given; any other reference is flagged.
- `llm.py`: Claude Sonnet 5.5 (`claude-sonnet-5-5`) at effort `low` by
  default, set by `WAYPOINT_LLM_MODEL` and `WAYPOINT_LLM_EFFORT`.
  Server-side refusal fallback is on. Refusals, truncation and API
  failures raise an error, never a partial answer.
- Hand check: alcohol (12-hour CAR and 24-hour AIM advice, all cited),
  an off-topic question (not-found path), a go/no-go request (declined,
  considerations given) and stall theory (FAA handbook named in the
  text). One fix came from it: the model put "an FAA handbook" inside
  the brackets; the prompt now says brackets hold only labels.

Step 2 (eval set and baseline), done (issue #14):
- 54 cases in `api/eval/instructor.yaml`: 45 to answer, with key facts
  confirmed by reading the sources; 5 to decline (go/no-go, medication,
  evading the rules); 2 not covered by the sources; 2 off-topic. Reviewed
  and approved by the project owner.
- `uv run instructor-eval` runs the real instructor on every case, then
  grades it with code checks (citation validity, expected section, the
  not-found path) and a Claude Opus 5.5 judge (key facts, unsupported
  claims, FAA presented as Canadian, expected behaviour). A case passes
  only if every check does. Results go to `.claude/hillclimb/instructor/`.
- Baseline: pass 0.81 (95% CI 0.71 to 0.92), key facts 0.99, $2.89 per
  run. See `docs/evals/instructor-2026-11-19-baseline.md`.

## Done when

- The eval set passes the agreed thresholds.
- Citations in the web UI link to the document, edition and section.
