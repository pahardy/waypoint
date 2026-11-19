"""Embed text with Voyage AI (see docs/EMBEDDINGS.md).

Documents and queries must use the same model and size as the chunk table.
"""

from typing import Literal

import voyageai

MODEL = "voyage-4-large"
DIMENSIONS = 1024
BATCH_SIZE = 64

InputType = Literal["document", "query"]


def embed(texts: list[str], input_type: InputType) -> list[list[float]]:
    """Embed texts in batches. Reads VOYAGE_API_KEY from the environment.

    Batches of 64 chunks of at most 800 tokens stay well under the
    120,000-token request limit. Over-length input raises instead of being
    silently truncated.
    """
    client = voyageai.Client()
    vectors: list[list[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        result = client.embed(
            texts[start : start + BATCH_SIZE],
            model=MODEL,
            input_type=input_type,
            output_dimension=DIMENSIONS,
            truncation=False,
        )
        vectors.extend(result.embeddings)
    return vectors
