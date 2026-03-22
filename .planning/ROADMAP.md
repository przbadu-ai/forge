# Roadmap: Forge

## Overview

Forge is built in eleven dependency-ordered phases, each delivering a coherent slice of the product. The sequence follows a strict dependency graph: infrastructure and correctness first, then authentication, then streaming chat, then the execution trace system (Forge's primary differentiator), then the agentic orchestration loop, then tool integrations (MCP, Skills), then retrieval (RAG), then settings completion and health diagnostics, and finally a quality gate that validates everything end-to-end. Every v1 requirement maps to exactly one phase. No phase begins until its predecessor delivers working, tested software.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Infrastructure Foundation** - Project scaffolding, async DB engine, SQLite WAL+WAL, Alembic batch migrations, dev tooling (completed 2026-03-21)
- [x] **Phase 2: Authentication** - Single-user login, JWT sessions, protected API routes (completed 2026-03-21)
- [x] **Phase 3: LLM Provider Settings** - LLM provider/model configuration, test-connection, theme (completed 2026-03-21)
- [x] **Phase 4: Core Streaming Chat** - Streaming SSE chat, conversation CRUD, markdown rendering (completed 2026-03-21)
- [x] **Phase 5: Chat Completions** - System prompts, stop generation, regenerate, export, conversation search, model parameters (completed 2026-03-22)
- [x] **Phase 6: Execution Trace System** - TraceEmitter, trace UI, persistence, replay on resume (completed 2026-03-21)
- [ ] **Phase 7: Orchestration Loop** - Custom agentic loop, executor interfaces, timeout/retry, run state
- [ ] **Phase 8: MCP Integration** - MCP server registration, process manager, tool invocation, trace visibility
- [x] **Phase 9: Skills Integration** - Skills settings, skill execution, trace visibility, persistence (completed 2026-03-22)
- [x] **Phase 10: File Upload + RAG** - File upload, chunking, embedding, ChromaDB retrieval, source attribution (completed 2026-03-22)
- [ ] **Phase 11: Settings Completion + Quality Gate** - Embedding/reranker/web search settings, health diagnostics, full test coverage, CI

## Phase Details

### Phase 1: Infrastructure Foundation
**Goal**: The project skeleton is correct, deterministic, and ready for feature work with no latent infrastructure bugs
**Depends on**: Nothing (first phase)
**Requirements**: TEST-04
**Success Criteria** (what must be TRUE):
  1. `make dev` starts both frontend (Next.js) and backend (FastAPI) servers from a single command
  2. SQLite database initializes with WAL mode and busy timeout; no "database is locked" errors under concurrent async requests
  3. Alembic migrations run forward and backward cleanly with batch mode enabled; `alembic upgrade head` completes without error
  4. Ruff, Black, ESLint, Prettier, mypy, and TypeScript strict mode all pass with zero violations on the starter codebase
  5. Vitest and pytest execute with zero failures on skeleton test suites
**Plans:** 3 plans

Plans:
- [x] 01-01: Backend project scaffold (FastAPI app factory, uv environment, pyproject.toml, ruff/black/mypy config)
- [x] 01-02: Database layer (SQLite engine with WAL+busy_timeout, SQLModel base models, Alembic with batch mode)
- [x] 01-03: Frontend project scaffold (Next.js 16 App Router, TypeScript strict, shadcn/ui, Tailwind, ESLint, Prettier, Vitest)
- [x] 01-04: Dev tooling (Makefile/scripts for dev/test/lint, CI skeleton, directory structure)

### Phase 2: Authentication
**Goal**: Users can securely access Forge and all API routes are protected
**Depends on**: Phase 1
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04
**Success Criteria** (what must be TRUE):
  1. User can log in with username and password at the login page
  2. User remains logged in after browser refresh without re-entering credentials
  3. User can log out from any page and is redirected to login
  4. Navigating to any page while unauthenticated redirects to login
  5. All FastAPI API routes return 401 without a valid session token
**Plans:** 3 plans

Plans:
- [x] 02-01: Backend auth (pwdlib bcrypt password hash, JWT token generation/validation, auth middleware, /auth endpoints)
- [x] 02-02: Frontend auth (login page, session storage, auth context, route protection, logout)
- [x] 02-03: Auth tests (pytest auth unit + integration, Playwright E2E login/logout/protected-route)

### Phase 3: LLM Provider Settings
**Goal**: Users can configure at least one LLM provider and verify connectivity before chatting
**Depends on**: Phase 2
**Requirements**: SET-01, SET-05, UX-01
**Success Criteria** (what must be TRUE):
  1. User can add an LLM provider with a base URL, API key, and one or more model names
  2. User can click "Test Connection" and see a success or error response within a few seconds
  3. User can switch between Light, Dark, and System themes and the preference persists across page refresh
  4. Configured LLM providers and models are saved to the database and survive server restart
**Plans:** 1/1 plans complete

Plans:
- [x] 03-01: Settings backend (LLM provider CRUD endpoints, test-connection endpoint, encrypted API key storage with SecretStr)
- [ ] 03-02: Settings frontend (Settings page shell, LLM Providers section, test-connection button, theme switcher with next-themes)
- [x] 03-03: Settings tests (provider CRUD, test-connection, theme persistence)

### Phase 4: Core Streaming Chat
**Goal**: Users can have a complete streaming conversation with an LLM and manage their conversation history
**Depends on**: Phase 3
**Requirements**: CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05, CHAT-06, CHAT-07
**Success Criteria** (what must be TRUE):
  1. User can start a new conversation and receive streaming tokens from the configured LLM in real time
  2. Assistant messages render markdown with syntax-highlighted code blocks
  3. Conversations appear in the sidebar list immediately after creation
  4. User can click a previous conversation in the sidebar and continue it; messages load correctly
  5. User can rename a conversation inline and the new name persists
  6. User can delete a conversation and it is removed from the sidebar
**Plans:** 2/1 plans complete

Plans:
- [x] 04-01-PLAN.md — Backend chat models + CRUD + SSE streaming (Wave 1)
- [ ] 04-02-PLAN.md — Frontend chat layout + streaming consumer + markdown rendering (Wave 2)
- [x] 04-03-PLAN.md — Chat tests: backend pytest + frontend Vitest + Playwright E2E (Wave 3)

### Phase 5: Chat Completions
**Goal**: Users have full control over chat behavior including system prompts, generation control, and data export
**Depends on**: Phase 4
**Requirements**: CHAT-08, CHAT-09, CHAT-10, CHAT-11, CHAT-12, SET-07, UX-02
**Success Criteria** (what must be TRUE):
  1. User can set a global system prompt in Settings that applies to all new conversations
  2. User can override the system prompt for a specific conversation and the override persists
  3. User can click "Stop" to halt an in-progress generation and the stream stops immediately
  4. User can click "Regenerate" on the last assistant message and receive a fresh response
  5. User can export a conversation as a JSON file containing all messages
  6. User can search conversations by message content and see matching results
  7. User can adjust temperature and max tokens per conversation or globally
**Plans:** 1/1 plans complete

Plans:
- [x] 05-01: Backend completions (system prompt global + per-conversation, model parameter storage, regenerate endpoint, conversation search)
- [ ] 05-02: Frontend completions (system prompt UI in settings + per-conversation, stop button, regenerate button, model parameters)
- [ ] 05-03: Export + search (JSON export endpoint + download trigger, full-text search endpoint + search UI)
- [ ] 05-04: Completions tests (system prompt override, regenerate, stop/abort, export, search)

### Phase 6: Execution Trace System
**Goal**: Every assistant message shows a persisted, replayable execution trace — Forge's core differentiator
**Depends on**: Phase 5
**Requirements**: TRACE-01, TRACE-02, TRACE-03, TRACE-04, TRACE-05
**Success Criteria** (what must be TRUE):
  1. Each assistant message has an expandable "Execution Trace" section that is collapsed by default
  2. Expanding the trace shows ordered events (at minimum: token generation start/end) with type, name, status, and timestamps
  3. Trace events persist in the database linked to their message as a JSON blob
  4. Resuming a conversation reloads and correctly renders all trace events for every message
  5. An error during generation produces an error trace event visible in the trace panel
**Plans:** 3/1 plans complete

Plans:
- [x] 06-01-PLAN.md — Backend: TraceEmitter service, Message.trace_data field, Alembic migration, SSE trace events (Wave 1)
- [x] 06-02-PLAN.md — Frontend: TraceEvent types, useChat trace accumulation, TracePanel component, MessageBubble integration, trace replay (Wave 2)
- [x] 06-03-PLAN.md — Tests: TraceEmitter unit, SSE integration, persistence, TracePanel component tests (Wave 3)

### Phase 7: Orchestration Loop
**Goal**: The backend runs a full agentic loop with modular executor interfaces, run state tracking, and configurable timeout/retry
**Depends on**: Phase 6
**Requirements**: ORCH-01, ORCH-02, ORCH-03, ORCH-04, ORCH-05
**Success Criteria** (what must be TRUE):
  1. A chat turn that produces a tool call response enters the orchestration loop and continues until a final text response
  2. Tool calls are dispatched through an executor registry; swapping or mocking an executor requires no changes to the Orchestrator
  3. Every executor action emits a structured trace event (tool_start, tool_end) visible in the TracePanel
  4. Each run has a lifecycle state (created, running, completed, failed, cancelled) that updates correctly
  5. Configurable timeout and retry counts are respected; a timed-out call produces an error trace event, not a silent hang
**Plans:** 2 plans

Plans:
- [ ] 07-01-PLAN.md — Backend: Orchestrator service, BaseExecutor protocol, ExecutorRegistry, ToolExecutor, RunStateStore, current_datetime built-in tool, chat.py refactor, timeout/retry (Wave 1)
- [ ] 07-02-PLAN.md — Tests: Orchestrator unit tests with mock executors, RunState lifecycle tests, orchestration integration tests via SSE, timeout behavior (Wave 2)

### Phase 8: MCP Integration
**Goal**: Users can register MCP servers and Forge invokes their tools during orchestration with full trace visibility
**Depends on**: Phase 7
**Requirements**: MCP-01, MCP-02, MCP-03, MCP-04, MCP-05
**Success Criteria** (what must be TRUE):
  1. User can register an MCP server (name, command, args, env vars) in Settings and it persists
  2. User can enable or disable individual MCP servers; disabled servers are not started or invoked
  3. A chat message that triggers an MCP tool call invokes the correct server and appends the result to the conversation
  4. MCP tool calls appear in the execution trace with full metadata (server name, tool name, input, output, status)
  5. An MCP failure or timeout shows a user-visible error status in the trace panel, not a blank or crashed UI
**Plans:** 2 plans

Plans:
- [x] 08-01-PLAN.md — Backend: McpServer model + migration, CRUD API, McpProcessManager, McpExecutor, mcp package, backend tests (Wave 1)
- [ ] 08-02-PLAN.md — Frontend: mcp-api.ts client, McpServersSection + card + form components, Settings tab, frontend tests (Wave 2)

### Phase 9: Skills Integration
**Goal**: Users can enable agent skills and skill execution is visible and persisted in the trace
**Depends on**: Phase 7
**Requirements**: SKILL-01, SKILL-02, SKILL-03
**Success Criteria** (what must be TRUE):
  1. User can view available skills in Settings and toggle each on or off
  2. A chat turn that triggers a skill shows the skill name, trigger, and output in the execution trace
  3. Skill execution metadata (skill name, input, output, status, timestamps) persists in the database linked to the message
**Plans:** 1/1 plans complete

Plans:
- [x] 09-01-PLAN.md — Verify existing skills implementation (backend + frontend + tests already built in prior phases)

### Phase 10: File Upload + RAG
**Goal**: Users can upload documents and receive answers with source attribution from their files
**Depends on**: Phase 7
**Requirements**: RAG-01, RAG-02, RAG-03, RAG-04, RAG-05, SET-02, SET-03
**Success Criteria** (what must be TRUE):
  1. User can upload a PDF, DOCX, TXT, or MD file and see it appear in their file list
  2. After upload, the file is chunked and embedded; subsequent chat questions about the document return relevant answers
  3. Assistant responses to document questions show source attribution: file name, chunk preview, and relevance score
  4. User can view and delete uploaded files from the file management UI
  5. User can configure the embedding model endpoint and reranker endpoint in Settings
**Plans:** 1/1 plans complete

Plans:
- [x] 10-01-PLAN.md — Close remaining gaps: persist source citations to DB for conversation resume, wire reranker into retrieval pipeline, add tests

### Phase 11: Settings Completion + Quality Gate
**Goal**: All settings are complete, health diagnostics work, and every shipped feature has passing tests with CI green
**Depends on**: Phase 10
**Requirements**: SET-04, SET-06, TEST-01, TEST-02, TEST-03
**Success Criteria** (what must be TRUE):
  1. User can configure web search providers (SearXNG, Exa) in Settings
  2. Health diagnostics panel shows live status for LLM providers, ChromaDB, embedding model, reranker, and MCP servers
  3. `pytest` passes all backend unit, integration, and async tests with no failures
  4. `vitest` passes all frontend unit and component tests with no failures
  5. Playwright E2E tests pass for: auth flow, streaming chat, tool trace rendering, and settings persistence
  6. CI pipeline runs lint, type-check, unit/integration tests, E2E smoke, and build — all green
**Plans:** 3 plans

Plans:
- [ ] 11-01: Web search settings (SearXNG and Exa provider configuration, Settings UI)
- [ ] 11-02: Health diagnostics panel (backend health-check endpoints for all integrations, frontend diagnostics panel)
- [ ] 11-03: Backend test completion (pytest coverage review, missing unit/integration tests for all phases)
- [ ] 11-04: Frontend test completion (Vitest coverage review, missing component tests)
- [ ] 11-05: E2E test suite (Playwright: auth, streaming, trace panel, settings, export, search)
- [ ] 11-06: CI pipeline (GitHub Actions or Makefile: lint, type-check, unit, integration, E2E smoke, build)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Infrastructure Foundation | 4/1 | Complete   | 2026-03-21 |
| 2. Authentication | 3/1 | Complete   | 2026-03-21 |
| 3. LLM Provider Settings | 1/1 | Complete   | 2026-03-21 |
| 4. Core Streaming Chat | 2/1 | Complete   | 2026-03-21 |
| 5. Chat Completions | 1/1 | Complete   | 2026-03-22 |
| 6. Execution Trace System | 3/1 | Complete   | 2026-03-21 |
| 7. Orchestration Loop | 2/2 | Complete | 2026-03-21 |
| 8. MCP Integration | 1/2 | In progress | - |
| 9. Skills Integration | 1/1 | Complete   | 2026-03-22 |
| 10. File Upload + RAG | 1/1 | Complete   | 2026-03-22 |
| 11. Settings Completion + Quality Gate | 0/6 | Not started | - |
