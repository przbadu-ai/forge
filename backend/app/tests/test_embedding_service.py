"""Tests for the embedding service."""

import pytest

from app.services.embedding_service import _hash_embed, embed_texts


def test_hash_embed_returns_correct_dimension() -> None:
    result = _hash_embed("test text")
    assert len(result) == 384


def test_hash_embed_deterministic() -> None:
    a = _hash_embed("hello world")
    b = _hash_embed("hello world")
    assert a == b


def test_hash_embed_different_texts_produce_different_embeddings() -> None:
    a = _hash_embed("hello")
    b = _hash_embed("goodbye")
    assert a != b


def test_hash_embed_values_in_range() -> None:
    result = _hash_embed("test text")
    for val in result:
        assert -1.0 <= val <= 1.0


@pytest.mark.asyncio
async def test_embed_texts_fallback_without_config() -> None:
    """Without base_url and model, uses hash fallback."""
    results = await embed_texts(["hello world", "another text"])
    assert len(results) == 2
    assert len(results[0]) == 384
    assert len(results[1]) == 384


@pytest.mark.asyncio
async def test_embed_texts_fallback_same_text_same_result() -> None:
    """Hash-based embeddings should be deterministic."""
    a = await embed_texts(["test"])
    b = await embed_texts(["test"])
    assert a[0] == b[0]
