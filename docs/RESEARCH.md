# Research Results: Knowledge-Base Sources

Addresses GitHub issue #2. Carries out `docs/RESEARCH_PLAN.md`.

Research date: 2026-11-18.

Method: web searches against publisher pages (tc.canada.ca, Justice
Laws, navcanada.ca, ISED, TSB, faa.gov) and the Government of Canada
publications catalogue (publications.gc.ca). No documents were
downloaded or acquired, as the issue instructed.

Confidence levels:
- **Confirmed:** found on the publisher's own page or catalogue record.
- **Partial:** found in older editions or secondary sources only.
- **Open:** not resolved. Listed in section 6.

## Decisions (2026-11-18)

- Waypoint is a non-commercial test project. It may never have users.
- Transport Canada and other federal government documents will be
  used in the knowledge base.
- NAV CANADA documents will not be ingested. NAV CANADA is a private,
  not-for-profit corporation, so its documents are not Crown
  copyright, and its reuse terms are unknown.
- *From the Ground Up* will not be ingested.

Impact of leaving out NAV CANADA:
- **Meteorology:** the Aviation Weather Services Guide and the
  regional weather manuals are lost. The MET chapter of the TC AIM,
  MANOBS (ECCC) and the FAA Aviation Weather Handbook cover most of
  the theory. Canadian product formats (for example the GFA) rely on
  the TC AIM alone.
- **Navigation:** the CFS, charts and Designated Airspace Handbook are
  lost. The TC AIM covers airspace classes and chart principles.
  Exercises based on real aerodromes and charts are not possible.

## 1. Summary

- **Core curriculum documents:** All of them are free from Transport
  Canada (TC), and they cover the PPL-A pathway. These are the PSTAR
  guide (TP 11919), the PPAER guide (TP 12880), the PPAER sample exam
  (TP 13014), the Flight Test Guide (TP 13723), the TC AIM (TP 14371)
  and Standard 421.
- **Regulations:** The Canadian Aviation Regulations are on Justice
  Laws in HTML, PDF and XML, with point-in-time versions back to 2006.
  This is the best-structured source for citations.
- **Examiner material:** The Pilot Examiner Manual (TP 14277) is
  public, which partly closes a gap the plan assumed. Internal marking
  practice is still not public.
- **Licensing is the main risk.** TC permits copying for personal and
  public **non-commercial** use. Revising or adapting a TC work, or
  distributing a commercial product, needs Crown copyright permission.
  We found no evidence that the Open Government Licence – Canada
  covers TC aviation publications. NAV CANADA's licence terms are
  unknown.
- **Restricted content:** The actual PPAER question bank is
  confidential. The leading textbook, *From the Ground Up*, is
  commercially copyrighted. Aircraft operating handbooks (POHs) are
  manufacturer copyright.

## 2. Exam facts

Confirmed on 2026-11-18 against the downloaded TP 12880 (6th ed., May
2025) and TP 11919 (7th ed., December 2022).

| Exam | Questions | Time | Pass mark | Source |
|---|---|---|---|---|
| PSTAR | 50, selected from about 200 in TP 11919 (14 sections) | Not stated in TP 11919 | 90% | TP 11919, introduction |
| PPAER | 100 | 3 hours | 60% overall, and 60% in each of Air Law, Navigation, Meteorology and Aeronautics – General Knowledge | TP 12880, p. 4 |
| PALAW (Air Law supplementary) | 20 | 1 hour | 60% | TP 12880, p. 5 |
| PANAV (Navigation supplementary) | 20 | 2 hours | 60% | TP 12880, p. 5 |
| PAMET (Meteorology supplementary) | 30 | 1½ hours | 60% | TP 12880, p. 5 |
| PAGEN (Aeronautics – General Knowledge supplementary) | 30 | 1½ hours | 60% | TP 12880, p. 5 |

Rules from TP 12880:
- **Partial pass:** 60% or more overall, but under 60% in one or more
  subjects. The candidate writes a supplementary exam for each failed
  subject, in one sitting. Several supplementaries together may not
  exceed 3 hours.
- **Fail:** under 60% overall. The full exam must be rewritten
  (CAR 421.26).
- **Rewrite waiting periods (CAR 400.04):** 14 days after a first
  failure, 30 days after a second, then 30 days more for each further
  failure, up to 180 days. PSTAR may be rewritten at any time after
  reviewing weak areas.
