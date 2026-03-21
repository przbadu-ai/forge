# Stack Research

**Domain:** Local-first AI assistant — Next.js frontend, Python/FastAPI backend
**Researched:** 2026-03-21
**Confidence:** HIGH (versions verified against PyPI/npm as of research date)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Next.js | 16.2.0 | Frontend framework | App Router is production-stable; React 19.2 Server Components reduce client JS; Turbopack build now in beta. Latest stable as of March 2026. |
| TypeScript | 5.x (bundled with Next.js) | Type safety across frontend | Strict mode enforced in PROJECT.md; shadcn/ui requires TS. |
| Tailwind CSS | 4.x | Utility-first styling | Pairs natively with shadcn/ui; zero-runtime CSS, best DX for rapid iteration. |
| shadcn/ui | latest (copy-paste model) | Component primitives | Not a dependency — components are owned code. Radix UI primitives + Tailwind. Accessible, unstyled by default; won't fight custom identity. |
| Python | 3.12 | Backend runtime | 3.12 has best package support + performance; 3.13 support still trailing in ML libs (sentence-transformers). Avoid 3.11 — crypt module deprecation breaks passlib. |
| FastAPI | 0.135.1 | Backend API framework | 0.135.0+ includes native SSE support (EventSourceResponse), eliminating the need for sse-starlette. Pydantic V2 native. |
| Pydantic | 2.x (bundled with FastAPI 0.135+) | Request/response validation | V2 is 5-50x faster than V1; FastAPI 0.115+ requires it. |
| SQLite | 3.x (stdlib) | Primary relational store | Zero-config, file-based, WAL mode for concurrent reads. Perfect for single-user local-first. |
| SQLModel | 0.0.22+ | ORM / schema definition | Combines SQLAlchemy 2.0 + Pydantic 2 models in one class — eliminates duplication. Maintained by FastAPI author. |
| SQLAlchemy | 2.0.35+ | Async DB engine | aiosqlite driver enables true async SQLite access. SQLModel 0.0.22 targets SA 2.0. |
| Alembic | 1.13.x | Schema migrations | Standard migration tool for SQLAlchemy. Must import sqlmodel types in env.py. |
| ChromaDB | 1.5.5 | Vector store for RAG | Local-first, embedded mode (no server needed), SQLite-backed persistence. Native Python client. Latest: 1.5.5 (March 2026). |

---

### Supporting Libraries — Backend (Python)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openai | 2.29.0 | OpenAI-compatible API client | All LLM calls — works against Ollama, LM Studio, vLLM, and remote APIs via `base_url` override. Includes `AsyncOpenAI` for non-blocking streaming. |
| mcp | 1.26.0 | MCP client + server SDK | Official `modelcontextprotocol/python-sdk`. Use `ClientSession` to connect to external MCP servers and invoke tools. Targets spec 2025-11-25. |
| aiosqlite | 0.21.x | Async SQLite driver | Required by SQLAlchemy async engine with `sqlite+aiosqlite:///` URLs. |
| httpx | 0.27.x | Async HTTP client | Used by openai library internally; also used directly for health-check endpoints and external calls. Already a FastAPI dependency. |
| python-multipart | 0.0.x | Form / file upload parsing | Required by FastAPI for `UploadFile` endpoints. File chunking for RAG ingestion. |
| python-jose[cryptography] | 3.3.x | JWT encode/decode | Used for session tokens. Maintained; `python-jose[cryptography]` is the variant with RSA/EC support. |
| pwdlib[bcrypt] | 0.2.x | Password hashing | FastAPI now officially recommends pwdlib over passlib. passlib is abandoned and breaks on Python 3.13. |
| sentence-transformers | 3.x | Local embedding generation | Runs HuggingFace models locally (no API key). `all-MiniLM-L6-v2` (384-dim) is default — 4x less CPU than OpenAI 1536-dim. Used to embed uploaded files for ChromaDB. |
| uvicorn[standard] | 0.30.x | ASGI server | Production ASGI server for FastAPI. `[standard]` adds uvloop + httptools for performance. |
| ruff | 0.4.x | Linter + formatter | Replaces flake8 + isort. 10-100x faster than pylint. PROJECT.md mandates it. |
| black | 24.x | Code formatter | Opinionated formatter; ruff's formatter is compatible but black is the explicit project requirement. |
| mypy | 1.10.x | Static type checking | PROJECT.md mandates mypy. Run with `--strict` for full coverage. |

