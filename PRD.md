# PRD: Local-First Claude-Like Assistant (MVP)

## 1) Product Overview

Build a Claude-like chat application for local/self-hosted LLM workflows, with support for streaming chat, tool use visibility, MCP integrations, and skills.  
The app should prioritize practical local usage (simple setup, transparent execution, configurable providers) over advanced/complex orchestration.

## 1.1) Frontend Stack Mandate (MVP)

Frontend implementation is fixed for MVP:
- Framework: `Next.js` (App Router) with `TypeScript`
- UI system: `shadcn/ui` (Radix primitives)
- Styling: `Tailwind CSS`

Implementation rule:
- If a UI primitive exists in `shadcn/ui` (button, dialog, dropdown, sheet, tabs, accordion, tooltip, etc.), use it instead of building custom primitives from scratch.
- Customization is allowed through composition, theming, and styling, while keeping `shadcn/ui` primitives as the foundation for accessibility and consistency.

## 1.2) Backend Stack Mandate (MVP)

Backend implementation is fixed for MVP:
- Language/runtime: `Python 3.11+`
- API framework: `FastAPI`
- Validation/schema: `Pydantic`
- ORM/data access: `SQLModel` or `SQLAlchemy`
- Migrations: `Alembic`
- Relational DB: `SQLite`
- Vector store: `ChromaDB`

Streaming/runtime:
- Use SSE (or WebSocket where required) for token streaming and execution trace events.
- Use direct OpenAI-compatible API calls for chat, embeddings, and reranking.

Agent framework decision:
- MVP should use a lightweight custom orchestration loop (model -> tools/MCP/skills -> model).
- Do not require `LangGraph` (or equivalent agent framework) in MVP.
- `LangGraph` is optional for V2+ only when multi-step graph orchestration is genuinely needed.

## 1.3) Testing and Validation Stack Mandate (MVP)

Testing stack is required so autonomous coding agents can ship features safely:

Frontend:
- Unit/component tests: `Vitest` + `Testing Library` (`@testing-library/react`, `@testing-library/user-event`)
- E2E tests: `Playwright`

Backend:
- Test runner: `pytest`
- API testing: `httpx` + FastAPI test client patterns
- Async tests: `pytest-asyncio`

Quality gates:
- Linting/formatting: `ESLint` + `Prettier` (frontend), `Ruff` + `Black` (backend)
- Type checks: `TypeScript` strict mode + `mypy` (backend where practical)

Contract and regression validation:
- Add API contract/smoke tests for core chat endpoints (streaming + trace payload shape).
- Add deterministic regression tests for tool trace persistence and settings persistence.

## 2) Problem Statement

Current hosted assistants are powerful but often:
- Require cloud-first model usage
- Provide limited transparency into tool/agent execution
- Are hard to tailor for local model stacks and self-hosted search/retrieval

The user needs a local-first assistant where models, rerankers, embeddings, tools, MCP servers, and skills are configurable and observable in one place.

## 3) Goals

- Deliver a Claude-like chat UX with token streaming.
- Support local and remote OpenAI-compatible model endpoints.
- Persist conversations, tool calls, skill invocations, and MCP interactions.
- Keep RAG architecture intentionally simple for MVP.
- Provide a settings-first experience so core integrations can be configured without code edits.

## 4) Non-Goals (MVP)

- Complex agent orchestration trees
- Multi-tenant organization features
- Enterprise governance/audit workflows
- Advanced retrieval research features (graph RAG, adaptive chunking pipelines, etc.)

## 5) Target Users

- Primary: solo developer running local LLM infrastructure
- Secondary: small technical teams prototyping self-hosted AI assistants

## 6) Success Criteria (MVP)

- User can configure at least one chat model + embeddings + reranker and complete end-to-end Q&A.
- Chat responses stream reliably in the UI.
- Every tool/skill/MCP action is visible per message and stored for later review.
- User can upload/manage files for retrieval and reference them in chat.
- App works with SQLite + ChromaDB in a local environment.

## 7) Functional Requirements

### 7.1 Authentication
- Provide login/authentication for app access.
- Session handling should be secure enough for local/self-hosted deployment.

### 7.2 Chat Experience
- Chat interface with:
  - streaming token output
  - markdown rendering
  - syntax-highlighted code blocks
  - conversation history list and resume
- Message state should handle: generating, completed, failed, cancelled.
- The chat UI should be built with `Next.js` + `shadcn/ui` components.

### 7.3 Tool Use + Execution Trace UI
- Each assistant message can include an expandable "Execution Trace" section.
- Section displays ordered events, including:
  - tool calls (e.g., web search, web fetch, bash/code execution, memory, etc.)
  - skill triggers/executions
  - MCP calls
- Each event should include minimal metadata:
  - type
  - name
  - status (started/success/failure)
  - timestamps
  - compact input/output preview (safe truncation)
- Persist traces in DB and re-render them on chat reload.

### 7.4 MCP Support
- User can register/configure MCP servers in Settings.
- Chat runtime can invoke MCP tools and surface events in trace UI.
- Failures/timeouts must show user-visible error status in trace.
- Backend should execute MCP calls via a dedicated MCP executor layer (framework-agnostic interface).

### 7.5 Agent Skills Support
- User can configure and enable/disable skills in Settings.
- Skill triggers and outputs appear in message trace UI.
- Skill execution metadata persists in DB.
- Backend should execute skills via a dedicated skills executor layer (framework-agnostic interface).

### 7.6 Retrieval and File Handling (Simple MVP)
- Use SQLite for app data and ChromaDB for vectors.
- Keep file storage simple:
  - **Recommended MVP approach:** store user files in `./uploads` (not `./public`) and serve through controlled endpoints.
  - Reason: avoids exposing raw files publicly while staying lightweight.
- Ingestion should support chunking + embedding (configurable via env).
- Retrieval flow should remain straightforward (no complex RAG strategies for MVP).

### 7.7 Settings
- Settings pages for:
  - LLM providers/models (OpenAI-compatible; multiple profiles)
  - embedding model config
  - reranker config
  - web search providers (e.g., SearXNG, Exa, others)
  - MCP server configuration
  - skills configuration
- Validate required fields before save.
- Support test-connection/check-health action where feasible.
- Build settings forms and controls using `shadcn/ui` form-related components.

### 7.8 Theme Support
- Support Light, Dark, and System themes.

### 7.9 Backend Runtime and Orchestration
- Implement a transparent, deterministic orchestration loop for MVP:
  - create run state
  - call model
  - dispatch tool/MCP/skill requests
  - persist trace events
  - continue until assistant turn completes or fails
- Keep orchestration logic modular with explicit interfaces:
  - `ToolExecutor`
  - `McpExecutor`
  - `SkillExecutor`
  - `TraceEmitter`
  - `RunStateStore`
- These interfaces should make future LangGraph adoption possible without major rewrites.

### 7.10 Testing Requirements
- Every shipped feature must include corresponding tests at the appropriate layer:
  - unit/component tests for UI and business logic
  - integration/API tests for backend flows
  - E2E tests for critical user journeys
- Minimum critical E2E coverage:
  - authenticate user
  - start a chat and receive streamed output
  - trigger at least one tool call and verify trace rendering
  - configure a model/provider in settings and verify persistence
- Streaming-specific tests must verify:
  - ordered token/event delivery
  - graceful handling of stream interruptions
  - persisted final message + trace integrity after completion/failure
- CI/local validation must fail on:
  - test failures
  - lint/type-check failures
  - broken build

### 7.11 Autonomous Delivery Loop (Coding Agent Autopilot)
- The project must support an end-to-end autonomous loop:
  1. plan task from PRD + acceptance criteria
  2. implement code changes
  3. run lint/type checks
  4. run relevant test suites
  5. apply fixes for failures
  6. re-run checks until green
  7. produce verification summary (what passed, what remains)
- Definition of done for agent-executed tasks:
  - acceptance criteria implemented
  - tests added/updated and passing
  - no new lint/type errors
  - reproducible verification output captured
- Prefer small, verifiable increments so agents can iterate quickly and recover from failures.

## 8) Data Requirements

Persist at minimum:
- users/auth records
- chat sessions
- chat messages
- execution traces (tools/skills/MCP events linked to message)
- model + provider settings
- MCP server configs
- skill configs
- file metadata and ingestion status

