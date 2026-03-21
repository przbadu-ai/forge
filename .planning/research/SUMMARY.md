# Project Research Summary

**Project:** Forge — Local-first AI assistant
**Domain:** Local-first self-hosted AI chat application with agent execution transparency
**Researched:** 2026-03-21
**Confidence:** HIGH

## Executive Summary

Forge is a local-first, single-user AI assistant built on a Next.js 16 frontend and FastAPI 0.135 backend, with SQLite for relational persistence, ChromaDB for vector retrieval, and a custom agent orchestration loop. The competitive landscape (Open WebUI, LibreChat, Jan.ai, Msty) has converged on a standard feature set for streaming chat, conversation management, and file-based RAG. Forge's differentiation is not in those features but in full execution transparency: a persisted, replayable execution trace per message that shows every tool call, MCP invocation, and skill trigger as an expandable tree. No competitor does this today, and it is the product's core reason to exist.

The recommended approach is a clean layered architecture with distinct concerns: FastAPI routers handle HTTP concerns, a custom Orchestrator service runs the agentic loop, and three executor types (ToolExecutor, McpExecutor, SkillExecutor) adapt external systems behind a shared interface. SSE carries both token deltas and structured trace events over a single stream per chat turn. Trace events are stored as a JSON blob per message (not normalized rows) and replayed on conversation resume. The build sequence is strictly dependency-ordered: infrastructure and auth first, then basic streaming chat, then the trace system, then tool/MCP integration, then file RAG — each phase adding a coherent capability slice.

The critical risks are infrastructure-level and must be addressed before any feature work: SQLite requires WAL mode + busy timeout to avoid lock errors under async concurrency; Alembic requires batch mode enabled in env.py before the first migration; the SSE stream must connect browser-to-FastAPI directly (not proxied through Next.js Route Handlers) to avoid buffering; and ChromaDB should run as a standalone HTTP server even locally to avoid multi-process data staleness. Getting these four things right in Phase 1 eliminates the most common sources of production failure for this stack.

---

## Key Findings

### Recommended Stack

The stack is a well-integrated Python/TypeScript split with strong version coherence. FastAPI 0.135.1 (native SSE via EventSourceResponse), SQLModel 0.0.22 (SQLAlchemy 2.0 + Pydantic V2 unified), and ChromaDB 1.5.5 (SQLite-backed embedded store) form the backend foundation. The openai Python client (2.29.0) provides OpenAI-compatible API access that works against Ollama, LM Studio, vLLM, and remote endpoints via base_url override. The MCP Python SDK (1.26.0) handles the full MCP client lifecycle for both stdio and HTTP transports. Authentication uses pwdlib[bcrypt] — not passlib, which is abandoned and broken on Python 3.12+.

On the frontend, Next.js 16 with App Router, shadcn/ui component primitives, zustand for client state, and @tanstack/react-query for server state form a proven combination. Markdown rendering uses react-markdown + rehype-highlight (not assistant-ui, which would fight custom identity). The critical frontend decision is to use fetch() + ReadableStream for SSE consumption, not the native EventSource API, because EventSource only supports GET and cannot send a chat payload body.

**Core technologies:**
- Next.js 16.2 + TypeScript 5 — frontend framework with App Router; Server Components reduce client JS
- FastAPI 0.135.1 — native SSE support (EventSourceResponse); Pydantic V2 native
- Python 3.12 — best package support; ChromaDB 1.5.x not confirmed on 3.13
- SQLite + SQLModel 0.0.22 + Alembic — zero-config local persistence with async support via aiosqlite
- ChromaDB 1.5.5 — embedded local vector store; run as HTTP server to avoid multi-process staleness
- openai 2.29.0 — OpenAI-compatible async client; works against any provider via base_url override
- mcp 1.26.0 — official MCP Python SDK; supports stdio, SSE, and Streamable HTTP transports
- sentence-transformers 3.x — local embedding (all-MiniLM-L6-v2); no API key required
- zustand 5 + @tanstack/react-query 5 — client state + server state management; minimal boilerplate
- pwdlib[bcrypt] — password hashing; replaces abandoned passlib

