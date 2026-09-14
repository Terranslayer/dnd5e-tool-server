"""Embedding providers. Tests use FakeEmbedder (deterministic, no network);
the server/scripts use OpenAIEmbedder (reads key from env via config)."""

from __future__ import annotations

import math
from typing import Protocol


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


def _normalize(v: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


class FakeEmbedder:
    """Deterministic test embedder: maps text to a fixed-dim normalized vector
    from its character codes. Same text -> same vector; different text differs."""

    def __init__(self, dim: int = 8):
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            v = [0.0] * self.dim
            for i, ch in enumerate(t):
                v[i % self.dim] += (ord(ch) % 17) / 17.0
            out.append(_normalize(v))
        return out


class OpenAIEmbedder:
    """OpenAI embeddings. Requires OPENAI_EMBEDDING_API_KEY in the environment
    (loaded from .env by config). Not unit-tested without a key."""

    def __init__(self, model: str | None = None, api_key: str | None = None):
        from openai import OpenAI
        from dnd5e_engine import config

        self.model = model or config.embedding_model()
        self.client = OpenAI(api_key=api_key or config.embedding_api_key())

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self.client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]
