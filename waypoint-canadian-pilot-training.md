# Waypoint

## Canadian Pilot Training & Exam Preparation

Waypoint is an AI-powered study and training companion for people
pursuing a Canadian Private Pilot Licence -- Aeroplane (PPL-A).

Its initial focus is specific: help students prepare for the Canadian
Student Pilot Permit examination (PSTAR), the Private Pilot Licence
Aeroplane written examination (PPAER), and the knowledge and procedural
components of the PPL-A flight test.

Waypoint is an educational aid. It does not replace flight instruction,
an authorized flight examiner, current Transport Canada publications, or
a pilot's operational responsibilities.

## Initial audience and scope

The first release targets aspiring Canadian private pilots training in
the aeroplane category, from early student-pilot preparation through the
PPL-A flight test. It deliberately does not attempt to cover every
licence, aircraft category, or jurisdiction.

## Examination pathways

### 1. PSTAR --- Student Pilot Permit

Prepare students for the PSTAR examination, covering foundational
Canadian aviation knowledge required before solo flight.

Study areas include: - Canadian aviation regulations and operating
rules - Airspace and airport operations - Radio communication and
procedures - Flight rules and pilot responsibilities - Aviation safety

### 2. PPAER --- Private Pilot Licence Aeroplane written examination

Organize the curriculum around the four mandatory subject areas:

-   **Air Law:** Canadian Aviation Regulations, licensing, airspace,
    operating rules, communications, and procedures.
-   **Navigation:** Aeronautical charts, plotting, headings, bearings,
    wind correction, flight planning, and fuel calculations.
-   **Meteorology:** Weather systems, clouds, fronts, METARs, TAFs,
    turbulence, icing, and visibility.
-   **Aeronautics --- General Knowledge:** Aerodynamics, aircraft
    structures and systems, engines, flight instruments, flight
    operations, and human factors.

Practice tests and progress reports should reflect the current published
examination structure. Question counts, time limits, pass marks, and
subject-area thresholds must be verified against current Transport
Canada guidance before being presented as current facts.

### 3. PPL-A flight-test preparation

Help students understand the flight-test standards and prepare for the
knowledge, planning, and decision-making involved in practical
evaluation.

Preparation topics may include: - Pre-flight planning and preparation -
Aircraft inspection and documentation - Normal and crosswind takeoffs
and landings - Circuit procedures - Airwork and manoeuvres - Navigation
and diversion planning - Emergency and abnormal procedures - Arrival and
landing procedures - Aeronautical decision-making and risk management

Waypoint can explain standards, provide scenario practice, and help
students prepare for discussions with instructors. It cannot assess or
certify real-world flying skill or replace supervised flight training
and the examiner's flight test.

## Core product capabilities

### 1. Structured aviation knowledge base

Build a searchable, citation-backed knowledge base from authoritative
Canadian aviation material.

Potential sources include: - Transport Canada examination guides and
flight-test guides - Canadian Aviation Regulations and associated
standards - Transport Canada aeronautical publications and safety
material - Relevant aircraft Pilot Operating Handbooks (POHs), where the
student has access to the applicable documentation - Reputable aviation
textbooks and learning resources, subject to licensing and usage rights

Organize content with metadata such as: - Jurisdiction - Licence and
aircraft category - Examination - Subject area - Topic and learning
objective - Source document, edition, and publication date - Section or
page reference

Answers should cite their sources and identify when information is
incomplete, outdated, jurisdiction-specific, or not covered by retrieved
material.

### 2. AI aviation instructor

Provide conversational instruction that explains concepts at an
appropriate level and responds to follow-up questions.

The instructor should: - Explain difficult concepts in plain language -
Adjust explanations to the student's level - Use examples and practical
aviation scenarios - Compare related concepts and clarify common
misconceptions - Ask questions to check understanding - Ground
regulatory and technical claims in retrieved sources

### 3. Examination practice

Provide practice questions and timed mock examinations aligned with the
relevant examination objectives.

Capabilities: - Topic-specific quizzes - Mixed-subject practice tests -
Timed mock examinations - Explanations for correct and incorrect
answers - Performance breakdowns by subject and topic - Question review
and targeted follow-up practice

Generated questions must be clearly identified as practice questions,
not official Transport Canada examination questions unless explicitly
licensed and sourced as such. Assessment content should be reviewed for
technical accuracy.

### 4. Oral questioning and scenario-based learning

Go beyond recall-based multiple-choice questions. The application should
conduct interactive questioning in which students explain concepts, make
decisions, or work through situations. It can ask follow-up questions,
identify gaps in reasoning, and provide feedback against a defined
rubric.

Example exercises: - Explain the consequences of a blocked pitot tube or
static port. - Interpret a METAR and TAF for a proposed training
flight. - Explain airspace and communication requirements for a route. -
Work through a diversion or deteriorating-weather scenario. - Discuss
considerations involved in an abnormal or emergency situation.

