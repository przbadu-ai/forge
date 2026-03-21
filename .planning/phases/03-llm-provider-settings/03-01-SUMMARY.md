---
phase: 03-llm-provider-settings
plan: "01"
subsystem: api
tags: [fastapi, sqlmodel, fernet, encryption, openai, crud, alembic]

# Dependency graph
requires:
  - phase: 02-authentication
    provides: get_current_user dependency, User model, auth endpoints
provides:
  - LLMProvider SQLModel with encrypted api_key storage
  - Fernet encrypt/decrypt helpers keyed to SECRET_KEY
  - CRUD + test-connection API endpoints under /settings/providers
  - Alembic migration 0003 for llm_provider table
affects: [03-02-settings-frontend, 03-03-settings-tests, 04-streaming-chat]

# Tech tracking
tech-stack:
  added: [cryptography, openai]
  patterns: [fernet-encryption-from-secret-key, json-string-column-pattern, single-default-enforcement]

key-files:
  created:
    - backend/app/core/encryption.py
    - backend/app/models/llm_provider.py
    - backend/app/api/v1/settings/__init__.py
    - backend/app/api/v1/settings/providers.py
    - backend/alembic/versions/0003_add_llm_provider_table.py
    - backend/app/tests/test_encryption.py
  modified:
    - backend/app/models/__init__.py
    - backend/app/api/v1/router.py
    - backend/pyproject.toml

key-decisions:
  - "SHA-256 key derivation from SECRET_KEY for Fernet (not PBKDF2) — simpler, fast, deterministic"
  - "Models stored as JSON string column (not normalized table) — always read as complete set"
  - "Router-level Depends(get_current_user) protects all settings endpoints"
  - "AsyncOpenAI client with 10s timeout for test-connection endpoint"

patterns-established:
  - "Fernet encryption: derive key from settings.secret_key via SHA-256 + base64url"
  - "Settings sub-router: app/api/v1/settings/ package with per-feature routers"
  - "JSON-in-text-column: serialize list[str] as JSON string, deserialize in API layer"

requirements-completed: [SET-01, SET-05]

# Metrics
duration: 4min
completed: 2026-03-21
---

# Phase 3 Plan 01: Settings Backend Summary

**LLM provider CRUD API with Fernet-encrypted API key storage, test-connection via AsyncOpenAI, and single-default enforcement**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-21T15:44:16Z
- **Completed:** 2026-03-21T15:48:07Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Fernet encryption helper with SHA-256 key derivation from SECRET_KEY
- LLMProvider model with encrypted api_key, JSON models column, is_default flag
- Full CRUD endpoints (GET/POST/PUT/DELETE) with api_key never exposed in responses
- Test-connection endpoint using AsyncOpenAI client with 10s timeout
- Alembic migration 0003 with clean up/down cycle
- 3 encryption roundtrip tests

## Task Commits

Each task was committed atomically:

1. **Task 1: LLMProvider model, encryption helper, and Alembic migration** - `7dc951b` (feat)
2. **Task 2: Provider CRUD endpoints and test-connection endpoint** - `5e3fbc1` (feat)

## Files Created/Modified
- `backend/app/core/encryption.py` - Fernet encrypt/decrypt helpers with SHA-256 key derivation
- `backend/app/models/llm_provider.py` - LLMProvider SQLModel table definition
- `backend/app/models/__init__.py` - Updated to export LLMProvider
- `backend/app/api/v1/settings/__init__.py` - Settings sub-package init
- `backend/app/api/v1/settings/providers.py` - CRUD + test-connection router with Pydantic schemas
- `backend/app/api/v1/router.py` - Wired providers router under /settings/providers
- `backend/alembic/versions/0003_add_llm_provider_table.py` - Migration for llm_provider table
- `backend/app/tests/test_encryption.py` - Encryption roundtrip and error tests
- `backend/pyproject.toml` - Added cryptography and openai dependencies

## Decisions Made
- Used SHA-256 key derivation (not PBKDF2) for Fernet key from SECRET_KEY — simpler, fast, sufficient for app-level encryption
- Models column stored as JSON text string — deserialized in API layer, not ORM
- Router-level `Depends(get_current_user)` instead of per-endpoint — all settings routes protected uniformly
- test-connection uses `asyncio.wait_for` with 10s timeout around `client.models.list()`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Stale forge.db blocking migration**
- **Found during:** Task 1 (Alembic migration generation)
- **Issue:** Existing forge.db had user table but no alembic_version tracking, preventing `alembic upgrade head`
- **Fix:** Removed stale forge.db and ran fresh migration cycle
- **Files modified:** None (runtime artifact)
- **Verification:** Migration up/down/up cycle completes cleanly

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Trivial — stale dev DB artifact, no code changes needed.

## Issues Encountered
None beyond the stale DB issue documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Provider CRUD API ready for frontend (03-02) to consume
- Provider data available for Phase 4 streaming chat to query default provider
- Test suite for provider endpoints planned in 03-03

---
*Phase: 03-llm-provider-settings*
*Completed: 2026-03-21*
