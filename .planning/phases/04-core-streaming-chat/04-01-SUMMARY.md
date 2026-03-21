---
phase: 04-core-streaming-chat
plan: 01
subsystem: backend-chat
tags: [chat, sse, streaming, crud, models]
dependency_graph:
  requires: [llm-providers, encryption, auth]
  provides: [conversation-model, message-model, chat-crud-api, sse-streaming-endpoint]
  affects: [frontend-chat]
tech_stack:
  added: []
  patterns: [StreamingResponse-SSE, AsyncOpenAI-stream, SQLModel-where-type-ignore]
key_files:
  created:
    - backend/app/models/conversation.py
    - backend/app/models/message.py
    - backend/app/api/v1/chat.py
    - backend/alembic/versions/0004_add_conversation_message_tables.py
  modified:
    - backend/app/models/__init__.py
    - backend/app/api/v1/router.py
decisions:
  - Used StreamingResponse (not EventSourceResponse) since FastAPI 0.135 does not include native EventSourceResponse and sse-starlette not in dependencies
  - Used client.chat.completions.create(stream=True) instead of .stream() context manager because text_stream attribute not available in openai SDK version
  - SQLAlchemy Column[Any] aliases for order_by (.desc()/.asc()) to satisfy mypy strict mode
metrics:
  duration: 6min
  completed: 2026-03-21
---

# Phase 4 Plan 1: Backend Chat + SSE Streaming Summary

Conversation and Message models with Alembic migration, conversation CRUD at /api/v1/chat/conversations, and SSE streaming endpoint at /api/v1/chat/{id}/stream using AsyncOpenAI with token-by-token streaming.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Conversation and Message models + migration | 738ccb4 | conversation.py, message.py, 0004 migration |
| 2 | CRUD endpoints + SSE streaming | ed1fc1b | chat.py, router.py |

## Models Created

**Conversation** (`conversation` table):
- id (PK), title (max 200, default "New Conversation"), user_id (FK to user, indexed), created_at, updated_at

**Message** (`message` table):
- id (PK), conversation_id (FK to conversation, indexed), role (max 20: user/assistant/system), content, created_at

## Endpoints Created

| Method | Path | Behavior |
|--------|------|----------|
| GET | /api/v1/chat/conversations | List user's conversations, ordered by updated_at DESC |
| POST | /api/v1/chat/conversations | Create new conversation |
| GET | /api/v1/chat/conversations/{id}/messages | Get all messages for conversation |
| PUT | /api/v1/chat/conversations/{id} | Rename conversation |
| DELETE | /api/v1/chat/conversations/{id} | Delete conversation + messages |
| POST | /api/v1/chat/{id}/stream | SSE streaming: persist user msg, stream LLM tokens, persist assistant msg |

## SSE Event Format

All events use `data: {json}\n\n` format:
- `{"type": "token", "delta": "..."}` - content delta
- `{"type": "done", "message_id": N}` - stream complete
- `{"type": "error", "message": "..."}` - error occurred

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] EventSourceResponse not available in FastAPI 0.135**
- **Found during:** Task 2
- **Issue:** Plan specified `from fastapi.responses import EventSourceResponse` but it does not exist in FastAPI 0.135
- **Fix:** Used `starlette.responses.StreamingResponse` with `media_type="text/event-stream"` and manual SSE formatting
- **Files modified:** backend/app/api/v1/chat.py

**2. [Rule 3 - Blocking] openai SDK .stream() context manager lacks text_stream**
- **Found during:** Task 2
- **Issue:** `AsyncChatCompletionStream` in the installed openai SDK version does not have `text_stream` attribute
- **Fix:** Used `client.chat.completions.create(stream=True)` with async iteration over chunks, extracting `chunk.choices[0].delta.content`
- **Files modified:** backend/app/api/v1/chat.py

**3. [Rule 1 - Bug] mypy strict mode type errors on SQLModel field ordering**
- **Found during:** Task 2
- **Issue:** `Conversation.updated_at.desc()` resolves to `datetime.desc()` for mypy, which doesn't exist
- **Fix:** Created `Column[Any]` aliases (`_conv_updated_at`, `_msg_created_at`) with type: ignore[assignment] for ordering
- **Files modified:** backend/app/api/v1/chat.py

## Verification

- All new model imports work
- Migration applies cleanly (conversation and message tables created)
- Ruff, black, mypy all pass on new/modified files
- Full test suite: 41 tests pass (no regressions)

## Self-Check: PASSED

All 4 created files exist. Both task commits (738ccb4, ed1fc1b) verified in git log.
