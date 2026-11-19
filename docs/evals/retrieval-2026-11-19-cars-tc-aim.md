# Retrieval Eval: 2026-11-19

- Model: `voyage-4-large`, vector search only (cosine)
- Questions: 65 (`ingest/eval/retrieval.yaml`)
- Sources: cars, tc-aim (3020 chunks)

| Subject | Questions | Recall@5 | MRR@10 |
|---|---|---|---|
| pstar | 13 | 1.00 | 1.00 |
| air-law | 15 | 0.93 | 0.91 |
| navigation | 12 | 1.00 | 0.96 |
| meteorology | 12 | 1.00 | 0.89 |
| aeronautics | 13 | 1.00 | 0.91 |
| **all** | **65** | **0.98** | **0.93** |

## Not in the top 5

- **air-law-06** (rank 7): Does ATC provide me any service at all in uncontrolled airspace? Expected RAC 2.8.7; top 3 were RAC 1.5.8, RAC 5.7, RAC 1.1.1.
