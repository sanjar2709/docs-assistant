"""Text embeddings, computed locally with fastembed (ONNX, no API key, no GPU needed).

The model is multilingual, so a question in Uzbek can find a paragraph in Russian or English.
It is loaded once per process and reused; the first run downloads it (~1 GB) into EMBEDDING_CACHE_DIR.
"""

import asyncio
from functools import lru_cache
from typing import Protocol

import numpy as np

from core import settings


class Embedder(Protocol):
    dimensions: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class FastEmbedEmbedder:
    def __init__(self, model_name: str, dimensions: int, cache_dir: str):
        from fastembed import TextEmbedding

        self.dimensions = dimensions
        self.model = TextEmbedding(model_name=model_name, cache_dir=cache_dir)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = np.array(list(self.model.embed(texts)))
        # Normalised vectors: cosine distance in pgvector then behaves the same for every model
        vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors.tolist()


@lru_cache
def get_embedder() -> Embedder:
    return FastEmbedEmbedder(settings.EMBEDDING_MODEL, settings.EMBEDDING_DIMENSIONS, str(settings.EMBEDDING_CACHE_DIR))


async def embed(texts: list[str]) -> list[list[float]]:
    # CPU-heavy, so it runs in a thread and doesn't block the event loop
    return await asyncio.to_thread(get_embedder().embed, texts)
