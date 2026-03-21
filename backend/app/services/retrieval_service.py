"""Retrieval service — embed query, search ChromaDB, return formatted results."""

import logging
from typing import Any

from app.core.chroma_client import query_documents
from app.services.embedding_service import embed_texts

logger = logging.getLogger(__name__)


async def retrieve(
    query: str,
    top_k: int = 5,
    file_ids: list[int] | None = None,
    embedding_base_url: str | None = None,
    embedding_model: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve relevant document chunks for a query.

    Returns a list of dicts with keys: file_id, chunk_text, score, chunk_index.
    """
    # Embed the query
    embeddings = await embed_texts(
        [query],
        base_url=embedding_base_url,
        model=embedding_model,
    )
    query_embedding = embeddings[0]

    # Search ChromaDB
    results = query_documents(
        query_embedding=query_embedding,
        top_k=top_k,
        file_ids=file_ids,
    )

    # Format results
    sources: list[dict[str, Any]] = []
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])
    distances = results.get("distances", [])

    for i in range(len(documents)):
        doc = documents[i] if i < len(documents) else ""
        meta = metadatas[i] if i < len(metadatas) else {}
        distance = distances[i] if i < len(distances) else 1.0

        # ChromaDB cosine distance: 0 = identical, 2 = opposite
        # Convert to similarity score: 1.0 = identical, 0.0 = orthogonal
        score = max(0.0, 1.0 - float(distance))

        sources.append(
            {
                "file_id": meta.get("file_id"),
                "chunk_text": doc,
                "score": round(score, 4),
                "chunk_index": meta.get("chunk_index", 0),
            }
        )

    return sources


def format_context_for_prompt(sources: list[dict[str, Any]], file_names: dict[int, str]) -> str:
    """Format retrieved sources into a context block for the system prompt."""
    if not sources:
        return ""

    lines = ["--- Retrieved Document Context ---"]
    for i, src in enumerate(sources, 1):
        file_id = src.get("file_id")
        name = file_names.get(file_id, f"File {file_id}") if file_id else "Unknown"
        text = src.get("chunk_text", "")
        score = src.get("score", 0.0)
        lines.append(f"\n[Source {i}] {name} (relevance: {score:.2f})")
        lines.append(text)

    lines.append("\n--- End of Retrieved Context ---")
    lines.append(
        "\nUse the above context to answer the user's question. "
        "Cite sources by their file name when referencing specific information."
    )
    return "\n".join(lines)
