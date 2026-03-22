# Forge

## What This Is

A local-first, self-hosted AI assistant application connecting to any OpenAI-compatible LLM endpoint. Forge provides streaming chat with markdown rendering, execution trace visibility for every tool call and MCP action, file upload with RAG retrieval and source attribution, MCP server management, agent skills, and comprehensive settings — all through a polished web interface built for transparency and control.

## Core Value

Every AI interaction — chat, tool call, MCP action, skill execution — is visible, persisted, and reviewable. The user always knows what happened and why.

## Requirements

### Validated

- ✓ Single-user authentication with JWT sessions — v1.0
- ✓ Chat interface with streaming SSE, markdown rendering, syntax-highlighted code — v1.0
- ✓ Conversation history with resume, rename, delete, search — v1.0
- ✓ System prompts (global + per-conversation), stop/regenerate, model parameters — v1.0
- ✓ Execution trace UI per message (expandable, collapsed by default) — v1.0
- ✓ Trace persistence in DB with reload on conversation resume — v1.0
- ✓ MCP server registration, enable/disable, tool invocation with trace visibility — v1.0
- ✓ Agent skills configuration and execution with trace persistence — v1.0
- ✓ File upload, chunking, embedding, ChromaDB retrieval with source attribution — v1.0
- ✓ Settings: LLM providers, embedding, reranker, web search, MCP servers, skills — v1.0
- ✓ Test-connection and health diagnostics for all integrations — v1.0
- ✓ Light/Dark/System theme support — v1.0
- ✓ JSON export of chat sessions — v1.0
- ✓ Custom orchestration loop with modular executors — v1.0
- ✓ Configurable timeout/retry for external calls — v1.0
- ✓ Test coverage: Vitest, pytest, Playwright E2E, CI pipeline — v1.0

### Active

(None yet — define in next milestone)

### Out of Scope

- Complex agent orchestration (LangGraph, etc.) — custom loop is sufficient and more transparent
- Multi-tenant/multi-user features — single-user tool for local deployment
- Enterprise governance/audit workflows — not the target audience
- Advanced RAG (graph RAG, adaptive chunking) — simple retrieval works for MVP
- Mobile app — web-first, responsive UI is sufficient
- OAuth/SSO — single-user doesn't need it
- Real-time collaboration — solo developer tool

## Context

Shipped v1.0 MVP with 76 Python files (~7,800 LOC) and 78 TypeScript files (~7,500 LOC). Split stack: Next.js 16 (App Router) + shadcn/ui + Tailwind CSS v4 for frontend, Python 3.11 + FastAPI + SQLite (WAL mode) + ChromaDB for backend. 130 git commits over 2 days of development.

The application connects to any OpenAI-compatible endpoint (Ollama, LM Studio, vLLM, or remote APIs). UI is functionally comparable to Claude.ai with its own visual identity.

### Known Tech Debt (from v1.0)
- 11 pre-existing orchestration test failures (test_orchestrator.py)
- Skill tool schemas not passed to Orchestrator (skills unreachable via LLM function-calling)
- TracePanel.tsx orphaned dead code (replaced by ExecutionStep refactor)
- Several requirement checkboxes in REQUIREMENTS.md were out of sync (fixed in archive)

## Constraints

- **Frontend stack**: Next.js (App Router), TypeScript, shadcn/ui, Tailwind CSS — fixed
- **Backend stack**: Python 3.11+, FastAPI, Pydantic, SQLModel/SQLAlchemy, Alembic, SQLite, ChromaDB — fixed
- **Testing stack**: Vitest + Testing Library + Playwright (frontend), pytest + httpx + pytest-asyncio (backend) — mandatory
- **Quality gates**: ESLint + Prettier (frontend), Ruff + Black (backend), TypeScript strict mode, mypy — required
- **No agent framework**: Custom orchestration loop only; no LangGraph dependency
- **File storage**: `./uploads` directory served through controlled endpoints (not `./public`)
- **Streaming**: SSE for token streaming and trace events

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Name: Forge | Hub where AI workflows are shaped locally | ✓ Good |
| Functional match to Claude UI, not replica | Own visual identity | ✓ Good |
| Single-user auth with JWT | Solo developer target; simplifies scope | ✓ Good |
| Any OpenAI-compatible endpoint | Maximum flexibility — Ollama, LM Studio, vLLM, remote APIs | ✓ Good |
| Custom orchestration over agent frameworks | Keep it simple, debuggable; LangGraph optional for v2+ | ✓ Good |
| SQLite + ChromaDB | Local-first, zero-config data layer | ✓ Good |
| Mandatory testing at all layers | Enables autonomous coding agent delivery loops | ✓ Good |
| SSE over WebSocket | Simpler, sufficient for streaming; EventSource needs POST workaround | ✓ Good |
| Traces as JSON blob per message | Always read as complete set; simpler than normalized rows | ✓ Good |
| EphemeralClient for ChromaDB | Single-process dev; switch to HttpClient for production | ⚠️ Revisit for multi-process |
| pwdlib[bcrypt] over passlib | passlib abandoned, broken on Python 3.12+ | ✓ Good |

---
*Last updated: 2026-03-22 after v1.0 milestone*
