"""ChromaDB client — vector storage for RAG documents."""

import contextlib
import logging
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

logger = logging.getLogger(__name__)

# Module-level client singleton
_client: Any = None
_collection: Collection | None = None

COLLECTION_NAME = "forge_documents"


def get_chroma_client() -> Any:
    """Get or create the ChromaDB client singleton.

    Uses EphemeralClient for local development (single-process Uvicorn).
    For production multi-worker, switch to HttpClient pointing at a Chroma server.
    """
    global _client
    if _client is None:
        try:
            _client = chromadb.EphemeralClient()
            logger.info("ChromaDB ephemeral client initialized")
        except Exception:
            logger.exception("Failed to initialize ChromaDB client")
            raise
    return _client


def get_collection() -> Collection:
    """Get or create the forge_documents collection."""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB collection '%s' ready", COLLECTION_NAME)
    return _collection


def add_documents(
    file_id: int,
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    """Add document chunks with embeddings to ChromaDB."""
    collection = get_collection()
    ids = [f"file_{file_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas: list[dict[str, Any]] = [
        {"file_id": file_id, "chunk_index": i} for i in range(len(chunks))
    ]
    collection.add(
        ids=ids,
        embeddings=embeddings,  # type: ignore[arg-type]
        documents=chunks,
        metadatas=metadatas,  # type: ignore[arg-type]
    )


def query_documents(
    query_embedding: list[float],
    top_k: int = 5,
    file_ids: list[int] | None = None,
) -> dict[str, Any]:
    """Query ChromaDB for similar document chunks.

    Returns dict with keys: ids, documents, metadatas, distances.
    """
    collection = get_collection()
    where_filter: dict[str, Any] | None = None
    if file_ids:
        if len(file_ids) == 1:
            where_filter = {"file_id": file_ids[0]}
        else:
            where_filter = {"file_id": {"$in": file_ids}}

    results = collection.query(
        query_embeddings=[query_embedding],  # type: ignore[arg-type]
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    # Extract results safely
    raw_ids = results.get("ids") or [[]]
    raw_docs = results.get("documents") or [[]]
    raw_metas = results.get("metadatas") or [[]]
    raw_dists = results.get("distances") or [[]]

    return {
        "ids": raw_ids[0] if raw_ids else [],
        "documents": raw_docs[0] if raw_docs else [],
        "metadatas": raw_metas[0] if raw_metas else [],
        "distances": raw_dists[0] if raw_dists else [],
    }


def delete_file_documents(file_id: int) -> None:
    """Remove all chunks for a given file from ChromaDB."""
    collection = get_collection()
    # Get all IDs for this file
    results = collection.get(
        where={"file_id": file_id},
        include=[],
    )
    if results["ids"]:
        collection.delete(ids=results["ids"])


def reset_collection() -> None:
    """Reset the collection (for testing)."""
    global _collection
    client = get_chroma_client()
    with contextlib.suppress(Exception):
        client.delete_collection(COLLECTION_NAME)
    _collection = None
