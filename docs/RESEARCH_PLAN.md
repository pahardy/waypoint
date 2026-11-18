# Research Plan: Source Documentation for the Waypoint Knowledge Base

Addresses GitHub issue #1. Scope follows `CLAUDE.md`: the Canadian PPL-A
pathway (PSTAR, PPAER, PPL-A flight test).

This is a plan, not a finished survey. Document titles, TP numbers,
editions, URLs and licence terms below come from prior knowledge. Each
item is marked **Verify** until someone confirms it against the
publisher's current page.

## 1. Goals

1. List candidate sources for each exam pathway and subject area.
2. Rate each source's expected quality and its suitability for ingestion.
3. Identify material that is not publicly available, what it would
   provide, and the impact of leaving it out.
4. Produce a verified source register (section 7) that the
   knowledge-base build (MVP step 2) can use.

## 2. Evaluation criteria

Rate each source on these criteria:

| Criterion | Question |
|---|---|
| Authority | Is it from Transport Canada (TC), the Justice Laws site, NAV CANADA or another official body, or is it secondary? |
| Jurisdiction | Is it Canadian? If not, which parts are still valid (for example aerodynamics)? |
| Currency | What are its edition and amendment date, and how often is it updated? |
| Licence | May we store it, chunk it, embed it, quote it to users and cite it? |
| Format | Is it HTML, a text-based PDF, or a scanned PDF? Is the section structure clean enough to cite? |
| Coverage | Which exams, subjects and learning objectives does it cover? |

Expected quality ratings:
- **High:** official, current, and directly maps to exam objectives.
- **Medium:** official but indirect, or secondary but reputable.
- **Low:** unofficial, outdated, or from another jurisdiction.

## 3. Publicly available sources (candidates)

### 3.1 Curriculum and exam definition

| Source | Publisher | Covers | Expected quality | Notes |
|---|---|---|---|---|
| PSTAR study and reference guide (TP 11919, **Verify**) | TC | PSTAR | High | Historically shipped with the public PSTAR question bank. Check whether the bank is still published and whether it may be reused. |
| PPAER study and reference guide (TP number **Verify**) | TC | PPAER | High | Defines the exam's subject areas and references. This is the main source for mapping learning objectives. |
| Flight Test Guide: Private Pilot Licence Aeroplane (TP 13723, **Verify**) | TC | Flight test | High | Lists each exercise with its aim, description and performance criteria. It is the base for the flight-test companion. |
| Written examination information pages (format, time, pass marks) | TC | All exams | High | The spec says these facts must be verified before we show them as current. |
| Flight crew licensing standard (CAR Standard 421) | TC / Justice Laws | Licensing requirements | High | Sets experience, knowledge and medical requirements. |

### 3.2 Regulations and air law

| Source | Publisher | Covers | Expected quality | Notes |
|---|---|---|---|---|
| Canadian Aviation Regulations (SOR/96-433) | Justice Laws website | Air Law, PSTAR | High | Available as HTML and XML with stable section numbering, which suits citation. Updated often, so record the date of each consolidation. |
| TC Aeronautical Information Manual (TC AIM, TP 14371) | TC | Air Law, Navigation, Meteorology, Radio | High | Free to download and revised twice a year. This is the core reference for PSTAR and PPAER. |
| Advisory Circulars and Staff Instructions | TC | Varies | Medium | Useful for interpretation. Only a small subset is relevant to PPL. |
| Restricted operator certificate (aeronautical) study guide (RIC-21, **Verify**) | ISED Canada | Radio procedures | Medium–High | Covers the radio certificate that PPL holders need. |

### 3.3 Navigation and aeronautical data

| Source | Publisher | Covers | Expected quality | Notes |
|---|---|---|---|---|
| Canada Flight Supplement (CFS) and Water Aerodrome Supplement | NAV CANADA | Navigation, airport operations | High | Authoritative but licensed. Check whether it may be redistributed or embedded (**Verify**). |
| VNC and VTA charts and chart legends | NAV CANADA | Navigation | High | Charts are sold commercially. The legends and the user guides may be usable on their own. |
| Designated Airspace Handbook | NAV CANADA | Airspace | High | Licence terms **Verify**. |
| NAV CANADA flight planning and weather site (CFPS) | NAV CANADA | Live METAR, TAF, GFA, NOTAM | High (live) | For scenarios only, never for operational advice. Check the terms of use before any automated access. |

### 3.4 Meteorology

| Source | Publisher | Covers | Expected quality | Notes |
|---|---|---|---|---|
| Aviation Weather Services Guide | NAV CANADA | METAR, TAF, GFA decoding | High | Freely downloadable (**Verify**). Maps directly to PPAER meteorology. |
| Local Area Knowledge Aviation Weather (LAKES) manuals | NAV CANADA | Regional weather | Medium–High | Six regional volumes. Useful for scenario realism. |
| MET section of the TC AIM | TC | Meteorology | High | Already counted in 3.2. |
| Meteorological Service of Canada educational material | ECCC | General meteorology | Medium | Not aviation-specific. |

### 3.5 Aeronautics general knowledge, human factors and safety

