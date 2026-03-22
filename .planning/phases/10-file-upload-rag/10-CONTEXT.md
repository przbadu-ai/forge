# Phase 10: File Upload + RAG - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

File upload, chunking, embedding into ChromaDB, retrieval during chat, source attribution in responses, file management UI, and embedding/reranker settings.

</domain>

<decisions>
## Implementation Decisions

### File handling
- **D-01:** Files stored in ./uploads directory (not ./public)
- **D-02:** Served through controlled API endpoints (not static file serving)
- **D-03:** Supported formats: PDF, DOCX, TXT, MD
- **D-04:** File model: id, filename, original_name, content_type, size, status (pending/processing/ready/failed), chunk_count, created_at

### Chunking + Embedding
- **D-05:** Recursive character-based chunking (512 tokens, 50 token overlap)
- **D-06:** ChromaDB for vector storage (HTTP client mode)
- **D-07:** Single ChromaDB collection with metadata filtering by file_id
- **D-08:** Embedding via configured embedding model endpoint (OpenAI-compatible /v1/embeddings)

### Retrieval
- **D-09:** On chat, if files exist, embed query and retrieve top-K chunks (K=5)
- **D-10:** Inject retrieved chunks as context in system prompt
- **D-11:** Source attribution: track which chunks were used per message

### Source attribution UI
- **D-12:** Below assistant message, show collapsible "Sources" section
- **D-13:** Each source shows: file name, chunk preview (first ~100 chars), relevance score

### Settings
- **D-14:** Embedding model endpoint config in Settings (base_url, model_name)
- **D-15:** Reranker endpoint config (optional, for v1.x)

### Claude's Discretion
- Exact chunking implementation
- ChromaDB collection naming
- Retrieval query construction
- Source attribution UI design

</decisions>

<canonical_refs>
## Canonical References

- `PRD.md` §7.6 — Retrieval and file handling
- `.planning/research/PITFALLS.md` — ChromaDB HTTP mode, collection management
- `.planning/research/ARCHITECTURE.md` — File pipeline pattern

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Settings UI pattern (providers, MCP, skills) — reuse for embedding config
- TracePanel — will show retrieval trace events
- Orchestrator — retrieval can be a step before LLM call

### Integration Points
- File upload endpoint + management
- ChromaDB client initialization
- Retrieval injected into chat orchestration
- Source data attached to message response

</code_context>

<deferred>
## Deferred Ideas

- Semantic chunking — v2
- Graph RAG — v2
- Hybrid search — v2

</deferred>

---

*Phase: 10-file-upload-rag*
*Context gathered: 2026-03-21*
