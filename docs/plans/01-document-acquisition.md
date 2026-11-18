# Phase 1: Document Acquisition and Curriculum

Goal: download the selected federal documents, record exactly what we
have, and turn the official study guides into a structured list of
learning objectives.

Spec MVP step 1: "Confirm the curriculum."

## Scope

Documents, from `docs/RESEARCH.md` section 3:

| Priority | Document | Use |
|---|---|---|
| 1 | TP 11919 (PSTAR guide), 7th ed. | Objectives and official PSTAR questions |
| 1 | TP 12880 (PPAER guide), 6th ed. | Objectives for the four subject areas |
| 1 | TP 13723E (Flight Test Guide), Mar 2021 | Flight-test exercises and criteria |
| 1 | TC AIM (TP 14371), current issue | Main reference text |
| 1 | Canadian Aviation Regulations (XML from Justice Laws) | Regulatory citations |
| 2 | Standard 421 and Standard 428 (web pages) | Licensing and flight-test conduct |
| 2 | TP 13014 (sample exam, 2008) | Question style reference only |
| 2 | TP 975, TP 14277 | Flight-test preparation |
| 2 | RIC-21 (ISED) | Radio |
| 3 | MANOBS (ECCC), Aviation Safety Letter issues, selected TSB reports | Meteorology detail and scenarios |
| 3 | FAA PHAK and Aviation Weather Handbook | Theory, tagged `non-CA` |

Out of scope: NAV CANADA documents and *From the Ground Up*.

## Design

- **Manifest:** `ingest/sources.yaml` lists each source with an id,
  title, publisher, TP number, edition, publication date, URL,
  jurisdiction, licence note and format. It is committed, because it
  holds metadata only.
- **Downloader:** `uv run ingest fetch` reads the manifest, downloads
  each source into `data/raw/<id>/`, and records the retrieval date
  and a SHA-256 hash in `data/raw/<id>/meta.json`.
- **Objectives:** the learning objectives are extracted from TP 11919,
  TP 12880 and TP 13723 into `db/seed/objectives.yaml`. Each objective
  records its exam, subject, topic, objective text and source section.
  This file contains short paraphrased objective names only, so it can
  be committed.

## Steps

1. Write `sources.yaml` for priority 1 only. Check each URL by hand.
2. Implement `fetch` for PDF and HTML. Verify the files open and the
   hashes are recorded.
3. Confirm the open exam facts from `RESEARCH.md` section 6 against
   the downloaded TP 12880 and TP 11919, and update `RESEARCH.md`.
4. Extract the PPAER objectives from TP 12880, with a script assisted
   by manual review. Check the count per subject against the guide.
5. Extract the PSTAR and flight-test objectives in the same way.
6. Add the priority 2 and 3 sources.

## Tests

Unit (CI):
- `sources.yaml` loads and validates: required fields are present, ids
  are unique, and no source is published by NAV CANADA.
- `fetch` with a mocked HTTP client writes the file and `meta.json`
  with the correct SHA-256 and retrieval date.
- `fetch` skips a source whose hash is unchanged, and keeps the
  previous copy when a new download's hash differs, logging the
  change.
- `fetch` reports an HTTP 404 for one source and continues with the
  others.
- `objectives.yaml` validates: every objective has an exam, subject,
  text and source reference, and ids are unique.

Manual (recorded in this document when done):
- Each priority 1 file opens and matches the expected edition.
- Objective counts per subject match the count in TP 12880.

## Done when

- Every priority 1 source is in `data/raw/` with recorded metadata.
- `objectives.yaml` covers PSTAR, all four PPAER subjects and the
  flight-test exercises, and each objective points to a source
  section.
- The exam facts in `RESEARCH.md` are confirmed or corrected.

## Open questions

- Should the Canadian Aviation Regulations be pinned to one
  consolidation date, or refreshed on every run? Proposal: pin, and
  refresh by hand.
