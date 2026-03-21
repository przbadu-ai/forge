---
phase: 06-execution-trace-system
plan: 01
subsystem: backend-trace
tags: [trace, sse, backend, dataclass]
dependency_graph:
  requires: [04-01, 04-03]
  provides: [trace-emitter, trace-persistence, trace-sse]
  affects: [chat-api, message-model]
tech_stack:
  added: []
  patterns: [dataclass-service, sse-multiplexed-events, json-blob-storage]
key_files:
  created:
    - backend/app/services/__init__.py
    - backend/app/services/trace_emitter.py
    - backend/app/tests/test_trace_emitter.py
    - backend/alembic/versions/0006_add_trace_data_to_message.py
  modified:
    - backend/app/models/message.py
    - backend/app/api/v1/chat.py
decisions:
  - "TraceEvent as Python dataclass (not Pydantic) for internal service use"
  - "token_count stored in metadata dict on token_generation events"
  - "trace_data as nullable TEXT column for SQLite JSON blob storage"
metrics:
  duration: 3min
  completed: 2026-03-21
  tasks: 3
  files: 6
---

# Phase 6 Plan 1: Backend Execution Trace System Summary

TraceEmitter service with dataclass-based TraceEvent, JSON blob persistence on Message model, SSE trace event multiplexing alongside token stream.

## What Was Built

### TraceEmitter Service (`backend/app/services/trace_emitter.py`)
- **TraceEvent dataclass**: id (uuid4), type (run_start|run_end|token_generation|error), name, status (running|completed|error), started_at, completed_at, input, output, error, metadata
- **TraceEmitter class**: Collects events during a chat turn
  - `start_run(name)` -> TraceEvent (status=running)
  - `end_run(success)` -> TraceEvent (status=completed|error)
  - `emit_token_generation(token_count)` -> TraceEvent (metadata={token_count})
  - `emit_error(error_message)` -> TraceEvent (error field populated)
  - `to_json()` -> str (JSON array of event dicts)
  - `events` property -> list copy

### Message Model Update
- Added `trace_data: str | None` field (nullable TEXT column)
- Alembic migration `0006_add_trace_data` with batch_alter_table for SQLite

### SSE Stream Extension
- TraceEmitter created at start of each `_token_generator` call
- `run_start` trace event emitted before LLM call
- `token_generation` and `run_end` events emitted after stream completes
- `error` and `run_end(success=False)` events on exceptions
- All trace events sent as SSE: `data: {"type": "trace_event", "event": {...}}`
- `trace_data` saved to assistant message on completion (all code paths)

### API Response Updates
- `MessageRead` schema includes `trace_data: str | None`
- GET `/conversations/{id}/messages` returns trace_data per message
- GET `/conversations/{id}/export` includes parsed trace_data as JSON

## SSE Event Types (after this plan)
| Event Type | Payload | When |
|---|---|---|
| `trace_event` | `{type, event: TraceEvent}` | Before/after LLM call, on error |
| `token` | `{type, delta}` | Each token from LLM |
| `done` | `{type, message_id}` | Stream complete |
| `stopped` | `{type, message_id}` | Client disconnect or error with partial content |
| `error` | `{type, message}` | Error occurred |

## Migration
- Revision: `0006_add_trace_data`
- Down revision: `0005_chat_completions_fields`
- Applies and reverses cleanly

## Verification Results
- 10 TraceEmitter unit tests: all pass
- 11 chat endpoint tests: all pass
- 78 total tests: all pass
- ruff, black, mypy: all clean

## Deviations from Plan

None - plan executed exactly as written.

## Commits
| Hash | Description |
|---|---|
| a498afd | TraceEmitter service and TraceEvent dataclass (TDD) |
| 8a3311c | Message.trace_data field and Alembic migration |
| 33bf4b8 | SSE trace events, trace persistence, API updates |
