"""Text embeddings, computed locally with fastembed (ONNX, no API key, no GPU needed).

multilingual-e5-large is trained on ~100 languages including Uzbek, so a question in Uzbek finds
a paragraph in English or Russian. A smaller model (paraphrase-multilingual-mpnet) missed Uzbek
questions in testing. It is loaded once per process; the first run downloads it (~2.2 GB).

E5 models expect "query: " in front of questions and "passage: " in front of document text.
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


async def embed_passages(texts: list[str]) -> list[list[float]]:
    # CPU-heavy, so it runs in a thread and doesn't block the event loop
    return await asyncio.to_thread(get_embedder().embed, [f'passage: {t}' for t in texts])


async def embed_query(text: str) -> list[float]:
    [vector] = await asyncio.to_thread(get_embedder().embed, [f'query: {text}'])
    return vector
