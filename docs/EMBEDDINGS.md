# Embedding Models

Addresses GitHub issue #8. Feeds phase 2, step 2 of
`docs/plans/02-ingestion-retrieval.md`.

Research date: 2026-11-19.

Method: vendor documentation and Hugging Face model cards, read on the
research date. Benchmark scores are the vendors' own figures, often
from different MTEB boards, so they are not directly comparable. The
final choice is made by Waypoint's own retrieval eval (recall@5, MRR),
as the phase 2 plan requires.

## What the task needs

- **Text:** English, technical and regulatory (TC AIM, CARs, TC study
  guides). Queries are short student questions. Documents are chunks
  of up to 800 tokens with a section heading path.
- **Asymmetric retrieval:** the model should treat queries and
  documents differently (input types or query instructions).
- **Size:** the TC AIM is about 0.44 million tokens; all sources are a
  few million. Embedding everything costs under USD 1 on any paid API
  below, so cost does not decide the choice.
- **Storage:** pgvector 0.8.7 indexes `vector` up to 2,000 dimensions
  and `halfvec` up to 4,000 (HNSW and IVFFlat). Models that allow a
  shorter output should use 1,024 dimensions so they fit `vector` and
  the comparison is fair.
- **Stability:** the same model must embed documents and queries. A
  model change means re-embedding every chunk.

## Top 3

| Rank | Model | Vector size | Open weight | Max input | Price per 1M tokens |
|---|---|---|---|---|---|
| 1 | Voyage AI `voyage-4-large` | 1,024 default; 256, 512, 2,048 | No (API) | 32,000 | USD 0.12; first 200M free |
| 2 | NVIDIA `Nemotron-3-Embed-1B` | 2,048; can be cut to 1,024 or 512 | Yes (OpenMDW-1.1) | 32,768 | None (runs locally) |
| 3 | Google `gemini-embedding-2` | 3,072 default; 128 to 3,072 | No (API) | 8,192 | USD 0.20 (free tier available) |

### 1. Voyage AI voyage-4-large: recommended first choice

- Built for retrieval and RAG. Voyage describes it as its "best
  general-purpose and multilingual retrieval quality" model.
- Separate `query` and `document` input types handle the asymmetric
  task directly.
- The default 1,024 dimensions fit a pgvector `vector` index.
- The 200 million free tokens cover the whole corpus and every
  re-embedding the eval needs, many times over.
- Anthropic offers no embedding model, and its documentation points to
  Voyage AI. That fits the planned Claude LLM.
- There is an open-weight sibling, `voyage-4-nano` (Hugging Face).
  Voyage states that 4-series embeddings are compatible with each
  other. That gives a path to local query embedding later, which the
  eval should confirm.
- Weakness: closed weights, and one more vendor and API key.

### 2. NVIDIA Nemotron-3-Embed-1B: best open-weight choice

- Released 2026-07-16 and built for retrieval. NVIDIA reports first
  place on the RTEB retrieval board (average NDCG@10 72.38) and 71.04
  on MMTEB retrieval. These are NVIDIA's own figures.
- About 1.1 billion parameters, small enough to run on a laptop.
  There are no API costs, no API key, and student queries never leave
  the server.
- Queries need a `query:` prefix and documents a `passage:` prefix.
  Sentence Transformers adds these automatically.
- Weaknesses: Waypoint has to host inference, which adds PyTorch and
  model weights to the API service, and Python 3.14 support for that
  stack must be checked. Its 2,048 dimensions need cutting to 1,024
  (and re-normalizing) to fit a `vector` index.
- Alternatives, if it does not work out:
  - `Qwen/Qwen3-Embedding-0.6B` (Apache 2.0, 1,024 dimensions). It is
    the most widely used open model, but weaker at retrieval (MTEB
    English v2 retrieval 61.83).
  - `microsoft/harrier-oss-v1-0.6b` (MIT, 1,024 dimensions,
    Multilingual MTEB v2 69.0). Its card has no release date and no
    shorter-output support.

### 3. Google gemini-embedding-2: strong API alternative

- Google's latest embedding model, listed as stable. It is
  multimodal, so figures and diagrams in the TC AIM could be embedded
  later.
- Output can be shortened (Matryoshka), and 1,536 or 768 dimensions
  fit pgvector. Google recommends 768, 1,536 or 3,072.
- Weaknesses:
  - The default 3,072 dimensions exceed the `vector` index limit, so
    the output must be shortened or stored as `halfvec`.
  - It has no `task_type` setting. Queries and documents are marked
    with text prefixes instead (`task: search result | query: ...`
    and `title: ... | text: ...`).
  - Free-tier data terms differ from the paid tier's. Use the paid
    tier for student queries.
- The price above comes from a summary of Google's pricing page, so
  confirm it before relying on it.

## Also considered

- **OpenAI `text-embedding-3-large`** (3,072 dimensions, can be
  shortened, USD 0.13 per 1M; `-3-small` is 1,536 dimensions at
  USD 0.02). It is reliable and widely used, but it dates from 2024.
  OpenAI's documentation lists no newer embedding model. It is a
  reasonable baseline if a fourth model is wanted in the eval.
- **Cohere `embed-v5.0-pro`** (2,048 dimensions default; 256 to 1,536
  also available; 128k context). It is new and capable, but its price
  and input types were not confirmed in this research.
- **Microsoft `harrier-oss-v1-27b`** (MIT, 5,376 dimensions) and
  **Qwen3-Embedding-8B** (Apache 2.0, 4,096 dimensions). They score
  highest on MTEB, but they are too large to host for this project.
- **NVIDIA `llama-embed-nemotron-8b`.** Non-commercial licence, 8B
  parameters, and superseded by Nemotron 3 Embed.

## Recommendation

Use the three models above in the phase 2 embedding comparison, all at
1,024 dimensions. Start with `voyage-4-large`, because it is the
simplest to run and its free allowance covers all testing. Keep it
unless the open-weight model matches it on recall@5 and MRR. If it
does, prefer the open-weight model, because it removes a vendor
dependency and keeps queries private. Record the results in
`docs/evals/`.

## Sources

- Voyage AI: https://docs.voyageai.com/docs/embeddings,
  https://docs.voyageai.com/docs/pricing
- Google: https://ai.google.dev/gemini-api/docs/embeddings,
  https://ai.google.dev/gemini-api/docs/pricing
- NVIDIA: https://huggingface.co/nvidia/Nemotron-3-Embed-1B-BF16,
  https://huggingface.co/nvidia/llama-embed-nemotron-8b
- Qwen: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B,
  https://huggingface.co/Qwen/Qwen3-Embedding-8B
- Microsoft: https://huggingface.co/microsoft/harrier-oss-v1-0.6b,
  https://huggingface.co/microsoft/harrier-oss-v1-27b
- OpenAI: https://developers.openai.com/api/docs/guides/embeddings,
  https://developers.openai.com/api/docs/pricing
- Cohere: https://docs.cohere.com/docs/cohere-embed
- pgvector: https://github.com/pgvector/pgvector
- Anthropic: https://platform.claude.com/docs/en/build-with-claude/embeddings
