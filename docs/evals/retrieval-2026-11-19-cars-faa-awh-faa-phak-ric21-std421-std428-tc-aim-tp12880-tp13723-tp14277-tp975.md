# Retrieval Eval: 2026-11-19

- Model: `voyage-4-large`, vector search only (cosine)
- Questions: 72 (`ingest/eval/retrieval.yaml`)
- Sources: cars, faa-awh, faa-phak, ric21, std421, std428, tc-aim, tp12880, tp13723, tp14277, tp975 (5098 chunks)

| Subject | Questions | Recall@5 | MRR@10 |
|---|---|---|---|
| pstar | 13 | 1.00 | 1.00 |
| air-law | 15 | 0.93 | 0.91 |
| navigation | 12 | 1.00 | 0.88 |
| meteorology | 12 | 0.92 | 0.76 |
| aeronautics | 13 | 1.00 | 0.86 |
| exam | 7 | 0.86 | 0.81 |
| **all** | **72** | **0.96** | **0.88** |

## Not in the top 5

- **air-law-06** (rank 8): Does ATC provide me any service at all in uncontrolled airspace? Expected RAC 2.8.7; top 3 were RAC 1.5.8, RAC 5.7, RAC 1.1.1.
- **meteorology-09** (not in top 10): Are winds aloft forecasts given relative to true or magnetic north? Expected MET 9.2; top 3 were AWH p.39, AWH p.38, PHAK p.323.
- **exam-02** (rank 6): I passed the written overall but failed the meteorology part. What happens now? Expected TP 12880 p.8; top 3 were TP 14277 5.0 Conduct of the Flight Test / 5.18 Partial Flight Test, CAR 401.16, CAR 401.17.
