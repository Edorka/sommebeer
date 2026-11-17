"""Local MiniLM embeddings — shared by the backfill script and the agent."""

from __future__ import annotations

from functools import lru_cache

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBED_MODEL)


def embed(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts, L2-normalised (cosine == dot product)."""
    return _model().encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()


def embed_one(text: str) -> list[float]:
    return embed([text])[0]
