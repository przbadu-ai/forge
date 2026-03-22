---
phase: 10-file-upload-rag
plan: 01
subsystem: api, database, ui
tags: [rag, source-citations, reranker, alembic, chromadb, sse]

# Dependency graph
requires:
  - phase: 10-file-upload-rag
    provides: "File upload, chunking, embedding, retrieval, source attribution UI, embedding/reranker settings"
provides:
  - "Source citation persistence across page refresh via Message.source_data"
  - "Optional reranker integration in retrieval pipeline"
  - "GET /messages returns sources field for messages with citations"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "JSON blob column for source citations (same pattern as trace_data)"
    - "Optional reranker step in retrieval pipeline with graceful fallback"

key-files:
  created:
    - backend/alembic/versions/0012_add_message_source_data.py
    - backend/app/tests/test_source_persistence.py
  modified:
    - backend/app/models/message.py
    - backend/app/api/v1/chat.py
    - backend/app/services/retrieval_service.py
    - frontend/src/hooks/useChat.ts
    - frontend/src/types/chat.ts

key-decisions:
  - "source_data stored as JSON text blob on Message (same pattern as trace_data)"
  - "Reranker calls POST {base_url}/rerank with OpenAI-compatible format"
  - "Reranker fallback returns original ChromaDB ranking on any error"

patterns-established:
  - "Source citation persistence: JSON blob column + deserialization on GET"
  - "Optional pipeline step: reranker called only when configured, graceful fallback"

requirements-completed: [RAG-01, RAG-02, RAG-03, RAG-04, RAG-05, SET-02, SET-03]

# Metrics
duration: 3min
completed: 2026-03-22
---

# Phase 10 Plan 01: Source Citation Persistence and Reranker Integration Summary

**Source citations persist to Message.source_data JSON column and survive page refresh; optional reranker re-ranks retrieval results when configured**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-22T06:48:41Z
- **Completed:** 2026-03-22T06:51:41Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- Source citations now persist across conversation resume via source_data column on Message
- GET /messages returns sources field, frontend restores them on page load
- Reranker optionally re-ranks ChromaDB results when reranker_base_url and reranker_model are configured
- Tests verify source round-trip, null sources, and reranker graceful fallback

## Task Commits

Each task was committed atomically:

1. **Task 1: Persist source citations to Message model and return on GET** - `fd8ebfe` (feat)
2. **Task 2: Wire optional reranker into retrieval pipeline** - `2ef2f1a` (feat)
3. **Task 3: Add test for source persistence across conversation resume** - `6b981eb` (test)

## Files Created/Modified
- `backend/app/models/message.py` - Added source_data column
- `backend/alembic/versions/0012_add_message_source_data.py` - Migration adding source_data to message table
- `backend/app/api/v1/chat.py` - Persist source_data on save, return sources on GET /messages, pass reranker settings to retrieve()
- `backend/app/services/retrieval_service.py` - Added rerank() function and reranker params to retrieve()
- `frontend/src/hooks/useChat.ts` - Restore sources from loaded messages on conversation resume
- `frontend/src/types/chat.ts` - Added sources field to Message interface
- `backend/app/tests/test_source_persistence.py` - Tests for source persistence and reranker fallback

## Decisions Made
- source_data stored as JSON text blob on Message model (same pattern as trace_data) for consistency
- Reranker uses POST {base_url}/rerank with model, query, documents, top_n format (OpenAI-compatible)
- Reranker gracefully falls back to original ChromaDB ranking on any error (timeout, connection refused, bad response)
- Migration numbered 0012 following the actual chain: 0010 -> 0bdc -> 37f1 -> 0011 -> 0012

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Migration revision chain correction**
- **Found during:** Task 1 (migration creation)
- **Issue:** Plan assumed down_revision would be "0010_add_embedding_settings" but actual head was "0011_add_skill_directories_and_skill_content" due to intermediate migrations
- **Fix:** Created migration 0012 with correct down_revision pointing to 0011
- **Files modified:** backend/alembic/versions/0012_add_message_source_data.py
- **Verification:** alembic upgrade head succeeds
- **Committed in:** fd8ebfe (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary correction to follow actual migration chain. No scope creep.

## Issues Encountered
- Pre-existing mypy errors in skills.py and mcp_servers.py (4 errors) unrelated to changes -- no new type errors introduced
- Pre-existing test failure in test_orchestration_integration.py (event loop closed) unrelated to changes -- 94/95 tests pass

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- RAG pipeline is now complete with source persistence and optional reranking
- All source citations survive page refresh
- Ready for any follow-up phases

---
*Phase: 10-file-upload-rag*
*Completed: 2026-03-22*