**Do not use:** passlib, LangChain/LangGraph, WebSockets for token streaming, native EventSource for POST SSE, redis, Celery, next-auth v4.

### Expected Features

Users of self-hosted AI assistants in 2026 have well-established baseline expectations formed by Open WebUI, LibreChat, Jan.ai, and Msty. Missing any table-stakes feature makes the product feel incomplete, regardless of differentiators.

**Must have (table stakes) — v1:**
- Streaming token output — non-streaming feels broken to all modern AI chat users
- Markdown + syntax-highlighted code rendering — primary output format for developer users
- Conversation list with resume, rename, delete — expected from any chat product
- Configurable LLM provider + model with test-connection button — prerequisite for any interaction
- System prompt / custom instructions — global default + per-conversation override
- Message regeneration (retry) — one-click retry on bad or failed output
- File upload for document Q&A — all major competitors support this
- Light/Dark/System theme — near-free with Tailwind + shadcn; expected universally
- Single-user authentication — login gate for data protection
- JSON export of conversations — basic data portability

**Should have (differentiators) — v1:**
- Execution trace UI per message (collapsed, expandable) — Forge's core differentiator; no competitor has this
- Trace persistence + replay on conversation resume — unique; Open WebUI and LibreChat both lose trace state on refresh
- MCP server registration + invocation with trace visibility — MCP is becoming the standard tool protocol
- Agent skills configuration (enable/disable per session) — modular capability toggling
- Source attribution for RAG answers (file name, chunk preview, similarity score) — few competitors show the source
- Health diagnostics panel — status page for LLM, ChromaDB, embeddings, MCP servers

**Add after validation (v1.x):**
- Conversation search, reranker configuration, web search tool, model parameter controls (temperature/max tokens), health diagnostics panel, configurable timeout/retry per provider

**Defer (v2+):**
- Multi-user support, image generation, voice/TTS, parallel model comparison, advanced RAG (graph RAG, adaptive chunking), OAuth/SSO

**Confirmed anti-features — do not build for MVP:** multi-user collaboration, OAuth/SSO, mobile app, LangGraph/AutoGen integration, image generation, voice call/video.

### Architecture Approach

The architecture is a clean split: Next.js frontend communicates with FastAPI over HTTP REST and direct SSE. The FastAPI backend has four layers — routers (HTTP contract), services (business logic and orchestration), executors (external system adapters), and data stores (SQLite + ChromaDB). The Orchestrator service is the heart: a while-loop that sends messages to the LLM, detects tool call responses, dispatches to the appropriate executor, appends results to message history, and repeats until a final text response. The TraceEmitter sits alongside the Orchestrator and emits named SSE events (token, tool_start, tool_end, mcp_call, skill_start, run_done, run_error) over the same stream, while batching events for persistence on run completion.

The executor pattern is critical for testability: ToolExecutor, McpExecutor, and SkillExecutor all implement `BaseExecutor` with `invoke(name, input) -> str` and `list_tools() -> list[ToolDefinition]`. The Orchestrator never knows which executor handles a call — it routes through an executor registry. This makes unit-testing the Orchestrator loop trivial by mocking executors.

**Major components:**
1. **Orchestrator Service** — core agent loop (model call → tool dispatch → observation → repeat)
2. **TraceEmitter** — emits structured SSE events per step; persists complete trace JSON at run end
3. **ToolExecutor / McpExecutor / SkillExecutor** — executor registry adapters; uniform interface
4. **FilePipeline** — upload → chunk → embed → ChromaDB storage; async background to avoid blocking SSE
5. **SQLite via SQLModel** — conversations, messages, traces (JSON blob), file records, settings
6. **ChromaDB HTTP server** — vector store; one shared collection with metadata filtering, not per-conversation collections

**Key patterns to follow:**
- Store traces as a JSON array in a single TEXT column, not normalized rows — traces are always read as a complete set
- Use one shared ChromaDB collection with metadata filters, not per-conversation collections
- File uploads and embedding happen asynchronously before chat, not inline during a streaming turn
- SSE stream connects browser directly to FastAPI, bypassing Next.js Route Handlers for streaming routes

### Critical Pitfalls

All 9 pitfalls are documented in PITFALLS.md with recovery strategies. The top 5 that must be addressed before any feature work:

1. **SSE buffering through Next.js Route Handlers** — tokens arrive in a single batch in production. Prevention: connect browser directly to FastAPI for the SSE stream; set `X-Accel-Buffering: no`, disable Next.js `compress`, export `dynamic = 'force-dynamic'`. Address in Phase 1.

2. **SQLite "database is locked" under async concurrency** — intermittent `OperationalError` when streaming writes overlap with reads. Prevention: enable WAL mode (`PRAGMA journal_mode=WAL`) + busy timeout (`PRAGMA busy_timeout=5000`) at connection creation; use `NullPool` with aiosqlite. Address in Phase 1 database setup.

3. **Alembic ALTER TABLE failures on SQLite schema changes** — any column modification/drop beyond ADD COLUMN fails. Prevention: enable batch mode in `env.py` (`render_as_batch=True`) before writing any migration. Address in Phase 1 before first migration.

4. **ChromaDB library mode data staleness in multi-process** — workers maintain separate in-memory state; uploads by one worker are invisible to others. Prevention: run ChromaDB as an HTTP server (`chroma run --path ./chroma_data`) even locally; use `chromadb.HttpClient`. Address before RAG phase.

5. **MCP zombie processes on reconfiguration** — old child processes accumulate when settings change. Prevention: implement `McpProcessManager` with PID tracking, clean shutdown sequence (stdin close → SIGTERM → SIGKILL), and orphan cleanup on startup. Address in MCP integration phase.

**Additional critical concerns:** API keys must use Pydantic `SecretStr` and never be returned in full from GET endpoints; markdown rendering must use `rehype-sanitize` to block LLM-injected XSS; abort signals must propagate to the upstream LLM request (not just the client listener).

---

## Implications for Roadmap

Research establishes a clear dependency graph that dictates phase ordering. Each phase must be complete before the next can begin.

### Phase 1: Infrastructure Foundation
**Rationale:** Every subsequent phase depends on the database, migrations, and FastAPI/Next.js skeleton. Pitfalls 4 (SQLite locking) and 7 (Alembic batch mode) must be resolved here or they corrupt everything built on top. This phase has no user-visible features — it is pure correctness.
**Delivers:** Working FastAPI app factory, SQLite engine with WAL mode + busy timeout, SQLModel models with Alembic migrations (batch mode enabled), Next.js shell with App Router and shadcn/ui configured, uv and npm dependency lock files, development tooling (ruff, mypy, vitest).
**Avoids:** SQLite lock errors (Pitfall 4), Alembic migration failures (Pitfall 7)
**Research flag:** Standard patterns — no additional research needed; exact configuration is documented in STACK.md and PITFALLS.md.

### Phase 2: Auth + Settings Foundation
**Rationale:** Authentication gates every API endpoint. Settings (LLM provider config) are required before the chat interface is useful. These two must come before chat because without them you cannot test chat end-to-end. API key security (Pitfall 9) must be designed in here, not retrofitted.
**Delivers:** Single-user login (username + password + bcrypt via pwdlib), JWT session tokens (python-jose), protected FastAPI middleware, Settings CRUD for LLM provider configuration, test-connection button, light/dark/system theme (next-themes).
**Addresses:** Auth, LLM provider config, test-connection, theme (all P1 table stakes)
**Avoids:** API key plain text storage (Pitfall 9), session token security
**Research flag:** Standard patterns — auth and settings are well-documented; no additional research needed.

### Phase 3: Core Streaming Chat
**Rationale:** This is the core product experience. Conversation CRUD, message persistence, LLM streaming via SSE, and markdown rendering form the foundation that all agent features extend. The SSE buffering pitfall (Pitfall 1) must be solved here with the correct browser-to-FastAPI direct connection pattern. Markdown XSS (Pitfall 8) must be addressed before first render.
**Delivers:** Conversation creation/list/resume/rename/delete, streaming chat via SSE (browser → FastAPI directly), markdown + syntax-highlighted code rendering (react-markdown + rehype-highlight + rehype-sanitize), message persistence, system prompt support, message retry/regenerate, JSON export.
**Addresses:** Streaming chat, conversation management, markdown rendering, system prompt, retry, export (all P1 table stakes)
**Avoids:** SSE buffering (Pitfall 1), streaming abort/resume incompatibility (Pitfall 3), markdown XSS (Pitfall 8)
**Research flag:** Standard patterns for most; the SSE stream implementation (browser → FastAPI direct, fetch + ReadableStream) is well-documented. Abort signal propagation needs careful implementation.

### Phase 4: Execution Trace System
**Rationale:** The trace system is Forge's primary differentiator and must be in v1 to validate the concept. It is built alongside (not after) tools — the TraceEmitter infrastructure is shared by all subsequent executor types. Building trace before tools means the UI and persistence schema are established before tool events arrive.
**Delivers:** TraceEmitter service (emits named SSE events: token, tool_start, tool_end, run_done, run_error), trace persistence (JSON blob in `traces` table, FK to message), TracePanel UI component (collapsed by default, expandable), trace replay on conversation resume.
**Addresses:** Execution trace UI, trace persistence + replay (P1 differentiators)
**Avoids:** Trace event DB bloat from normalized rows (Pitfall — store as JSON blob, not rows)
**Research flag:** Standard patterns for SSE event types. The trace schema design (JSON blob vs normalized) is clearly established in ARCHITECTURE.md.

### Phase 5: Orchestration Loop + Tool/MCP Integration
**Rationale:** With trace infrastructure in place, the orchestrator loop and executor pattern can be built. This phase delivers the agentic loop that enables tool calling, MCP invocations, and skills. All three executor types share the BaseExecutor interface established here. MCP process lifecycle management (Pitfall 6) must be addressed in this phase.
**Delivers:** Custom Orchestrator service (model → tools → model while-loop), executor registry, ToolExecutor (built-in tools), McpExecutor + McpProcessManager (MCP server lifecycle, tool discovery, invocation), SkillExecutor (skill workflows), MCP settings UI (register/remove servers), skills configuration UI (enable/disable per session), provider API divergence adapter layer (Pitfall 2).
**Addresses:** Custom orchestration loop, MCP integration, agent skills (all P1), web search tool (P2 — can defer to v1.x)
**Avoids:** MCP zombie processes (Pitfall 6), provider API divergence (Pitfall 2)
**Research flag:** MCP process lifecycle management and per-provider capability detection may benefit from a research-phase pass. vLLM tool call configuration (`--enable-auto-tool-choice` with parser flags) needs validation against actual vLLM deployment.

### Phase 6: File Upload + RAG + Source Attribution
**Rationale:** RAG is a table-stakes feature but has significant infrastructure complexity (FilePipeline, ChromaDB, embedding). It can be developed in parallel with Phase 5 after Phase 3 completes, but must follow the core chat phase because retrieval context is injected into chat turns. ChromaDB must run as an HTTP server (Pitfall 5) — establish this before writing any RAG code.
**Delivers:** File upload endpoint (PDF, DOCX, TXT), async FilePipeline (chunk → embed → ChromaDB HTTP server), retrieval at chat time (query embedding → ChromaDB → top-K chunks → context injection), source attribution UI (file name, chunk preview, similarity score per RAG answer), embedding settings UI (model selection, local vs remote).
**Addresses:** File upload + RAG, source attribution (P1 must-haves)
**Avoids:** ChromaDB library mode staleness (Pitfall 5), blocking embedding during chat (Architecture anti-pattern 5)
**Research flag:** ChromaDB HTTP server setup and the FilePipeline (chunking strategy, async upload flow) may benefit from a targeted research-phase pass to confirm the correct API surface for ChromaDB 1.5.5 HTTP client.

### Phase 7: Quality + Polish
**Rationale:** Final pass to ensure correctness, coverage, and usability before launch. All pitfall checklists verified. UX issues (loading states, scroll lock, error messages) addressed.
**Delivers:** Test coverage (pytest-asyncio for backend, Vitest + Playwright for frontend), health diagnostics panel, conversation search, model parameter controls (temperature/max tokens), all UX pitfalls addressed (loading states, scroll lock, error mapping), "looks done but isn't" checklist verified end-to-end.
**Addresses:** Health diagnostics (P2), conversation search (P2), model parameter controls (P2)
**Research flag:** Standard patterns — no additional research needed for testing infrastructure.

### Phase Ordering Rationale

- **Infrastructure before auth:** WAL mode, batch migrations, and the async SQLite engine must be correct before any endpoint can write data.
- **Auth before chat:** Session tokens gate all API routes; no feature can be tested end-to-end without them.
- **Chat before trace:** There must be messages and SSE events before trace infrastructure has anything to emit or persist.
- **Trace before tools:** TraceEmitter and the trace DB schema must exist before any executor emits events; building them together avoids retrofitting.
- **Tools before RAG:** The orchestrator loop handles RAG retrieval context injection; RAG needs the orchestrator in place. RAG also benefits from the executor pattern established in Phase 5.
- **RAG can parallelize with tools:** After Phase 3 is complete, the FilePipeline and ChromaDB work can run concurrently with the orchestrator/executor work in Phase 5, merging in Phase 6.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 5 (MCP Integration):** MCP process lifecycle patterns and per-provider capability detection (Ollama vs LM Studio vs vLLM tool call differences) are complex. The MCP Python SDK 1.26.0 API surface and subprocess management patterns warrant a `/gsd:research-phase` pass.
- **Phase 6 (RAG/ChromaDB):** ChromaDB 1.5.5 HTTP client API and the correct async initialization pattern for the FilePipeline may need a targeted research pass — the library is actively evolving and the HTTP client API has changed across versions.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Infrastructure):** SQLite WAL mode, Alembic batch mode, FastAPI lifespan — all exactly documented in PITFALLS.md and STACK.md.
- **Phase 2 (Auth):** Single-user JWT auth with pwdlib is well-documented; the FastAPI auth tutorial covers this precisely.
- **Phase 3 (Streaming Chat):** SSE pattern (browser → FastAPI direct, fetch + ReadableStream), react-markdown + rehype-sanitize — all well-documented. The pitfall avoidance strategies are concrete and implementation-ready.
- **Phase 4 (Trace):** SSE event types and JSON blob storage pattern are fully specified in ARCHITECTURE.md.
- **Phase 7 (Quality):** Standard testing infrastructure.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions verified against PyPI/npm as of 2026-03-21; version compatibility table cross-referenced |
| Features | HIGH | Based on direct analysis of 6 live competitors (Open WebUI, LibreChat, Jan.ai, Msty, AnythingLLM, LobeChat) |
| Architecture | HIGH | Patterns verified across official docs, multiple implementation guides, and production projects |
| Pitfalls | HIGH | Multiple verified sources per pitfall; several with linked GitHub issues and production post-mortems |

**Overall confidence:** HIGH

### Gaps to Address

- **vLLM tool call configuration in production:** The `--enable-auto-tool-choice` flag with the correct parser variant (hermes, llama3, mistral) needs validation against real vLLM deployment before Phase 5. The research documents the requirement but integration testing is needed.
- **ChromaDB 1.5.5 HTTP client API:** The exact initialization pattern for `chromadb.HttpClient` in async FastAPI context (lifespan startup, collection caching) should be confirmed during Phase 6 planning since the library API has changed across versions.
- **Sentence-transformers startup time:** The sentence-transformers library (heavy torch dependency) can significantly increase cold-start time. Consider lazy initialization with an `Optional[EmbeddingProvider]` pattern — validate the impact before Phase 6.
- **Streaming abort signal propagation to LLM:** The exact pattern for propagating `AbortSignal` from the browser through Next.js fetch through FastAPI to the upstream LLM streaming request needs implementation-level verification in Phase 3.

---

## Sources

### Primary (HIGH confidence)
- [FastAPI PyPI](https://pypi.org/project/fastapi/) — version 0.135.1, native SSE, Pydantic V2 requirement
- [FastAPI SSE official docs](https://fastapi.tiangolo.com/tutorial/server-sent-events/) — EventSourceResponse pattern
- [FastAPI async tests](https://fastapi.tiangolo.com/advanced/async-tests/) — httpx AsyncClient pattern
- [Next.js 16 blog](https://nextjs.org/blog) — version 16.2.0 confirmed March 2026
- [openai PyPI](https://pypi.org/project/openai/) — version 2.29.0, asyncio-native
- [mcp PyPI](https://pypi.org/project/mcp/) — version 1.26.0, spec 2025-11-25
- [chromadb PyPI](https://pypi.org/project/chromadb/) — version 1.5.5
- [Open WebUI GitHub](https://github.com/open-webui/open-webui) — competitor feature analysis
- [LibreChat GitHub](https://github.com/danny-avila/LibreChat) — competitor feature analysis
- [ChromaDB Cookbook — Road to Production](https://cookbook.chromadb.dev/running/road-to-prod/) — multi-process constraints
- [Alembic batch migrations — official docs](https://alembic.sqlalchemy.org/en/latest/batch.html) — SQLite ALTER TABLE limitation
- [passlib deprecation discussion](https://github.com/fastapi/fastapi/discussions/11773) — passlib abandoned; pwdlib recommended

### Secondary (MEDIUM confidence)
- [Agentic Loop with Tool Calling — Temporal Docs](https://docs.temporal.io/ai-cookbook/agentic-loop-tool-call-openai-python) — orchestrator loop pattern
- [ChromaDB library mode staleness](https://medium.com/@okekechimaobi/chromadb-library-mode-stale-rag-data-never-use-it-in-production-heres-why-b6881bd63067) — embedded mode production constraint
- [SQLite concurrent writes — tenthousandmeters](https://tenthousandmeters.com/blog/sqlite-concurrent-writes-and-database-is-locked-errors/) — WAL mode and busy timeout
- [Fixing SSE streaming in Next.js — Medium (Jan 2026)](https://medium.com/@oyetoketoby80/fixing-slow-sse-server-sent-events-streaming-in-next-js-and-vercel-99f42fbdb996) — buffering pitfall and fix
- [vercel/next.js SSE discussion #48427](https://github.com/vercel/next.js/discussions/48427) — SSE buffering root cause
- [Real Faults in MCP Software — arXiv 2603.05637](https://arxiv.org/html/2603.05637v1) — MCP process lifecycle failures
- [MCP Lifecycle spec](https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle) — shutdown sequence
- [Ollama vs vLLM vs LM Studio (2026)](https://www.clawctl.com/blog/ollama-vs-vllm-vs-lm-studio) — provider divergence

### Tertiary (LOW confidence)
- [AI SDK UI: Chatbot Resume Streams — Vercel](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-resume-streams) — abort vs resume architecture tradeoff; implementation for Forge differs from Vercel AI SDK approach

---

*Research completed: 2026-03-21*
*Ready for roadmap: yes*
