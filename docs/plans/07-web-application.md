# Phase 7: Web Application

Goal: the site itself. Its pages are built alongside phases 3–6. This
document holds the shared structure. Look and feel follow
`docs/BRANDING.md`.

## Pages

| Route | Page | Phase |
|---|---|---|
| `/` | Landing page: what Waypoint is, the three pathways, disclaimer | 0 |
| `/sign-in` | Sign in | 3 |
| `/dashboard` | Progress overview and recommendations | 6 (a placeholder before that) |
| `/learn` | AI instructor chat | 3 |
| `/practice` | Choose a quiz or mock exam | 4 |
| `/practice/[attemptId]` | Quiz or exam in progress, with timer | 4 |
| `/results/[attemptId]` | Results breakdown and question review | 4 |
| `/exercises` and `/exercises/[sessionId]` | Oral and scenario exercises; the URL holds the session, so a reload continues it | 5 |
| `/flight-test` | Flight-test study companion: exercises from TP 13723 with a personal checklist | 5 |
| `/sources` | List of ingested documents with their editions and dates | 2 |
| `/about` | Purpose, limitations, "built with Claude", sources policy | 0 |

## Design system

- Tailwind CSS with design tokens from `docs/BRANDING.md`, defined as
  CSS variables. Light and dark themes.
- A small component set: Button, Card, Badge (official, practice,
  non-CA), CitationChip, Gauge (progress), FlightStrip (list item),
  Timer, Disclaimer.
- Accessibility: WCAG 2.2 AA contrast, full keyboard navigation, and
  no information conveyed by colour alone.
- Mobile first: students will often study on their phones.

## Accounts

- Supabase Auth with email magic links. No passwords to manage.
- One role: student. Instructor access (from the spec) is deferred.

## Data access

- The browser talks only to the FastAPI backend. The backend talks to
  the database.
- The API checks the Supabase session token on each request.

## Steps

1. Phase 0: landing page and about page with the brand tokens.
2. Build the component set in isolation, then the chat page (phase 3).
3. Practice pages (phase 4). Exercise pages (phase 5).
4. Dashboard (phase 6).
5. Hosting decision: keep it local, or deploy the frontend and backend
   to a hosting provider.

## Progress

`/flight-test`, issue #50 (spec capability 5, the flight-test study
companion):
- The 32 TP 13723 items in guide order, grouped by exercise, as
  checklist rows with a dotted leader and the status as text (TO REVIEW
  or REVIEWED). Each row opens to its aim, a citation chip for its guide
  page, links to the exercises that practise it, a Reviewed checkbox and
  a "Questions for my instructor" note (saved on blur, at most 500
  characters). A count at the top, and the statement that marking items
  reviewed does not mean the student is ready for, or will pass, the
  flight test.
- API: `GET /flight-test`, `PUT /flight-test/{objective_id}` (404 for
  other objectives). Migration 0012 adds `flight_test_checklist` and
  `objective.detail`, which holds the aims from `objectives.yaml`; the
  seed did not store it before, so run `uv run migrate` and `uv run
  seed`.
- Tests: 6 API and database, 3 web unit, 3 end-to-end on desktop and
  phone (mark and note kept after a reload; axe clean in both themes).
  Desktop and phone edit different items, so parallel runs on the shared
  database don't collide.
- Fixed while testing: the checkbox waited for the save before it
  changed, so clicking it showed nothing at first. It now changes at once
  and reverts, with "Not saved.", if the save fails.
- Decisions (simplest option, owner's call): reviewed or not, no other
  status; aims and pages as stored, nothing model-written; exercise links
  go to /exercises.
- Spec capability 5 is covered; sharing with an instructor waits for
  accounts and consent.

## Tests

Component (CI, Vitest and React Testing Library):
- Each shared component renders its states, for example the Badge
  variants, a Gauge at 0%, 60% and 100%, and the Timer near zero.
- Gauges and status colours have text equivalents.

Accessibility (CI):
- An automated accessibility scan (axe, through Playwright) on each
  route in both themes, with no serious or critical issues.

End-to-end (CI, Playwright, stub LLM):
- Sign in with a test account on the local Supabase stack.
- Chat, a full quiz, results and the dashboard, each at desktop and
  phone sizes.
- Unauthenticated users are redirected from protected pages to sign-in.
- The disclaimer is present on every page.

API (CI):
- Requests with a missing, expired or invalid token get 401.

## Done when

- All routes work on a phone-sized screen and in both themes.
- End-to-end checks cover sign-in, chat, a full quiz and the results
  page.
