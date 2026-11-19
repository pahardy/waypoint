# Retrieval Eval: 2026-11-19

- Model: `voyage-4-large`; search: hybrid (vector and keyword, reciprocal rank fusion)
- Questions: 72 (`ingest/eval/retrieval.yaml`)
- Sources: cars, tc-aim, tp12880 (2983 chunks)

| Subject | Questions | Recall@5 | MRR@10 |
|---|---|---|---|
| pstar | 13 | 0.85 | 0.65 |
| air-law | 15 | 0.93 | 0.76 |
| navigation | 12 | 0.83 | 0.63 |
| meteorology | 12 | 0.83 | 0.73 |
| aeronautics | 13 | 1.00 | 0.95 |
| exam | 7 | 1.00 | 0.79 |
| **all** | **72** | **0.90** | **0.75** |

## Not in the top 5

- **pstar-05** (rank 7): How high do I have to be when flying over a city? Expected RAC 5.4, CAR 602.14; top 3 were AIR 2.4, CAR 602.13, AIR 2.4.1.
- **pstar-09** (rank 8): What does it mean when ATC says the weather is CAVOK? Expected RAC 1.4; top 3 were MET 1.2.3, MET 7.3, RAC 1.6.1.1.
- **air-law-08** (not in top 10): What information has to be in my arrival report? Expected RAC 3.11.1; top 3 were RAC 8.1, CAR 602.77, GEN 3.3.3.
- **navigation-07** (rank 7): Where do I find an airport's services, facilities and phone numbers? Expected MAP 2.5.3; top 3 were CAR 302.08, RAC 1.1.2.3, RAC 1.2.2.
- **navigation-09** (rank 6): What time standard is used in Canadian aviation? Expected GEN 1.5; top 3 were GEN 5.2, GEN 1.5.3, MAP 3.2.3.4.
- **meteorology-07** (rank 9): What is an AIRMET and what altitudes does it cover? Expected MET 5.1; top 3 were MET 5.16, MET 5.12, MET 5.14.
- **meteorology-08** (rank 7): What is a SIGMET? Expected MET 6.1; top 3 were MET 6.11, MET 6.14, MET 6.13.
