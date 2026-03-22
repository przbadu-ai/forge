# Milestones

## v1.0 MVP (Shipped: 2026-03-22)

**Phases completed:** 11 phases, 11 plans, 39 tasks

**Key accomplishments:**

- FastAPI app factory with uv, pydantic-settings config, health endpoint, and full quality toolchain (ruff, black, mypy, pytest) passing with zero violations
- Async SQLAlchemy engine with SQLite WAL pragmas, session factory, and Alembic batch-mode migrations
- Next.js 16 app with Tailwind CSS v4, shadcn/ui, Vitest, and Prettier configured for Forge frontend
- 1. [Rule 1 - Bug] pwdlib PasswordHash.recommended() requires argon2
- 1. [Rule 3 - Blocking] Route conflict between app/page.tsx and (protected)/page.tsx
- Backend integration tests (6), Vitest component tests (5), and Playwright E2E tests (6) covering full auth lifecycle, login UI behavior, and end-to-end auth flow
- LLM provider CRUD API with Fernet-encrypted API key storage, test-connection via AsyncOpenAI, and single-default enforcement
- 10 backend integration tests and 8 frontend component tests covering provider API CRUD, encryption, auth, and theme switching
- Conversation
- Backend chat CRUD integration tests (11) and frontend component tests (17) covering conversations, markdown XSS safety, and streaming endpoint verification
- Full generation control with system prompts, stop/regenerate, temperature/max_tokens settings, JSON export, and conversation search -- all wired end-to-end across 3 backend endpoints, 1 settings endpoint, DB migration, and matching frontend UI
- Full trace pipeline test coverage: 10 unit tests, 7 backend integration tests (mocked LLM SSE), 8 frontend component tests for TracePanel
- 1. [Rule 1 - Bug] Fixed ruff lint: import ordering, unused imports, raise-from, asyncio.TimeoutError alias
- Validated skills feature end-to-end: Skill model, SkillExecutor with trace emission, API endpoints, frontend SkillsSection with toggle switches, and seed data -- all 14 tests pass
- Source citations persist to Message.source_data JSON column and survive page refresh; optional reranker re-ranks retrieval results when configured
- Playwright E2E CI job with full quality gate verification -- ruff, mypy, eslint, tsc, prettier, vitest, and next build all passing
- 1. [Rule 1 - Bug] Fixed pre-existing mypy errors in test_orchestrator.py

---