- **Validity:** all exams for a licence must be completed within the
  24 months before the licence application.
- **Feedback:** the results letter lists the questions answered
  incorrectly.

Still unconfirmed, and not to be shown to students as fact:
- The PSTAR time limit. A third party says 90 minutes.
- Exam fees. Third parties say CAD 100–105 for PPAER and CAD 35 for
  PSTAR. TP 12880 mentions "the appropriate examination fee" without
  an amount.

## 3. Source register: publicly available

### 3.1 Curriculum and exam definition

| Source | Publisher | Edition / date | URL | Licence | Pathways | Quality | Confidence |
|---|---|---|---|---|---|---|---|
| Study and Reference Guide: Student Pilot Permit or PPL for Foreign and Military Applicants, Aviation Regulations (TP 11919) | TC | 7th ed., Dec 2022 | [TC page](https://tc.canada.ca/en/aviation/publications/student-pilot-permit-private-pilot-licence-foreign-military-applicants-aviation-regulations-tp-11919) | TC non-commercial | PSTAR | High | Confirmed |
| Study and Reference Guide for Written Examinations for the PPL Aeroplane (TP 12880) | TC | 6th ed., May 2025 | [TC page](https://tc.canada.ca/en/aviation/publications/study-reference-guide-written-examinations-private-pilot-licence-aeroplane-tp-12880), [PDF on publications.gc.ca](https://publications.gc.ca/collections/collection_2026/tc/T52-4-55-2025-eng.pdf) | The page says it "may be reproduced as required" | PPAER | High | Confirmed |
| Sample Examination: Recreational Pilot Permit and PPL Aeroplane (TP 13014) | TC | 4th ed., Nov 2008 | [Catalogue record](https://publications.gc.ca/site/eng/350688/publication.html) | TC non-commercial | PPAER | Medium (predates the 2025 guide) | Confirmed |
| Flight Test Guide: PPL Aeroplane (TP 13723E) | TC | 6th ed. (revised), Mar 2021, 35 pp. | [TC page](https://tc.canada.ca/en/aviation/publications/flight-test-guide-private-pilot-licence-aeroplane-tp-13723e) | TC non-commercial | Flight test | High | Confirmed |
| Standard 421: Flight Crew Permits, Licences and Ratings | TC | Live web page | [TC page](https://tc.canada.ca/en/corporate-services/acts-regulations/list-regulations/canadian-aviation-regulations-sor-96-433/standards/standard-421-flight-crew-permits-licences-ratings-canadian-aviation-regulations-cars) | TC | All (PPL-A is at 421.26) | High | Confirmed |
| Standard 428: Conduct of Flight Tests | TC | Live web page | [TC page](https://tc.canada.ca/en/corporate-services/acts-regulations/list-regulations/canadian-aviation-regulations-sor-96-433/standards/standard-428-conduct-flight-tests-canadian-aviation-regulations-cars) | TC | Flight test | High | Confirmed |
| Information for Student Pilots and Pilots Seeking Flight Training (TP 15703E) | TC | Apr 2026 | [TC page](https://tc.canada.ca/en/aviation/publications/information-student-pilots-pilots-seeking-flight-training-tp-15703e) | TC non-commercial | Orientation | Medium | Confirmed |

### 3.2 Regulations and air law

| Source | Publisher | Edition / date | URL | Licence | Pathways | Quality | Confidence |
|---|---|---|---|---|---|---|---|
| Canadian Aviation Regulations (SOR/96-433) | Justice Laws | Consolidated regularly. Point-in-time versions go back to 2006. | [Full text](https://laws.justice.gc.ca/eng/regulations/SOR-96-433/FullText.html) | Reproduction terms of federal law: **Open** | PSTAR, PPAER Air Law | High. XML is available (about 4 MB). | Confirmed |
| TC Aeronautical Information Manual (TC AIM, TP 14371) | TC | Revised twice a year. Current issue: 2026-2 (Oct 2026). | [TC page](https://tc.canada.ca/en/aviation/publications/transport-canada-aeronautical-information-manual-tc-aim-tp-14371) | TC non-commercial | All | High. Available as a full PDF (about 28 MB) and per-chapter PDFs. | Confirmed |
| RIC-21: Study Guide for the Restricted Operator Certificate with Aeronautical Qualification (ROC-A) | ISED Canada | Current web version | [ISED page](https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/node/817) | ISED (Crown) | Radio | Medium–High | Confirmed |

### 3.3 Navigation and aeronautical data

| Source | Publisher | Edition / date | URL | Licence | Pathways | Quality | Confidence |
|---|---|---|---|---|---|---|---|
| Designated Airspace Handbook (TP 1820) | NAV CANADA | 56-day cycle. Latest issue found: No. 323, 3 Sep 2026. | [navcanada.ca](https://www.navcanada.ca/en/dah20260903.pdf) | Free to download. Reuse terms **Open**. | Air Law, Navigation | High | Confirmed |
| Canada Flight Supplement (CFS) | NAV CANADA | 56-day cycle | [Shop](https://products.navcanada.ca/shop-vfr/) | **Paid**, single sale only. Licence **Open**. | Navigation | High | Confirmed |
| VNC (52 charts) and VTA (7 terminal areas) charts | NAV CANADA | Periodic | [Shop](https://products.navcanada.ca/shop-vfr/) | **Paid** (VTA about CAD 16.50 each). Licence **Open**. | Navigation | High | Confirmed |
| Aeronautical Publications Guide | NAV CANADA | Current | [PDF](https://www.navcanada.ca/en/publications/_localised-assets/files/14-403_aeronautical-publications-guide_e3.pdf) | Free | Reference | Medium | Confirmed |

### 3.4 Meteorology

| Source | Publisher | Edition / date | URL | Licence | Pathways | Quality | Confidence |
|---|---|---|---|---|---|---|---|
| Aviation Weather Services Guide | NAV CANADA | Revised May 2017. A newer edition is **Open**. | [PDF](https://www.navcanada.ca/EN/media/Publications/AWS-Guide-EN.pdf) | Free. Reuse terms **Open**. | PPAER Meteorology | Medium–High (may be dated) | Confirmed |
| Local Area Knowledge Aviation Weather manuals (6 regions: BC, Prairies, Ontario–Quebec, Atlantic, Yukon–NWT, Nunavut–Arctic) | NAV CANADA, prepared by MSC | Various | [Ontario–Quebec example](https://www.navcanada.ca/en/lawm-ontario-quebec-en.pdf) | Free. Reuse terms **Open**. | Meteorology, scenarios | Medium–High | Confirmed |
| Manual of Surface Weather Observation Standards (MANOBS) | ECCC | 8th ed., Amendment 2 | [ECCC page](https://www.canada.ca/en/environment-climate-change/services/weather-manuals-documentation/manobs-surface-observations.html) | Crown | Meteorology (METAR detail) | Medium | Confirmed |
| ECCC aviation weather services page | ECCC | Live | [ECCC page](https://www.canada.ca/en/environment-climate-change/services/types-weather-forecasts-use/aviation-services.html) | Crown | Meteorology | Medium | Confirmed |

The plan called the regional weather manuals "LAKES". NAV CANADA's
file names use `lawm-*`.

### 3.5 Aeronautics general knowledge, instruction and safety

| Source | Publisher | Edition / date | URL | Licence | Pathways | Quality | Confidence |
|---|---|---|---|---|---|---|---|
| Flight Instructor Guide: Aeroplane (TP 975) | TC | Revised Sep 2004 | [TC page](https://tc.canada.ca/en/aviation/publications/flight-instructor-guide-aeroplane-tp-975) | TC non-commercial | Flight test, instructor persona | Medium–High (old) | Confirmed |
| Pilot Examiner Manual (TP 14277) | TC | 7th ed., Oct 2019 | [TC page](https://tc.canada.ca/en/aviation/publications/pilot-examiner-manual-seventh-edition-tp-14277) | TC non-commercial | Flight test | High | Confirmed |
| Aviation Safety Letter (TP 185) | TC | Ongoing (Issue 2/2025 found). Older issues are in the LAC web archive. | [TC page](https://tc.canada.ca/en/aviation/publications/aviation-safety-letter) | TC non-commercial | Human factors, decision-making, scenarios | Medium | Confirmed |
| TSB air investigation reports | TSB Canada | Ongoing | [Terms](https://tsb-bst.gc.ca/eng/avis-notices/avis-notices.asp) | Non-commercial reproduction allowed with credit (from archived terms; current wording **Open**). Findings must not be used in legal proceedings. | Scenarios | Medium–High | Partial |
| Pilot's Handbook of Aeronautical Knowledge (FAA-H-8083-25C) | FAA | 2023 | faa.gov | US federal work, likely public domain | Aeronautics theory only (**non-Canadian**) | Medium | Confirmed |
| Aviation Weather Handbook (FAA-H-8083-28B) | FAA | Approved April 2026 | faa.gov | Likely public domain | Weather theory only (**non-Canadian**) | Medium | Confirmed |

## 4. Restricted or not public: findings

| Material | Finding | Impact | Recommended action |
|---|---|---|---|
| PPAER exam question bank | Not public. The only official question material is the 2008 sample exam (TP 13014). | Practice difficulty and topic weighting must be estimated. TP 13014 predates the 2025 guide. | Write questions against the TP 12880 (2025) objectives. Use TP 13014 only to check question style. Have an SME calibrate them. |
| PSTAR questions | **Public.** TP 11919 contains about 200 questions, and the exam draws 50 of them. | Positive: PSTAR practice can use official questions. | Confirm with TC whether we may reuse them, given the commercial-use restriction. |
| *From the Ground Up* (Aviation Publishers) | 30th ed., © 2024 Aviation Publishers Co. Ltd. | The de facto Canadian ground-school text, which cannot be ingested without a licence. | **Decided: not ingested.** May be cited as recommended reading. |
| TC Flight Training Manual | 4th ed. (revised) 2004, Crown copyright (T52-14/2004E). Current availability and distributor are **Open**. | It is the standard reference for flight exercises. If it is obtainable, it falls under TC terms. | Confirm its availability and whether TC permission covers it. |
| Aircraft POHs | Manufacturer copyright. Not researched further. | No aircraft-specific speeds or procedures. | Keep the plan's mitigation: generic content only, and optional student uploads after legal review. |
| NAV CANADA documents (all of section 3.3, and the weather guides in 3.4) | No reuse licence found. The CFS and charts are paid products. | See the Decisions section. | **Decided: not ingested.** |
| Examiner internal practice | TP 14277 and Standard 428 are public. Only informal marking practice is not. | Smaller gap than the plan assumed. | Fill it with instructor and examiner interviews during validation. |
| Commercial question banks and apps | Several exist (for example open-exam-prep.com, Dauntless GroundSchool, thewisepilot.com). | Copyrighted, and their accuracy varies. | Do not ingest. |

## 5. Licensing findings

1. **TC publications:** TC grants permission to copy and reproduce its
   publications for personal and public non-commercial use. Its
   [Important Notices](https://tc.canada.ca/en/corporate-services/important-notices)
   say permission is required to revise, adapt or translate a work,
   or to distribute a final product commercially. Requests go to
   TCcopyright-droitdauteurTC@tc.gc.ca.
   - Implication: Waypoint is non-commercial, so the commercial
     restriction does not apply. The notice still asks for permission
     to adapt a work, and summarizing or generating questions could
     count as adapting. This is low risk for a private test project.
     Request permission only if Waypoint is ever made public.
2. **Open Government Licence – Canada:** No TC page we found applies
   this licence to aviation publications. We must not assume it does.
3. **Justice Laws:** The reproduction terms for consolidated
   regulations still need checking.
4. **NAV CANADA:** Free documents (Designated Airspace Handbook,
   weather guides, regional manuals) and paid products (CFS, charts)
   have no published reuse terms that we found. NAV CANADA is a
   private company, so its own copyright applies. **Decided: not
   ingested.**
5. **TSB:** Reports may be reproduced non-commercially with credit
   (archived terms). There is an explicit restriction on use in legal
   or disciplinary proceedings.
6. **FAA handbooks:** As US federal works they are likely public
   domain. Commercial reprints add their own copyright.

## 6. Open items

1. Confirm the PSTAR time limit.
2. ~~Confirm the PPAER format in TP 12880~~ Done 2026-11-18 (section 2).
3. ~~Identify the current TC AIM issue~~ Done: issue 2026-2, October
   2026. (The Aviation Weather Services Guide is no longer needed,
   because NAV CANADA documents are excluded.)
4. Check whether the TC Flight Training Manual is available.
5. ~~Confirm the current FAA handbook revisions~~ Done: PHAK 25C
   (2023) and Aviation Weather Handbook 28B (April 2026).
6. Do research-plan task 5 (assess extraction quality) once document
   acquisition is approved.
7. Do research-plan task 4 (map TP 12880 objectives to sources) once
   the guide is acquired.

Dropped because the project is non-commercial: contacting TC, NAV
CANADA and Aviation Publishers about licensing; the Justice Laws and
TSB terms checks.