Scenarios are educational simulations, not operational instructions or
substitutes for instructor-led training.

### 5. Flight-test study companion

Translate the published flight-test guide into a study and preparation
checklist.

Students can: - Review the purpose and standards of each exercise -
Study related knowledge and procedures - Practise explaining decisions
and risks - Prepare questions for their instructor - Track areas they
want to review before a lesson or flight test

The product must not imply that completing its exercises guarantees
flight-test success.

### 6. Learning progress and personalization

Maintain a record of study activity and demonstrated knowledge.

Track: - Completed topics and learning objectives - Quiz and mock-exam
performance - Repeated errors and misconceptions - Confidence and
self-identified weak areas - Recommended next topics and practice
exercises

Use this information to create targeted study plans. Recommendations
should be explainable and linked to examination objectives rather than
based on opaque claims of readiness.

## Suggested technical architecture

  -----------------------------------------------------------------------
  Component                           Suggested technology or approach
  ----------------------------------- -----------------------------------
  Frontend                            React / Next.js

  Backend                             Python / FastAPI

  LLM                                 OpenAI API or another evaluated
                                      model provider

  Retrieval and vector storage        Supabase / PostgreSQL with vector
                                      search

  Embeddings                          Evaluated embedding model
                                      appropriate to the source material

  Document ingestion                  Python extraction, normalization,
                                      chunking, and metadata pipeline

  Orchestration                       Explicit application workflows and
                                      LLM tool calling

  External integrations               MCP servers where they provide
                                      useful, well-defined capabilities

  Voice (later phase)                 Speech-to-text and text-to-speech

  Student records                     PostgreSQL relational data model
  -----------------------------------------------------------------------

Keep document retrieval, student records, question and assessment logic,
and external integrations as distinct components. Use deterministic code
for scoring, examination timing, eligibility rules, and other logic that
should not be left to an LLM.

Use MCP where an external system or data provider offers a useful tool
interface. It is not necessary to make every internal application
function an MCP server.

## Safety, accuracy, and currency

Aviation information can be safety-critical. Waypoint must be designed
as an educational aid, not an operational authority.

Key requirements: - Prefer current, authoritative Transport Canada
sources for Canadian licensing and regulatory content. - Store source
edition, publication date, and retrieval date. - Review and refresh
content when source documents change. - Cite the source supporting
regulatory, procedural, and technical answers. - Clearly distinguish
Canadian requirements from FAA, ICAO, or other jurisdictions. - Do not
fabricate regulatory requirements, aircraft limitations, procedures, or
examination standards. - Flag uncertainty and direct students to their
instructor and current official publications. - Do not provide
operational go/no-go decisions or imply that AI-generated guidance is
sufficient for flight planning. - Protect student records and obtain
appropriate consent for any instructor access.

## MVP scope and development sequence

The first release should concentrate on the Canadian PPL-A pathway.

1.  **Confirm the curriculum.** Map PSTAR, PPAER, and PPL-A flight-test
    objectives to current Transport Canada source documents.
2.  **Build the knowledge base.** Ingest a carefully selected set of
    official documents, preserve document versions and section
    references, and test retrieval quality.
3.  **Build the AI instructor.** Support grounded explanations,
    citations, follow-up questions, and topic-based learning.
4.  **Build practice assessments.** Implement reviewed question sets,
    topic quizzes, mock examinations, deterministic scoring, and
    performance reporting.
5.  **Add oral and scenario exercises.** Use structured rubrics and
    scenario state to assess explanations and decision-making.
6.  **Add student progress tracking.** Personalize study recommendations
    using actual performance and curriculum coverage.
7.  **Validate with aviation professionals.** Have a Canadian flight
    instructor or other qualified subject-matter expert review content,
    questions, scenarios, and product boundaries.

## Future expansion

Once the Canadian PPL-A product is reliable, consider: - Commercial
Pilot Licence --- Aeroplane (CPL-A), including CPAER preparation -
Instrument Rating --- Aeroplane, including INRAT preparation - Airline
Transport Pilot Licence --- Aeroplane (ATPL-A), including SAMRA and
SARON preparation - IATRA examination preparation - Additional
aircraft-specific study modules - Instructor-facing lesson preparation
and student progress tools - Voice-based oral examination and ATC
communications practice

Treat each expansion as a distinct curriculum and validate it against
its own current official requirements.

## Product positioning

**Waypoint --- Canadian Pilot Training & Exam Preparation**

An AI-powered study companion that helps aspiring pilots understand
aviation, prepare for Transport Canada examinations, practise applying
their knowledge, and identify what to study next.

The differentiator is not simply access to an aviation chatbot or a
large question bank. It is a structured, source-grounded learning
pathway that connects official examination objectives, instruction,
assessment, scenario practice, and ongoing progress.