| Source | Publisher | Covers | Expected quality | Notes |
|---|---|---|---|---|
| Flight Instructor Guide (TP 975, **Verify**) | TC | Exercise teaching points | Medium–High | Useful for flight-test preparation and for the instructor persona. |
| Aviation Safety Letter and other safety publications | TC | Human factors, ADM | Medium | Real Canadian cases. |
| Air transportation investigation reports | TSB Canada | Scenarios, ADM | Medium–High | Public reports that are a rich source of scenario material. Must be anonymized and summarized with care. |
| FAA Pilot's Handbook of Aeronautical Knowledge, Airplane Flying Handbook, Aviation Weather Handbook | FAA | Aerodynamics, systems, weather theory | Medium | US public domain and well written. Use only for jurisdiction-neutral theory, and tag them **non-Canadian** so they never back a regulatory answer. |

### 3.6 Practice questions

| Source | Expected quality | Notes |
|---|---|---|
| PSTAR public question bank (if still published) | High | The only official question set that may be public. Confirm its status and whether reuse is allowed. |
| Self-authored questions mapped to TP objectives | Medium to start, High after SME review | This is the main route for PPAER practice content (see 4.1). |

## 4. Material not publicly available, or restricted

| Material | What it provides | Impact if absent | Mitigation |
|---|---|---|---|
| **4.1 PPAER examination question bank** (TC, confidential) | Exact questions, distractors, and the weight of each topic | We cannot reproduce real questions, and the spec forbids presenting generated ones as official. Practice tests may drift from the real exam's difficulty and emphasis. | Write questions against the published TP objectives. Calibrate difficulty with a flight instructor or other SME and with feedback from students who have passed. Label all questions as practice. |
| **4.2 Commercial ground-school textbooks** (for example *From the Ground Up*; the Flight Training Manual and its publication status **Verify**) | The de facto Canadian syllabus, with narrative explanations, diagrams and Canadian examples | Explanations draw on the regulations, the AIM and FAA theory instead. This may be less pedagogical and miss Canadian teaching conventions. Ingesting the books without a licence is not permitted. | Pursue a licence with the publisher. Otherwise cite them only as recommended reading, not as ingested content. |
| **4.3 Aircraft Pilot Operating Handbooks** (manufacturer copyright) | V-speeds, limitations, emergency checklists, performance charts | We cannot give aircraft-specific numbers or procedures, which matters for the flight test and for scenarios. Fabricating them would be a safety problem. | Use generic teaching only. Let students upload their own POH for private use (licence **Verify**), or seek manufacturer permission. |
| **4.4 Commercial question banks and apps** | Large pools of exam-like questions | Same as 4.1. These are also copyrighted, and many are of unknown accuracy. | Do not ingest. |
| **4.5 NAV CANADA charts and supplements under restrictive licence** | Real aerodrome data and chart symbology for navigation exercises | Navigation and planning scenarios are less realistic. | Seek a licence. Use synthetic or excerpted charts within fair-dealing limits, and clearly mark them as not for navigation. |
| **4.6 Examiner-internal guidance and marking practice** (anything beyond the public Flight Test Guide; check whether a public flight test examiner manual exists, **Verify**) | How examiners interpret the criteria and common failure points | Flight-test preparation rests only on published standards and could miss practical emphasis. | Interview examiners and instructors during validation (MVP step 7). |
| **4.7 Flight school syllabi and training records** | Lesson sequencing and common student errors | Personalization starts without priors on typical weak areas. | Partner with schools. Learn from in-app performance data, with consent. |
| **4.8 ICAO Annexes and documents** (paid) | International standards | Low impact, because Canadian requirements govern this product. | Mention only to distinguish jurisdictions. |

## 5. Expected coverage summary

| Pathway or subject | Public coverage | Main gap |
|---|---|---|
| PSTAR | Strong (CARs, TC AIM, study guide, possibly the official question bank) | None significant |
| PPAER: Air Law | Strong | Official question style |
| PPAER: Navigation | Medium | Licensed charts and the CFS |
| PPAER: Meteorology | Strong | Official question style |
| PPAER: Aeronautics general knowledge | Medium (FAA theory plus TC safety material) | Canadian textbooks and POH data |
| Flight-test preparation | Medium (Flight Test Guide, Instructor Guide) | POHs and examiner practice |

## 6. Research tasks

1. For every **Verify** item, confirm the current title, TP number,
   edition, publication date, URL and format.
2. Read the copyright or terms-of-use notice for each source. Record
   whether it may be ingested, quoted and redistributed, and whether
   it is covered by the Open Government Licence – Canada.
3. Confirm that the PPAER and PSTAR question banks are public or
   restricted, and confirm the current exam format, time limits and
   pass marks.
4. Map the learning objectives in the TP study guides to candidate
   sources. Mark each objective as covered, partial or gap.
5. Download a sample of each high-priority source and assess its
   extraction quality: text versus scanned PDF, and section structure.
6. Contact the restricted publishers (textbook publisher, NAV CANADA,
   aircraft manufacturers) about licensing.
7. Record results in the source register (section 7) and close
   issue #1.

## 7. Source register (to be filled in)

| Source | Publisher | Edition / date | URL | Licence | Format | Pathways | Quality | Ingest? |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |
