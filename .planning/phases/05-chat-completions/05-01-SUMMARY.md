---
phase: 05-chat-completions
plan: 01
subsystem: api, chat, settings, ui
tags: [openai, sse, streaming, system-prompt, temperature, max-tokens, export, search, regenerate, abort-controller]

# Dependency graph
requires:
  - phase: 04-streaming-chat
    provides: SSE streaming endpoint, Conversation/Message models, useChat hook, ChatPanel, ChatInput
  - phase: 03-settings
    provides: LLM provider CRUD, encryption, settings page structure
provides:
  - AppSettings model with global system_prompt, temperature, max_tokens
  - Per-conversation system_prompt, temperature, max_tokens on Conversation model
  - System prompt injection pattern (prepended as role=system in LLM call)
  - Stop generation with partial content persistence via AbortController + stopped SSE event
  - Regenerate endpoint (DELETE last assistant message + re-stream)
  - JSON export endpoint with Content-Disposition header
  - Conversation search via LIKE query on message content
  - General Settings UI (system prompt textarea, temperature slider, max_tokens input)
  - Search input in ConversationList with debounced API calls
  - Export button in ChatPanel header
  - Regenerate button below last assistant message
affects: [06-traces, 07-orchestrator, 08-mcp]

# Tech tracking
tech-stack:
  added: []
  patterns: [system-prompt-injection, abort-partial-save, settings-upsert, debounced-search]

key-files:
  created:
    - backend/app/models/settings.py
    - backend/alembic/versions/0005_chat_completions_fields.py
    - backend/app/api/v1/settings/general.py
    - backend/app/tests/test_settings_general.py
    - backend/app/tests/test_chat_completions.py
    - frontend/src/lib/settings-api.ts
    - frontend/src/hooks/useGeneralSettings.ts
    - frontend/src/components/settings/GeneralSection.tsx
    - frontend/src/__tests__/chat-input-streaming.test.tsx
    - frontend/src/__tests__/general-section.test.tsx
  modified:
    - backend/app/models/conversation.py
    - backend/app/api/v1/chat.py
    - backend/app/api/v1/router.py
    - backend/app/models/__init__.py
    - frontend/src/types/chat.ts
    - frontend/src/lib/chat-api.ts
    - frontend/src/hooks/useChat.ts
    - frontend/src/components/chat/ChatInput.tsx
    - frontend/src/components/chat/ChatPanel.tsx
    - frontend/src/components/chat/ConversationList.tsx
    - frontend/src/app/(protected)/settings/page.tsx

key-decisions:
  - "System prompt prepended as role=system message in LLM call, not persisted as Message row"
  - "Per-conversation settings override global via null-check cascade"
  - "Stop saves partial content via stopped SSE event on CancelledError/GeneratorExit"
  - "Regenerate = DELETE last assistant message on backend, re-stream from last user message on frontend"
  - "Search uses SQLite LIKE with DISTINCT join on Message content"
  - "AppSettings is single-row upsert pattern (id=1)"

patterns-established:
  - "System prompt injection: conversation.system_prompt or app_settings.system_prompt prepended to openai_messages"
  - "Abort + partial save: CancelledError/GeneratorExit in _token_generator persists partial content and yields stopped event"
  - "Settings upsert: single-row AppSettings with create-if-absent pattern in PUT endpoint"
  - "Debounced search: 300ms useEffect timer calling search API when query >= 2 chars"

requirements-completed: [CHAT-08, CHAT-09, CHAT-10, CHAT-11, CHAT-12, SET-07, UX-02]

# Metrics
duration: 2min
completed: 2026-03-22
---

# Phase 5 Plan 1: Chat Completions Summary

**Full generation control with system prompts, stop/regenerate, temperature/max_tokens settings, JSON export, and conversation search -- all wired end-to-end across 3 backend endpoints, 1 settings endpoint, DB migration, and matching frontend UI**

## Performance

- **Duration:** 2 min (verification-only -- code was pre-implemented across prior phases)
- **Started:** 2026-03-22T04:08:07Z
- **Completed:** 2026-03-22T04:10:11Z
- **Tasks:** 4
- **Files modified:** 1 (test fixture fix only; all implementation was pre-existing)

## Accomplishments
- Verified all 4 tasks' implementation already exists and passes all tests
- Backend: 5 settings general tests pass, 11 chat completions tests pass (169 total backend tests pass)
- Frontend: 8 component/hook tests pass (ChatInput streaming toggle, GeneralSection fields)
- TypeScript compiles with zero errors
- Ruff passes on all phase 5 files
- Migration round-trips cleanly (downgrade + upgrade)
- Fixed test isolation issue in test_settings_general.py (cleanup fixture)

## Task Commits

Each task was committed atomically:

1. **Task 1: Backend -- DB migration + model extensions + AppSettings CRUD** - `30ecf0c` (fix: added cleanup fixture to test)
2. **Task 2: Backend -- Extend streaming + regenerate + export + search endpoints** - pre-existing (verified passing)
3. **Task 3: Frontend -- Stop/regenerate/export in chat + system prompt + model params in settings + search in sidebar** - pre-existing (verified passing)
4. **Task 4: Tests -- backend completions + frontend Vitest component tests** - pre-existing (verified passing)

**Plan metadata:** (pending)

## Files Created/Modified

### Backend
- `backend/app/models/settings.py` - AppSettings model with system_prompt, temperature, max_tokens, embedding, reranker, web search fields
- `backend/app/models/conversation.py` - Conversation model extended with system_prompt, temperature, max_tokens
- `backend/alembic/versions/0005_chat_completions_fields.py` - Migration adding conversation columns + app_settings table
- `backend/app/api/v1/settings/general.py` - GET/PUT /settings/general endpoints with validation
- `backend/app/api/v1/chat.py` - Extended with regenerate, export, search endpoints; system prompt injection in streaming
- `backend/app/api/v1/router.py` - Registered general settings router
- `backend/app/tests/test_settings_general.py` - 5 tests for settings CRUD + validation
- `backend/app/tests/test_chat_completions.py` - 11 tests for regenerate, export, search, CRUD

### Frontend
- `frontend/src/types/chat.ts` - Added GeneralSettings type, SSEStoppedEvent, conversation fields
- `frontend/src/lib/chat-api.ts` - Added regenerate, export, search API functions
- `frontend/src/lib/settings-api.ts` - GET/PUT general settings API functions
- `frontend/src/hooks/useChat.ts` - Added stopGeneration(), regenerate(), stopped event handling
- `frontend/src/hooks/useGeneralSettings.ts` - TanStack Query hook for general settings
- `frontend/src/components/chat/ChatInput.tsx` - Stop/Send button toggle during streaming
- `frontend/src/components/chat/ChatPanel.tsx` - Export button, Regenerate button, wired stop/regenerate
- `frontend/src/components/chat/ConversationList.tsx` - Search input with debounced API calls
- `frontend/src/components/settings/GeneralSection.tsx` - System prompt textarea, temperature slider, max_tokens input
- `frontend/src/app/(protected)/settings/page.tsx` - General tab in settings page

### Tests
- `frontend/src/__tests__/chat-input-streaming.test.tsx` - 4 tests for Send/Stop button toggle
- `frontend/src/__tests__/general-section.test.tsx` - 4 tests for GeneralSection rendering

## Decisions Made
- System prompt prepended as role=system message in LLM call, not persisted as a Message row (per D-03)
- Per-conversation settings override global via null-check cascade (per D-07, D-08)
- Stop saves partial content via stopped SSE event on CancelledError/GeneratorExit (per D-04, D-06)
- Regenerate = DELETE last assistant message on backend, re-stream from last user message on frontend (per D-05)
- Search uses SQLite LIKE with DISTINCT join on Message content (per D-11, D-12)
- AppSettings is single-row upsert pattern (id=1)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added cleanup fixture to test_settings_general.py**
- **Found during:** Task 1 verification
- **Issue:** test_get_defaults_when_empty failed because prior test runs left data in app_settings table
- **Fix:** Added autouse fixture that deletes all AppSettings rows before each test
- **Files modified:** backend/app/tests/test_settings_general.py
- **Verification:** All 5 settings tests now pass reliably
- **Committed in:** 30ecf0c

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Trivial test isolation fix. No scope creep.

## Issues Encountered
- All implementation code was already present from prior phase executions and quick tasks. This execution was verification-focused.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Chat completions features fully operational: system prompts, stop/regenerate, export, search, temperature/max_tokens
- Ready for Phase 6 (traces) to build on the trace_data field and TraceEmitter patterns established here
- Ready for Phase 7 (orchestrator) to use the system prompt injection and model parameter patterns

## Self-Check: PASSED

All key files verified present. Commit 30ecf0c verified in git log.

---
*Phase: 05-chat-completions*
*Completed: 2026-03-22*