Tech constraints:
- Relational data: SQLite
- Vector data: ChromaDB

## 9) UX Requirements

- Clean, minimal chat-first layout.
- Execution trace collapsed by default; fast to expand.
- Clear visual distinction between:
  - assistant content
  - tool/mcp/skill operations
  - errors and retries
- Streaming must feel responsive and stable.
- UI must feel bespoke and intentional (not template-like), while still using `shadcn/ui` primitives for core interaction patterns.

## 10) MVP Feature Additions (Important + Not Overengineered)

These are the key missing features worth adding now:
- **Conversation management basics:** rename/delete chats.
- **Retry controls:** regenerate last response on failure.
- **File/source visibility:** show which sources were used for retrieved answers.
- **Basic import/export:** JSON export of chat sessions for backup.
- **Health diagnostics panel:** quick status check for configured model/search/MCP endpoints.

## 11) Milestones

### Milestone 1: Core Chat + Auth
- Auth, chat UI, streaming, markdown/code rendering, theme support, FastAPI backend skeleton.

### Milestone 2: Configurable Runtime
- Settings pages for models/embeddings/reranker/search + backend config persistence and validation.

### Milestone 3: MCP + Skills + Trace Persistence
- MCP + skills integration with full execution trace UI + DB persistence.

### Milestone 4: Simple Retrieval
- File upload/ingestion/retrieval with SQLite + ChromaDB and source display.

### Milestone 5: Backend Hardening
- Add retries/timeouts, structured error handling, and health-check endpoints for configured services.

### Milestone 6: Quality Automation + Autopilot Readiness
- Establish test harness (Vitest, pytest, Playwright), CI checks, and task verification templates.
- Ensure coding agents can run full implement/validate/fix loops without manual intervention.

## 12) Risks and Mitigations

- **Risk:** Overly complex retrieval implementation.
  - **Mitigation:** keep MVP to simple chunk/embed/retrieve pipeline.
- **Risk:** Local endpoint instability/timeouts.
  - **Mitigation:** retries, timeout controls, health checks, clear UI error states.
- **Risk:** Trace data becoming too noisy.
  - **Mitigation:** compact default view with expandable details and truncation.

## 13) References

- Claude-style chat inspiration: [https://claude.ai/new](https://claude.ai/new)
- MCP docs: [https://modelcontextprotocol.io/docs/getting-started/intro](https://modelcontextprotocol.io/docs/getting-started/intro)
- Skills docs:
  - [https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
  - [https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise)
- Tool use docs:
  - [https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
  - [https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool)
  - [https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool)
  - [https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool)
  - [https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
  - [https://platform.claude.com/docs/en/agents-and-tools/tool-use/bash-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/bash-tool)
  - [https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)

## 14) Environment Configuration Note

Use `.env.example` as the reference contract for configurable runtime values, including:
- model endpoints and keys
- embedding/reranker parameters
- retrieval toggles
- web search provider setup
- app/auth/database settings

## 15) Engineering Constraints (Frontend)

- Use `Next.js` for frontend routes, layout, and rendering.
- Use `shadcn/ui` as the default component foundation across the product.
- Avoid creating parallel custom component systems that duplicate `shadcn/ui`.
- Maintain accessibility baselines by relying on Radix-backed behavior for interactive UI primitives.

## 16) Engineering Constraints (Backend)

- Use Python + FastAPI as the backend foundation for MVP.
- Keep orchestration code framework-agnostic; avoid hard coupling to agentic frameworks during MVP.
- Treat every tool/skill/MCP action as a first-class persisted trace event.
- Use configurable timeout/retry settings for all external calls (model/search/MCP providers).

## 17) Engineering Constraints (Testing and CI)

- Testing is mandatory, not optional, for MVP features.
- Maintain fast feedback:
  - unit/integration tests should run quickly in local dev loops
  - E2E suite can be scoped by tags/projects for targeted runs
- Keep flaky tests near zero; quarantine and fix quickly when detected.
- Agents should use deterministic fixtures/mocks for unstable external dependencies.
- CI should expose clear pass/fail stages: lint, type-check, unit/integration, E2E-smoke, build.