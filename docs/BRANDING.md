# Branding, Look and Feel

Addresses GitHub issue #3.

## Concept: "Night cross-country"

Waypoint should feel like the cockpit on a clear night flight: a deep
navy sky, instrument amber and precise chart lines. It is calm,
focused and a little exciting. It should look like a modern flight
instrument, not a government form or a generic e-learning site.

The design borrows from things a student pilot already knows and
wants to master:
- **Aeronautical charts:** waypoint symbols, track lines and tick marks.
- **Instrument faces:** round gauges, bezels and needle markers.
- **Flight strips and checklists:** compact cards and the
  challenge-and-response rhythm.

The site must not use, or look like, Transport Canada or NAV CANADA
branding. Waypoint is independent of both.

## Name and tagline

- Name: **Waypoint**
- Tagline: **Plot your course to the PPL.**
- Descriptor: Canadian pilot training and exam preparation.

## Logo

- **Mark:** a four-pointed waypoint star inside a thin circle, with a
  short track line passing through it at a slight angle, like a leg
  on a chart. Drawn as a single-colour SVG at 1.5 px stroke weight, so
  it stays sharp from 16 px to hero size.
- **Wordmark:** "WAYPOINT" in the display font, uppercase, with wide
  letter spacing.
- **Colour:** the mark is in Beacon amber on Night, or Night on light
  backgrounds.
- **Favicon:** the mark only.

## Colour

Colour values are defined as CSS variables in the design system (see
`docs/plans/07-web-application.md`). Every text and background pair
below was checked against WCAG 2.2 AA: 4.5:1 or better on both
background and surface.

| Token | Role | Dark theme | Light theme |
|---|---|---|---|
| `--bg` | Page background | Night `#0B1426` | `#F6F8FB` |
| `--surface` | Cards, panels | `#13213A` | `#FFFFFF` |
| `--text` | Body text | `#E8EEF7` | `#0E1A2E` |
| `--muted` | Secondary text | `#9AA8BD` | `#4A5970` |
| `--accent` | Beacon amber: primary actions, logo, focus | `#F5A524` | `#A15C00` |
| `--sky` | Links, information, the instructor | `#38BDF8` | `#0369A1` |
| `--airway` | Chart magenta: highlights, track lines, citations | `#F062A8` | `#B0206E` |
| `--pass` | Correct, passed | `#34D399` | `#047857` |
| `--fail` | Incorrect, failed | `#F87171` | `#B91C1C` |

Usage rules:
- Dark is the default theme, and it is the signature look. The light
  theme follows the system setting, or the user's choice.
- Amber is for one primary action per screen. Overuse dulls it.
- On amber buttons, the text is `--on-accent`: Night `#0B1426` in the dark
  theme (9:1) and white in the light theme (4.9:1 on `#A15C00`).
- Pass and fail always come with an icon or a word, never colour alone.

## Typography

| Use | Font | Notes |
|---|---|---|
| Display and headings | **Barlow Condensed** (Google Fonts), 600–700 | Narrow and technical. Echoes airport signage and instrument labels. |
| Body and UI | **Inter** (Google Fonts), 400–600 | Highly legible at small sizes on phones |
| Data | **JetBrains Mono** (Google Fonts) | METARs, TAFs, regulation references, timers, scores |

- Type scale: 14, 16, 18, 22, 28, 36 and 48 px. Body text is 16 px
  with a line height of 1.6.
- Headings are uppercase only at H1 and H2 and in section labels.
  Lower levels use sentence case.

## Motifs and components

- **Waypoint markers:** the logo star marks steps in a progression,
  such as the PSTAR, PPAER and flight-test path on the dashboard.
- **Track line:** a dashed magenta line connects completed waypoints.
  This is the main progress visual on the landing page and dashboard.
- **Gauges:** subject scores appear as round instrument gauges with
  tick marks. The arc fills to the score and a pass-mark tick sits at
  60%.
- **Flight strips:** list items, such as questions, exercises and
  sources, are narrow cards with a coloured left edge that shows their
  status.
- **Checklist style:** the flight-test companion uses
  challenge-and-response rows with a dotted leader, for example
  "Pre-flight inspection ........ REVIEWED".
- **Citation chips:** small magenta-outlined chips in the mono font,
  for example `TC AIM RAC 2.8.1`. They open the source detail.
- **Badges:** `OFFICIAL` (amber), `PRACTICE` (sky) and `NON-CANADIAN`
  (muted, outlined).
- **Background texture:** a very faint latitude and longitude grid
  on hero sections only. Never behind body text.

## Imagery

- No stock photos of smiling pilots.
- Use SVG illustrations in the brand colours: chart fragments, a
  stylized aircraft silhouette (generic high-wing trainer, no real
  manufacturer's markings), and runway number motifs.
- The landing page hero is a night chart with a magenta track running
  through three waypoints labelled PSTAR, PPAER and FLIGHT TEST.

## Motion

- Short and purposeful, 150–250 ms. Ease-out on enter.
- Gauge needles sweep to their value once, on first view.
- The track line draws itself on the dashboard when progress changes.
- Respect `prefers-reduced-motion`: switch to fades, or no motion.

## Voice and tone

Write like a good flight instructor: calm, precise and encouraging.

- Short sentences and plain language. Define jargon on first use.
- Light use of aviation phrasing where it fits naturally, for example
  "Ready for departure?" or "Course correction: review Air Law 2.3".
  Never at the cost of clarity.
- Honest about limits: "I couldn't find this in the sources I have.
  Check the current TC AIM or ask your instructor."
- No guarantees: never say "you're ready for the exam". Show the
  numbers instead.

## Disclaimer placement

- A footer on every page: "Waypoint is an educational aid. It does not
  replace flight instruction, an authorized examiner or current
  Transport Canada publications."
- A short banner before scenarios: "Educational simulation. Not
  operational guidance."

## Accessibility

- WCAG 2.2 AA throughout. Visible amber focus rings, 2 px.
- Touch targets of at least 44 px.
- Gauges and charts have text equivalents.
