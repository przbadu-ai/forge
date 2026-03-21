# Forge

## What This Is

A local-first, self-hosted AI assistant application inspired by Claude's UX. Forge connects to any OpenAI-compatible LLM endpoint and provides streaming chat, tool use visibility, MCP integrations, and skills — all configurable through a settings-first interface. Built for solo developers running local LLM infrastructure who want transparency and control over their AI workflows.

## Core Value

Every AI interaction — chat, tool call, MCP action, skill execution — is visible, persisted, and reviewable. The user always knows what happened and why.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Single-user authentication with secure session handling
- [ ] Chat interface with streaming token output, markdown rendering, and syntax-highlighted code blocks
- [ ] Conversation history list with resume, rename, and delete
- [ ] Retry/regenerate last response on failure
- [ ] Execution trace UI per message (tool calls, MCP calls, skill triggers — expandable, collapsed by default)
- [ ] Trace persistence in DB with reload on chat resume
- [ ] MCP server registration and configuration in Settings
- [ ] MCP tool invocation with trace visibility and error states
- [ ] Agent skills configuration (enable/disable) in Settings
- [ ] Skill execution with trace visibility and persistence
- [ ] File upload, chunking, embedding, and retrieval (SQLite + ChromaDB)
- [ ] Source visibility — show which files/chunks were used for retrieved answers
- [ ] Settings pages: LLM providers/models, embedding config, reranker config, web search providers, MCP servers, skills
- [ ] Test-connection/health-check for configured endpoints
- [ ] Health diagnostics panel for quick status of all integrations
- [ ] Light/Dark/System theme support
- [ ] JSON export of chat sessions for backup
- [ ] Lightweight custom orchestration loop (model -> tools/MCP/skills -> model)
- [ ] Modular executor interfaces (ToolExecutor, McpExecutor, SkillExecutor, TraceEmitter, RunStateStore)
- [ ] Configurable timeout/retry for all external calls
- [ ] Test coverage at all layers (Vitest, pytest, Playwright)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Complex agent orchestration (LangGraph, etc.) — MVP uses lightweight custom loop; defer to v2+
- Multi-tenant/multi-user features — single-user MVP for local deployment
- Enterprise governance/audit workflows — not the target audience
- Advanced RAG (graph RAG, adaptive chunking) — keep retrieval simple for MVP
- Mobile app — web-first
- OAuth/SSO — single-user doesn't need it
- Real-time collaboration — solo developer tool

## Context

The user (przbadu) wants a practical local AI assistant that connects to any OpenAI-compatible endpoint (Ollama, LM Studio, vLLM, or remote APIs). The UI should be functionally comparable to Claude.ai — same features and general flow — but with its own visual identity, built using the `/frontend-design` skill for distinctive, polished design rather than a direct replica.

Screenshots of Claude.ai were provided as functional reference for:
- Chat layout with sidebar conversation list
- Message composition area with attachment options
- Skills/connectors management interface
- Tool use visibility in responses

The project uses a split stack: Next.js (App Router) + shadcn/ui + Tailwind for frontend, Python + FastAPI + SQLite + ChromaDB for backend. Testing is mandatory — the project must support autonomous coding agent workflows (plan, implement, test, fix, verify).

## Constraints

- **Frontend stack**: Next.js (App Router), TypeScript, shadcn/ui, Tailwind CSS — fixed for MVP
- **Backend stack**: Python 3.11+, FastAPI, Pydantic, SQLModel/SQLAlchemy, Alembic, SQLite, ChromaDB — fixed for MVP
- **Testing stack**: Vitest + Testing Library + Playwright (frontend), pytest + httpx + pytest-asyncio (backend) — mandatory
- **Quality gates**: ESLint + Prettier (frontend), Ruff + Black (backend), TypeScript strict mode, mypy — required
- **No agent framework**: Custom orchestration loop only; no LangGraph dependency in MVP
- **File storage**: `./uploads` directory served through controlled endpoints (not `./public`)
- **Streaming**: SSE (or WebSocket where required) for token streaming and trace events

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Name: Forge | Hub where AI workflows are shaped locally | — Pending |
| Functional match to Claude UI, not replica | Own visual identity using /frontend-design skill | — Pending |
| Single-user auth | Solo developer target; simplifies MVP scope | — Pending |
| Any OpenAI-compatible endpoint | Maximum flexibility — Ollama, LM Studio, vLLM, remote APIs | — Pending |
| Custom orchestration over agent frameworks | Keep MVP simple; LangGraph optional for v2+ | — Pending |
| SQLite + ChromaDB | Local-first, zero-config data layer | — Pending |
| Mandatory testing at all layers | Enables autonomous coding agent delivery loops | — Pending |

---
*Last updated: 2026-03-21 after initialization*
