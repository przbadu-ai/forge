"""Tests for ChromaDB client operations."""

import pytest

from app.core.chroma_client import (
    add_documents,
    delete_file_documents,
    query_documents,
    reset_collection,
)
from app.services.embedding_service import _hash_embed


@pytest.fixture(autouse=True)
def clean_collection() -> None:
    """Reset ChromaDB collection before each test."""
    reset_collection()


def test_add_and_query_documents() -> None:
    """Add documents and query to find them."""
    chunks = ["The sky is blue.", "Water is wet."]
    embeddings = [_hash_embed(c) for c in chunks]
    add_documents(file_id=1, chunks=chunks, embeddings=embeddings)

    # Query with one of the chunk texts
    query_emb = _hash_embed("The sky is blue.")
    results = query_documents(query_embedding=query_emb, top_k=2)

    assert len(results["documents"]) > 0
    assert "The sky is blue." in results["documents"]


def test_query_with_file_id_filter() -> None:
    """Query with file_id filter returns only matching documents."""
    chunks_1 = ["File one content."]
    chunks_2 = ["File two content."]
    add_documents(file_id=10, chunks=chunks_1, embeddings=[_hash_embed(c) for c in chunks_1])
    add_documents(file_id=20, chunks=chunks_2, embeddings=[_hash_embed(c) for c in chunks_2])

    # Query filtering for file 10 only
    query_emb = _hash_embed("content")
    results = query_documents(query_embedding=query_emb, top_k=5, file_ids=[10])

    # All returned docs should belong to file_id 10
    for meta in results["metadatas"]:
        assert meta["file_id"] == 10


def test_delete_file_documents() -> None:
    """Deleting file documents removes them from ChromaDB."""
    chunks = ["Delete me please."]
    embeddings = [_hash_embed(c) for c in chunks]
    add_documents(file_id=99, chunks=chunks, embeddings=embeddings)

    # Verify it's there
    query_emb = _hash_embed("Delete me please.")
    results = query_documents(query_embedding=query_emb, top_k=1)
    assert len(results["documents"]) > 0

    # Delete
    delete_file_documents(file_id=99)

    # Verify it's gone
    results_after = query_documents(query_embedding=query_emb, top_k=1)
    # Should either be empty or not contain the deleted doc
    if results_after["metadatas"]:
        for meta in results_after["metadatas"]:
            assert meta.get("file_id") != 99


def test_query_empty_collection() -> None:
    """Querying an empty collection returns empty results."""
    query_emb = _hash_embed("anything")
    results = query_documents(query_embedding=query_emb, top_k=5)
    assert results["documents"] == []
