# Phase 1: Infrastructure Foundation - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Project scaffolding with both frontend (Next.js) and backend (FastAPI) servers, async database engine with SQLite WAL mode, Alembic migrations with batch mode, and dev tooling (Makefile, linting, testing skeletons). No feature code — just the foundation that all subsequent phases build on.

</domain>

<decisions>
## Implementation Decisions

### Backend scaffold
- **D-01:** Python 3.12 target (not 3.13 — ChromaDB/sentence-transformers compatibility)
- **D-02:** Use `uv` for Python package management (faster than pip/poetry)
- **D-03:** FastAPI app factory pattern with `create_app()` function
- **D-04:** SQLite with WAL mode + busy_timeout=5000ms enabled at engine creation
- **D-05:** SQLModel for models (Pydantic v2 + SQLAlchemy 2.0 under the hood)
- **D-06:** Alembic configured with batch mode for SQLite ALTER TABLE support
- **D-07:** Async SQLAlchemy engine with `aiosqlite` driver
- **D-08:** Ruff for linting + Black for formatting + mypy for type checking
- **D-09:** pytest + pytest-asyncio + httpx for testing
- **D-10:** Use `pwdlib[bcrypt]` for password hashing (not passlib — deprecated)

### Frontend scaffold
- **D-11:** Next.js 15+ App Router with TypeScript strict mode
- **D-12:** shadcn/ui initialized with default theme
- **D-13:** Tailwind CSS 4
- **D-14:** ESLint + Prettier for linting/formatting
- **D-15:** Vitest + @testing-library/react for unit/component tests
- **D-16:** Playwright installed but E2E tests deferred to later phases

### Project structure
- **D-17:** Monorepo with `frontend/` and `backend/` top-level directories
- **D-18:** `Makefile` as the single entry point for dev commands (`make dev`, `make test`, `make lint`)
- **D-19:** `make dev` starts both servers concurrently (Next.js on 3000, FastAPI on 8000)
- **D-20:** `.env.example` with documented configuration values
- **D-21:** Backend serves API at `/api/v1/` prefix

### Claude's Discretion
- Exact pyproject.toml dependency versions (use latest stable)
- Vitest config details
- Makefile implementation (simple shell commands vs task runner)
- Directory structure within frontend/ and backend/

</decisions>

<specifics>
## Specific Ideas

- PRD Section 14 references `.env.example` as the configuration contract
- SSE streaming will connect browser directly to FastAPI (not through Next.js proxy) — set up CORS accordingly
- Backend at port 8000, frontend at port 3000

</specifics>

<canonical_refs>
## Canonical References

### Stack mandates
- `PRD.md` §1.1 — Frontend stack mandate (Next.js, shadcn/ui, Tailwind)
- `PRD.md` §1.2 — Backend stack mandate (Python, FastAPI, SQLite, ChromaDB)
- `PRD.md` §1.3 — Testing stack mandate (Vitest, pytest, Playwright)
- `PRD.md` §14 — Environment configuration note (.env.example contract)

### Research findings
- `.planning/research/STACK.md` — Verified package versions, SSE patterns, auth library choice
- `.planning/research/PITFALLS.md` — SQLite WAL requirement, Alembic batch mode, SSE compression disable

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project

### Established Patterns
- None — this phase establishes them

### Integration Points
- Backend CORS must allow frontend origin (localhost:3000) for direct SSE streaming in later phases

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-infrastructure-foundation*
*Context gathered: 2026-03-21*
