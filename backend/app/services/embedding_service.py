"""Embedding service — uses configured OpenAI-compatible /v1/embeddings endpoint."""

import hashlib
import struct
from typing import Any

import httpx


async def embed_texts(
    texts: list[str],
    base_url: str | None = None,
    model: str | None = None,
    api_key: str = "no-key",
) -> list[list[float]]:
    """Embed a list of texts into vectors.

    If base_url is configured, calls an OpenAI-compatible /v1/embeddings endpoint.
    Otherwise, falls back to a deterministic hash-based embedding for dev/testing.
    """
    if base_url and model:
        return await _remote_embed(texts, base_url, model, api_key)
    return [_hash_embed(text) for text in texts]


async def _remote_embed(
    texts: list[str],
    base_url: str,
    model: str,
    api_key: str,
) -> list[list[float]]:
    """Call OpenAI-compatible /v1/embeddings endpoint."""
    url = f"{base_url.rstrip('/')}/v1/embeddings"
    payload: dict[str, Any] = {
        "input": texts,
        "model": model,
    }
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    # OpenAI format: data[].embedding
    embeddings: list[list[float]] = []
    for item in sorted(data["data"], key=lambda x: x["index"]):
        embeddings.append(item["embedding"])
    return embeddings


def _hash_embed(text: str, dim: int = 384) -> list[float]:
    """Deterministic hash-based embedding for testing when no endpoint is configured.

    Produces a consistent vector of `dim` dimensions for a given text.
    NOT suitable for semantic similarity — only for testing the pipeline.
    """
    digest = hashlib.sha512(text.encode()).digest()
    # Extend hash to fill dimension
    extended = digest
    while len(extended) < dim * 4:
        extended += hashlib.sha512(extended).digest()

    values: list[float] = []
    for i in range(dim):
        raw = struct.unpack_from("<f", extended, i * 4)[0]
        # Normalize to [-1, 1] range
        values.append(max(-1.0, min(1.0, raw / 1e38)))
    return values