---

### Supporting Libraries — Backend (Testing)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.x | Test runner | Standard Python test runner. |
| pytest-asyncio | 0.23.x | Async test support | Required for `async def` test functions. Use `asyncio_mode = "auto"` in pytest.ini to avoid per-test decoration. |
| httpx (AsyncClient) | 0.27.x | FastAPI async test client | Use `AsyncClient(transport=ASGITransport(app=app))` instead of FastAPI's sync `TestClient` for async endpoints and SSE. |
| pytest-cov | 5.x | Coverage reporting | Standard coverage tooling. |
| factory-boy | 3.x | Test data factories | Build model instances in tests without fixture sprawl. |

---

### Supporting Libraries — Frontend (Next.js)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| react-markdown | 9.x | Markdown rendering | Render assistant message content. Composable with custom renderers for code blocks. |
| remark-gfm | 4.x | GFM tables/strikethrough | Extends react-markdown with GitHub Flavored Markdown support. |
| rehype-highlight | 7.x | Syntax highlighting | Applies highlight.js classes to fenced code blocks. Lightweight, server-compatible. |
| highlight.js | 11.x | Highlight.js theme + runtime | Provides language support and CSS themes for rehype-highlight. |
| zustand | 5.x | Global client state | Conversation list, active chat, settings state. Minimal boilerplate; hook-first. Better than Context for non-tree state. |
| @tanstack/react-query | 5.x | Server state / data fetching | History fetches, settings CRUD, health checks. Handles caching, refetching, optimistic updates. |
| next-themes | 0.3.x | Light/dark/system theme | Drop-in for shadcn/ui's theme system. Works with Tailwind `dark:` variants. |
| lucide-react | 0.400+ | Icon library | Official icon set used by shadcn/ui. Tree-shakeable SVG components. |
| @radix-ui/* | 2.x | Accessible UI primitives | Used by shadcn/ui internally. Install as needed per component. |
| clsx | 2.x | Conditional classNames | Used in shadcn/ui's `cn()` utility. Minimal, type-safe. |
| tailwind-merge | 2.x | Tailwind class deduplication | Pairs with clsx in `cn()`. Prevents duplicate Tailwind class conflicts. |

---

### Supporting Libraries — Frontend (Testing)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| vitest | 2.x | Unit/integration test runner | Vite-native, faster than Jest for Next.js projects. PROJECT.md mandates it. |
| @testing-library/react | 16.x | Component testing utilities | DOM-based component testing; encourages testing behavior not implementation. |
| @testing-library/user-event | 14.x | Realistic user interaction simulation | Simulates typing, clicking, pasting — more realistic than fireEvent. |
| @vitejs/plugin-react | 4.x | React plugin for Vitest | Required for JSX transform in Vitest. |
| jsdom | 24.x | Browser DOM simulation | Vitest `environment: "jsdom"` for component tests. |
| @playwright/test | 1.44.x | E2E testing | Tests full SSE streaming flows, navigation, auth — things unit tests cannot cover. |
| msw | 2.x | API mocking (service worker) | Mock FastAPI responses in Vitest. Avoids network calls in unit tests. |

---

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| ESLint 9 | Frontend linting | Next.js 16 ships with ESLint 9 config. Use `eslint-config-next`. |
| Prettier | Frontend formatting | Configure with `prettier-plugin-tailwindcss` to auto-sort Tailwind classes. |
| vite-tsconfig-paths | TypeScript path aliases in Vitest | Maps `@/` imports in tests. Required alongside `vitest.config.ts`. |
| uv | Python package manager | Faster than pip; lock-file based. Run `uv add` / `uv sync`. |
| alembic | Database migrations | `alembic revision --autogenerate` detects SQLModel schema changes. |

---

## SSE Streaming Implementation Pattern

FastAPI 0.135.0+ includes native SSE. The pattern for streaming LLM tokens is:

**Backend (FastAPI):**
```python
from fastapi import FastAPI
from fastapi.responses import EventSourceResponse  # native in 0.135+
from openai import AsyncOpenAI

async def token_generator(messages):
    client = AsyncOpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)
    async with client.chat.completions.stream(model=settings.model, messages=messages) as stream:
        async for text in stream.text_stream:
            yield {"data": text}

@app.post("/chat/{conversation_id}/stream")
async def stream_chat(conversation_id: str, body: ChatRequest):
    return EventSourceResponse(token_generator(body.messages))
```

**Frontend (Next.js App Router):**
Use `fetch` with a POST body (EventSource API only supports GET). Read with `ReadableStream`:
```typescript
const response = await fetch("/api/chat/stream", { method: "POST", body: JSON.stringify(payload) });
const reader = response.body!.getReader();
const decoder = new TextDecoder();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value);
  // parse "data: ..." lines
}
```

Do NOT use native `EventSource` for POST-based streaming — it only supports GET and cannot send a body.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| openai (Python) | litellm | litellm is better if you need automatic provider routing and fallbacks (OpenAI → Anthropic → Cohere). For a single-endpoint local assistant, openai is lighter. |
| sentence-transformers | OpenAI embeddings API | Use OpenAI embeddings if the user has configured an API key and wants no local ML overhead. Implement a pluggable embedding interface to swap. |
| SQLModel | SQLAlchemy + Pydantic (separate) | Pure SQLAlchemy gives more control for complex queries. SQLModel is the right default for this use case where models double as API schemas. |
| mcp (Python SDK) | Custom HTTP client to MCP servers | Only roll your own if the SDK is too heavy. mcp 1.26.0 supports stdio, SSE, and Streamable HTTP transports — use it. |
| react-markdown + rehype-highlight | assistant-ui | assistant-ui is a full opinionated component kit. For a custom-identity UI (as PROJECT.md requires), own the rendering layer with react-markdown primitives. |
| zustand + @tanstack/react-query | Redux Toolkit | Redux is appropriate for large teams needing strict conventions. For a solo-developer tool, zustand + react-query is less boilerplate. |
| pwdlib[bcrypt] | passlib | passlib is unmaintained and throws DeprecationWarning on Python 3.11+, is broken on 3.13. Do not use. |
| FastAPI native SSE (0.135+) | sse-starlette | sse-starlette (3.3.3) remains valid but is now redundant. Use native FastAPI SSE unless you need its multi-broadcast event bus features. |
| ChromaDB embedded | Qdrant / Weaviate / Pinecone | Qdrant is better for multi-user or high-volume production. For local-first single-user, ChromaDB embedded is zero-config. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| passlib | Abandoned 3+ years. Breaks on Python 3.12+ with DeprecationWarning; broken on 3.13. | pwdlib[bcrypt] |
| LangChain / LangGraph | PROJECT.md explicitly excludes agent frameworks. Adds hidden complexity and version churn. | Custom orchestration loop |
| EventSource (browser API) | Only supports GET requests — cannot send chat payloads. | fetch() + ReadableStream reader |
| WebSockets (for token streaming) | Heavier protocol, requires connection management. SSE is sufficient for unidirectional token streaming. | SSE via EventSourceResponse |
| redis (for state) | Overkill for single-user local-first. Adds infrastructure dependency. | SQLite for persistence, in-memory for run state |
| Celery / task queues | Not needed for single-user synchronous orchestration loop. | asyncio background tasks via FastAPI `BackgroundTasks` |
| next-auth v4 | v4 is deprecated; v5 (Auth.js) has major API changes. Single-user password auth doesn't need OAuth complexity. | Custom JWT via python-jose in FastAPI |
| Python 3.11 | crypt module removed in 3.12+, passlib breaks. Smaller performance improvements. | Python 3.12 |
| axios | Heavier than native fetch; React Query's fetcher handles retry/caching. | fetch() + @tanstack/react-query |

---

## Stack Patterns by Variant

**If user configures Ollama as LLM endpoint:**
- Use `AsyncOpenAI(base_url="http://localhost:11434/v1", api_key="ollama")`
- Ollama exposes an OpenAI-compatible REST API — no special client needed.

**If user wants remote embeddings instead of local:**
- Implement `EmbeddingProvider` interface with `LocalEmbedder` (sentence-transformers) and `OpenAIEmbedder` (openai client)
- ChromaDB supports custom embedding functions — swap at config time.

**If SSE doesn't work behind a proxy:**
- Set `X-Accel-Buffering: no` header on the SSE response
- Nginx must have `proxy_buffering off` for SSE connections.

**For MCP server connections:**
- Use `mcp.ClientSession` with `StdioServerParameters` for local process MCP servers
- Use `mcp.ClientSession` with `SSEServerParameters` for remote HTTP-based MCP servers

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| sqlmodel 0.0.22 | sqlalchemy 2.0.35, pydantic 2.x | SQLModel 0.0.22 officially targets SA 2.0. Earlier SQLModel versions required SA 1.4. |
| fastapi 0.135.x | pydantic 2.x | FastAPI 0.115+ dropped Pydantic V1 support. |
| mcp 1.26.0 | anyio 4.x, httpx 0.27.x, pydantic 2.x | mcp pins anyio >=4. Don't use anyio 3.x. |
| chromadb 1.5.5 | Python 3.8-3.12 | Python 3.13 support is not confirmed for ChromaDB 1.5.x — use Python 3.12. |
| sentence-transformers 3.x | torch 2.x, transformers 4.x | Heavy transitive dependencies. Install separately and consider optional import to keep startup fast. |
| openai 2.29.0 | Python 3.9-3.14 | asyncio-native via httpx. No special setup needed for async. |
| pytest-asyncio 0.23.x | pytest 8.x, asyncio | Set `asyncio_mode = "auto"` in pyproject.toml `[tool.pytest.ini_options]`. Otherwise every async test needs `@pytest.mark.asyncio`. |

---

## Installation

```bash
# ---- Backend ----
# Core runtime
uv add "fastapi[standard]" uvicorn[standard] pydantic sqlmodel alembic aiosqlite

# AI / LLM
uv add openai mcp sentence-transformers chromadb

# Auth
uv add "python-jose[cryptography]" "pwdlib[bcrypt]"

# HTTP utilities
uv add httpx python-multipart

# Dev & quality gates
uv add --dev pytest pytest-asyncio pytest-cov httpx factory-boy ruff black mypy

# ---- Frontend ----
# Core
npm install next react react-dom typescript tailwindcss

# shadcn/ui (run interactively)
npx shadcn@latest init

# Rendering
npm install react-markdown remark-gfm rehype-highlight highlight.js

# State management
npm install zustand @tanstack/react-query next-themes lucide-react clsx tailwind-merge

# Testing
npm install -D vitest @vitejs/plugin-react @testing-library/react @testing-library/user-event jsdom vite-tsconfig-paths msw @playwright/test
```

---

## Sources

- [FastAPI PyPI](https://pypi.org/project/fastapi/) — version 0.135.1 confirmed; native SSE in 0.135.0
- [openai PyPI](https://pypi.org/project/openai/) — version 2.29.0 confirmed
- [mcp PyPI](https://pypi.org/project/mcp/) — version 1.26.0 confirmed, spec 2025-11-25
- [@modelcontextprotocol/sdk npm](https://www.npmjs.com/package/@modelcontextprotocol/sdk) — version 1.27.1
- [chromadb PyPI](https://pypi.org/project/chromadb/) — version 1.5.5 confirmed
- [FastAPI SSE docs](https://fastapi.tiangolo.com/tutorial/server-sent-events/) — native SSE pattern
- [FastAPI async tests](https://fastapi.tiangolo.com/advanced/async-tests/) — httpx AsyncClient pattern
- [passlib deprecation discussion](https://github.com/fastapi/fastapi/discussions/11773) — passlib abandoned; pwdlib recommended
- [SQLModel + Alembic](https://testdriven.io/blog/fastapi-sqlmodel/) — SA 2.0 async pattern
- [Next.js 16](https://nextjs.org/blog) — version 16.2.0 confirmed March 2026
- [sse-starlette PyPI](https://pypi.org/project/sse-starlette/) — version 3.3.3; now redundant
- [Zustand State of React 2025](https://2025.stateofreact.com/en-US/libraries/state-management/) — leading satisfaction rating

---

*Stack research for: Forge — local-first AI assistant*
*Researched: 2026-03-21*
