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

## Done when

- The eval set passes the agreed thresholds.
- Citations in the web UI link to the document, edition and section.
