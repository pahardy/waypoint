# Retrieval Eval: 2026-11-19

- Model: `voyage-4-large`; search: keyword only (PostgreSQL full text)
- Questions: 72 (`ingest/eval/retrieval.yaml`)
- Sources: cars, tc-aim, tp12880 (2983 chunks)

| Subject | Questions | Recall@5 | MRR@10 |
|---|---|---|---|
| pstar | 13 | 0.23 | 0.13 |
| air-law | 15 | 0.67 | 0.44 |
| navigation | 12 | 0.42 | 0.31 |
| meteorology | 12 | 0.58 | 0.55 |
| aeronautics | 13 | 0.85 | 0.53 |
| exam | 7 | 0.43 | 0.14 |
| **all** | **72** | **0.54** | **0.37** |

## Not in the top 5

- **pstar-01** (not in top 10): My radio quits while I'm flying VFR inside a control zone. What am I supposed to do? Expected RAC 4.4.8, CAR 602.138; top 3 were RAC 2.7.3, CAR 303.05, RAC 4.7.
- **pstar-03** (not in top 10): While I'm taxiing, the tower points a steady red light at me. What does it mean? Expected RAC 4.2.11; top 3 were AGA 7.5.1, AGA 7.8.2, AGA 7.8.5.
- **pstar-04** (not in top 10): I'm circling to land without a radio and the tower shows me a steady red light. What should I do? Expected RAC 4.4.7; top 3 were AGA 7.5.1, AGA 7.8.2, AGA 7.8.5.
- **pstar-05** (not in top 10): How high do I have to be when flying over a city? Expected RAC 5.4, CAR 602.14; top 3 were CAR 602.88, AIR 2.4.3, RAC 3.12.2.
- **pstar-06** (not in top 10): Can I fly low over an airport if I'm not landing or taking off there? Expected RAC 5.5, CAR 602.96; top 3 were CAR 303.05, CAR 302.08, CAR 302.07.
- **pstar-08** (not in top 10): What should my transponder be set to for a normal VFR flight at 6,500 feet? Expected COM 8.4; top 3 were CAR 700.240, CAR 700.60, CAR 602.34.
- **pstar-09** (not in top 10): What does it mean when ATC says the weather is CAVOK? Expected RAC 1.4; top 3 were MET 1.3.8, RPA 3.2.22.1, CAR 101.01.
- **pstar-11** (not in top 10): How much extra fuel do I need to carry on a daytime VFR cross-country? Expected RAC 3.12.1, CAR 602.88; top 3 were RAC 4.7, RAC 3.15.9.3, AIR 1.3.3.
- **pstar-12** (not in top 10): My ELT went off by accident after a hard landing. Who do I tell? Expected SAR 3.7; top 3 were SAR 3.8.2, SAR 3.4, SAR 3.9.
- **pstar-13** (rank 6): A military jet pulls up beside me and rocks its wings. What am I expected to do? Expected SAR 4.6; top 3 were AIR 1.7, MET 4.12, AIR 2.9.
- **air-law-02** (not in top 10): What are the minimum altitude and visibility for doing aerobatics? Expected RAC 1.9, CAR 602.27; top 3 were GEN 5.1, RAC 8.6.1, RAC 9.19.1.
- **air-law-06** (not in top 10): Does ATC provide me any service at all in uncontrolled airspace? Expected RAC 2.8.7; top 3 were RAC 1.1.1, CAR 801.21, RPA 3.2.3.2.
- **air-law-08** (not in top 10): What information has to be in my arrival report? Expected RAC 3.11.1; top 3 were RAC 8.1, MET 8.4.4, MET 8.4.3.
- **air-law-09** (rank 10): Which frequency should I listen to and broadcast on when cruising VFR in uncontrolled airspace? Expected RAC 5.1; top 3 were RPA 3.2.3.2, RPA 3.2.3.2, CAR 601.01.
- **air-law-14** (not in top 10): What do I need to do to stay current to carry passengers? Expected LRA 1.12, CAR 401.05; top 3 were RAC 3.4.7, CAR 604.85, RAC 3.4.1.
- **navigation-01** (not in top 10): Why are runways in the Far North given in degrees true instead of magnetic? Expected RAC 2.2.1; top 3 were AGA 5.8.3, RAC 4.2.5, GEN 5.1.
- **navigation-03** (not in top 10): What frequencies do NDBs transmit on? Expected COM 4.6; top 3 were COM 1.4.2, COM 4.7, COM 1.4.
- **navigation-06** (rank 7): Which cities have VFR terminal area charts? Expected MAP 2.5.2; top 3 were RAC 9.2.2, RAC 4.7, RAC 9.2.2.
- **navigation-07** (not in top 10): Where do I find an airport's services, facilities and phone numbers? Expected MAP 2.5.3; top 3 were CAR 302.07, CAR 302.08, CAR 801.24.
- **navigation-08** (not in top 10): What is a NOTAM and when is one issued? Expected MAP 3.1; top 3 were MAP 3.2.3.1, MAP 3.3, MAP 3.4.
- **navigation-09** (not in top 10): What time standard is used in Canadian aviation? Expected GEN 1.5; top 3 were LRA 1.5, GEN 5.2, RAC 3.4.7.
- **navigation-12** (not in top 10): Can GPS signals be jammed or interfered with? Expected COM 5.10; top 3 were COM 5.2.1, AIR 1.8, COM 4.10.7.
- **meteorology-03** (rank 7): What does a TAF tell me? Expected MET 7.2; top 3 were MET 7.5, MET 7.4, MET 7.3.
- **meteorology-07** (not in top 10): What is an AIRMET and what altitudes does it cover? Expected MET 5.1; top 3 were GEN 5.1, RAC 8.6.1, RAC 9.17.1.
- **meteorology-08** (not in top 10): What is a SIGMET? Expected MET 6.1; top 3 were MET 6.15, MET 6.16, MET 6.12.
- **meteorology-11** (not in top 10): A thunderstorm is approaching the airport. Should I still take off? Expected AIR 2.7.2; top 3 were CAR 302.08, RAC 9.6.1, RAC 9.3.
- **meteorology-12** (not in top 10): What is a microburst and why is it dangerous when landing? Expected AIR 2.8, MET 2.3; top 3 were RAC 4.4.3, RAC 12.3, COM 11.2.
- **aeronautics-04** (not in top 10): Why do I feel like I'm turning when I'm actually flying straight in cloud? Expected AIR 3.7; top 3 were CAR 303.05, AGA 5.4.2, AGA 7.5.1.
- **aeronautics-09** (not in top 10): How much crosswind can a typical light aircraft be landed in? Expected AIR 2.2; top 3 were RPA 3.2.27.2, RAC 1.8, CAR 201.01.
- **exam-01** (not in top 10): How many questions are on the PPL written exam, how long do I get, and what's the pass mark? Expected TP 12880 p.7; top 3 were LRA 4.3, CAR 202.02, CAR 202.03.
- **exam-02** (not in top 10): I passed the written overall but failed the meteorology part. What happens now? Expected TP 12880 p.8; top 3 were CAR 571.07, CAR 571.09, CAR 521.307.
- **exam-05** (not in top 10): What happens if someone gets caught cheating on a pilot written exam? Expected TP 12880 p.5, LRA 3.2, CAR 400.02; top 3 were CAR 901.90, CAR 903.02, CAR 901.56.
- **exam-06** (not in top 10): What do I need before I'm allowed to write the PPL written exam? Expected TP 12880 p.4, CAR 401.13; top 3 were CAR 303.05, AGA 5.4.2, AGA 7.5.1.
