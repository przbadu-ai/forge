# Phase 1: Infrastructure Foundation - Research

**Researched:** 2026-03-21
**Domain:** Project scaffolding — FastAPI backend, Next.js 16 frontend, SQLite async DB, Alembic migrations, dev tooling
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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
- **D-11:** Next.js 15+ App Router with TypeScript strict mode
- **D-12:** shadcn/ui initialized with default theme
- **D-13:** Tailwind CSS 4
- **D-14:** ESLint + Prettier for linting/formatting
- **D-15:** Vitest + @testing-library/react for unit/component tests
- **D-16:** Playwright installed but E2E tests deferred to later phases
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

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TEST-04 | CI validates: lint, type-check, unit/integration tests, E2E smoke, build | Covered by dev tooling research (Makefile targets, pytest, Vitest, ruff/mypy/ESLint/tsc); CI skeleton with GitHub Actions |
</phase_requirements>

---

## Summary

Phase 1 establishes the full project skeleton for Forge: a Python 3.12 FastAPI backend with async SQLite (WAL mode + aiosqlite), SQLModel models, and Alembic batch migrations, alongside a Next.js 16 frontend with TypeScript strict mode, shadcn/ui (Tailwind v4), and Vitest. The monorepo is wired together with a Makefile that runs both servers concurrently and provides single-command access to test/lint/type-check operations.

The primary technical risks in this phase are: (1) SQLite locking errors from missing WAL + busy_timeout pragmas on the async engine; (2) Alembic migrations silently failing on SQLite ALTER TABLE without `render_as_batch=True`; and (3) pytest-asyncio 1.x having removed the `event_loop` fixture and changed default mode to `strict`, requiring explicit `asyncio_mode = "auto"` configuration. All three have deterministic fixes that must be applied at scaffold time.

**Primary recommendation:** Set up WAL + busy_timeout via a `@event.listens_for(engine.sync_engine, "connect")` hook, apply `render_as_batch=True` in both offline and online Alembic migration paths, and configure `asyncio_mode = "auto"` + `asyncio_default_fixture_loop_scope = "function"` in `pyproject.toml` to be compatible with pytest-asyncio 1.x.

---

## Standard Stack

### Core — Backend

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12 | Runtime | Best package compatibility; 3.13 not yet supported by ChromaDB/sentence-transformers |
| uv | latest | Package manager | Lock-file based, 10x faster than pip; replaces pip/poetry |
| fastapi[standard] | 0.135.1 | API framework | Native SSE (EventSourceResponse) in 0.135+; Pydantic v2 native |
| uvicorn[standard] | 0.42.0 | ASGI server | Production ASGI; [standard] adds uvloop + httptools |
| pydantic | 2.x (bundled) | Validation | V2 included with FastAPI 0.115+; 5-50x faster than V1 |
| sqlmodel | 0.0.37 | ORM + schema | Combines SQLAlchemy 2.0 + Pydantic 2 in one class; no duplication |
| sqlalchemy | 2.0.48 | Async DB engine | async engine via aiosqlite; SQLModel targets SA 2.0 |
| alembic | 1.18.4 | Migrations | Standard SQLAlchemy migration tool; must enable batch mode for SQLite |
| aiosqlite | 0.22.1 | Async SQLite driver | Required for `sqlite+aiosqlite:///` connection URLs |
| httpx | 0.28.1 | HTTP client | Used by openai SDK; also for health checks and async test client |

**Version verification:** All versions confirmed against PyPI on 2026-03-21.

### Core — Frontend

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| next | 16.2.1 | Framework | App Router stable; React 19 Server Components; Turbopack beta |
| typescript | 5.x (bundled) | Type safety | Strict mode required per project constraints |
| tailwindcss | 4.2.2 | Styling | v4 natively supported by shadcn/ui; zero-runtime CSS |
| shadcn/ui | latest (CLI) | Component primitives | Copy-paste model — owned code, not a dependency; Radix + Tailwind |
| react | 19.x (bundled) | UI runtime | Bundled with Next.js 16 |

### Supporting — Backend Quality + Testing

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ruff | 0.15.7 | Linter | Replaces flake8 + isort; 10-100x faster |
| black | 26.3.1 | Formatter | Opinionated formatter; project constraint |
| mypy | 1.19.1 | Type checker | Run with `--strict` mode |
| pytest | 9.0.2 | Test runner | Standard Python test runner |
| pytest-asyncio | 1.3.0 | Async test support | Required for `async def` tests; configure `asyncio_mode = "auto"` |
| httpx (AsyncClient) | 0.28.1 | Test HTTP client | `AsyncClient(transport=ASGITransport(app=app))` for async endpoint tests |
| pytest-cov | latest | Coverage | Standard coverage tooling |

### Supporting — Frontend Quality + Testing

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| eslint | 9.x (bundled) | Linter | Next.js 16 ships ESLint 9 with `eslint-config-next` |
| prettier | latest | Formatter | With `prettier-plugin-tailwindcss` for class sorting |
| vitest | 4.1.0 | Test runner | Vite-native; faster than Jest for Next.js |
| @testing-library/react | 16.3.2 | Component testing | DOM-based; tests behavior not implementation |
| @testing-library/user-event | 14.6.1 | User interaction simulation | More realistic than fireEvent |
| @vitejs/plugin-react | 4.x | React plugin | Required for JSX transform in Vitest |
| jsdom | 29.0.1 | DOM simulation | `environment: "jsdom"` in Vitest config |
| vite-tsconfig-paths | latest | Path alias support | Maps `@/` imports in Vitest tests |
| @playwright/test | 1.58.2 | E2E testing (deferred) | Install skeleton now; tests deferred to later phases |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| uv | pip / poetry | uv is faster and lock-file based; pip has no lock file; poetry is slower |
| SQLModel | SQLAlchemy + Pydantic (separate) | SQLModel reduces code duplication; pure SA gives more complex query control |
| Alembic batch mode | PostgreSQL | Batch mode is the SQLite workaround; PostgreSQL would not need it but violates project constraints |
| pytest-asyncio auto mode | Per-test @pytest.mark.asyncio | Auto mode removes decorator boilerplate; strict mode is default in v1.x |
| make -j | npm concurrently | `make -j 2` is zero-dependency; `concurrently` requires npm install |

### Installation

```bash
# ---- Backend ----
cd backend
uv init --name forge-backend --python 3.12
uv add "fastapi[standard]" "uvicorn[standard]" sqlmodel alembic aiosqlite httpx

# Dev dependencies
uv add --dev pytest pytest-asyncio pytest-cov httpx ruff black mypy

# ---- Frontend ----
cd frontend
npx create-next-app@latest . --typescript --app --tailwind --eslint --src-dir
npx shadcn@latest init -t next

# Testing
npm install -D vitest @vitejs/plugin-react @testing-library/react @testing-library/user-event jsdom vite-tsconfig-paths @playwright/test

# Formatting
npm install -D prettier prettier-plugin-tailwindcss
```

---

## Architecture Patterns

### Recommended Project Structure

```
forge/                          # repo root
├── Makefile                    # single entry point: dev, test, lint, build
├── .env.example                # documented configuration contract
├── .env                        # gitignored
├── backend/
│   ├── pyproject.toml          # uv project config + ruff/black/mypy/pytest settings
│   ├── uv.lock
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py              # SQLModel metadata, render_as_batch=True
│   │   └── versions/
│   └── app/
│       ├── __init__.py
│       ├── main.py             # create_app() factory + lifespan, export `app`
│       ├── core/
│       │   ├── config.py       # pydantic Settings (BaseSettings) reading .env
│       │   └── database.py     # engine, async session factory, WAL pragma hook
│       ├── api/
│       │   └── v1/             # router mounting point for /api/v1/
│       │       └── router.py
│       ├── models/             # SQLModel table models
│       └── tests/
│           ├── conftest.py     # test app fixture, db engine override
│           └── test_health.py  # skeleton test: GET /health returns 200
├── frontend/
│   ├── package.json
│   ├── tsconfig.json           # strict: true
│   ├── vitest.config.ts
│   ├── .prettierrc
│   ├── next.config.ts
│   └── src/
│       ├── app/                # Next.js App Router pages
│       │   └── page.tsx
│       ├── components/
│       │   └── ui/             # shadcn/ui copied components land here
│       └── __tests__/          # Vitest unit/component tests
│           └── placeholder.test.tsx
└── .github/
    └── workflows/
        └── ci.yml              # lint, type-check, test, build
```

### Pattern 1: FastAPI App Factory with Lifespan

**What:** `create_app()` returns a configured FastAPI instance; startup/shutdown handled by `@asynccontextmanager` lifespan.
**When to use:** Always — enables test isolation (each test gets a fresh app instance with overridden settings).

```python
# Source: https://fastapi.tiangolo.com/advanced/events/
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import create_db_and_tables
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_db_and_tables()
    yield
    # Shutdown — dispose engine here if needed

def create_app() -> FastAPI:
    app = FastAPI(
        title="Forge API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,  # ["http://localhost:3000"]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    return app

app = create_app()
```

### Pattern 2: Async SQLite Engine with WAL + busy_timeout

**What:** SQLAlchemy async engine configured with WAL mode and busy timeout via sync engine event hook.
**When to use:** All SQLite database access in FastAPI — set up once in `database.py`.

```python
# Source: SQLAlchemy 2.0 docs + verified pattern
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

DATABASE_URL = "sqlite+aiosqlite:///./forge.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # set True for debug SQL logging
    connect_args={"check_same_thread": False},
    poolclass=NullPool,  # avoid sharing connections across coroutines
)

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA synchronous=NORMAL")  # safe with WAL; faster
    cursor.close()

AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        yield session

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
```

**Critical note:** The `@event.listens_for` must target `engine.sync_engine` (not `engine`) when using async engines. The `NullPool` prevents the "cannot reuse connections across event loop" error common with aiosqlite.

### Pattern 3: Alembic env.py with SQLModel + Batch Mode

**What:** Alembic env.py configured to use SQLModel's metadata and `render_as_batch=True` for SQLite compatibility.
**When to use:** Required for any SQLite project — enables column drops, renames, constraint changes.

```python
# alembic/env.py — critical sections
# Source: https://alembic.sqlalchemy.org/en/latest/batch.html
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from sqlmodel import SQLModel

# IMPORTANT: import all models here so metadata is populated
import app.models  # noqa: F401 — ensures all SQLModel tables are registered

config = context.config
fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata  # NOT Base.metadata

def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # REQUIRED for SQLite
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,  # REQUIRED for SQLite
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Pattern 4: pytest-asyncio 1.x Configuration

**What:** pytest-asyncio 1.0 removed the `event_loop` fixture and changed default mode to `strict`. Configure `auto` mode explicitly.
**When to use:** All Python async tests.

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"

[tool.pytest.ini_options]
testpaths = ["app/tests"]
```

**Breaking change from 0.23.x:** Never use the `event_loop` fixture in test code. If loop access is needed inside a test, use `asyncio.get_running_loop()`. Custom loop scope is set via `@pytest.mark.asyncio(loop_scope="module")` or `@pytest_asyncio.fixture(loop_scope="session")`.

### Pattern 5: FastAPI CORS for Direct Browser SSE

**What:** CORS middleware configured to allow the Next.js origin to access FastAPI directly — required because SSE streaming connects browser-to-FastAPI (not proxied through Next.js).
**When to use:** Required when browser SSE/fetch connects to FastAPI at port 8000 directly.

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from typing import list

class Settings(BaseSettings):
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

```python
# In create_app():
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Cache-Control"],  # SSE headers
)
```

### Pattern 6: Vitest Configuration for Next.js App Router

**What:** Vitest configured with jsdom, path aliases, and React plugin for Next.js App Router component testing.
**When to use:** All frontend unit/component tests.

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [tsconfigPaths(), react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/__tests__/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json"],
    },
  },
});
```

```typescript
// src/__tests__/setup.ts
import "@testing-library/jest-dom";
```

### Pattern 7: Makefile for Concurrent Dev Servers

**What:** `make dev` starts both Next.js (3000) and FastAPI (8000) in parallel with no additional npm dependencies.
**When to use:** This approach uses `make -j 2` (zero-dependency vs npm `concurrently`).

```makefile
.PHONY: dev test lint type-check backend-dev frontend-dev

dev:
	make -j 2 backend-dev frontend-dev

backend-dev:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

frontend-dev:
	cd frontend && npm run dev

test:
	make -j 2 backend-test frontend-test

backend-test:
	cd backend && uv run pytest

frontend-test:
	cd frontend && npm run test

lint:
	cd backend && uv run ruff check . && uv run black --check .
	cd frontend && npm run lint

type-check:
	cd backend && uv run mypy app/
	cd frontend && npx tsc --noEmit

format:
	cd backend && uv run ruff check --fix . && uv run black .
	cd frontend && npm run format

migrate:
	cd backend && uv run alembic upgrade head
```

**Note:** `make -j 2` sends SIGTERM to all child processes when one exits — this is correct behavior for dev servers (Ctrl+C kills both). Color-prefixed output is not available without `concurrently`, but `make -j 2` requires no npm dependencies.

### Anti-Patterns to Avoid

- **`event_loop` fixture in pytest:** Removed in pytest-asyncio 1.0. Use `asyncio.get_running_loop()` inside async tests instead.
- **Missing `render_as_batch=True`:** Will silently generate broken migrations for any `ALTER TABLE ... DROP COLUMN` on SQLite.
- **`engine` (not `engine.sync_engine`) in `@event.listens_for`:** WAL pragma won't apply — the async engine wrapper doesn't fire sync connection events.
- **`NullPool` omitted:** aiosqlite connections can be shared across coroutines and cause `check_same_thread` errors.
- **`SQLModel.metadata` not populated:** If model files aren't imported before Alembic runs autogenerate, it will generate empty migrations. Always import models in `env.py`.
- **`passlib` instead of `pwdlib`:** passlib is abandoned; throws DeprecationWarning on Python 3.12, broken on 3.13.
- **`tailwindcss-animate` instead of `tw-animate-css`:** `tailwindcss-animate` is deprecated in shadcn/ui for Tailwind v4; new projects use `tw-animate-css`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SQLite WAL pragma | Custom connection hook | `@event.listens_for(engine.sync_engine, "connect")` | Correct hook point for async engines |
| Schema migrations | Manual SQL ALTER | Alembic with `render_as_batch=True` | SQLite ALTER limitations are complex; batch mode handles automatically |
| Async test client | Custom ASGI test client | `httpx.AsyncClient(transport=ASGITransport(app=app))` | FastAPI official pattern; handles auth headers, cookies, streams |
| CORS headers manually | Custom middleware | `fastapi.middleware.cors.CORSMiddleware` | Handles preflight OPTIONS, credentials, expose_headers correctly |
| Path aliases in Vitest | Manual resolve config | `vite-tsconfig-paths` plugin | Reads existing `tsconfig.json` paths — no duplication |
| Frontend/backend concurrent dev | tmux / screen / custom shell | `make -j 2` | Zero-dependency; kills both on Ctrl+C |
| Settings loading | `os.environ` directly | `pydantic_settings.BaseSettings` | Type-safe, validates on startup, supports .env files |

**Key insight:** The SQLite + async SQLAlchemy combination has enough setup complexity (WAL pragma placement, NullPool, check_same_thread) that any deviation from the established pattern reliably produces intermittent bugs that are hard to reproduce in testing but consistent in production.

---

## Common Pitfalls

### Pitfall 1: SQLite "database is locked" Without WAL Mode
**What goes wrong:** `sqlite3.OperationalError: database is locked` under async concurrent requests — even with a single user and no explicit concurrency.
**Why it happens:** FastAPI is async; without WAL mode, any pending write blocks all reads. `aiosqlite` with default pool can share connections across coroutines.
**How to avoid:** Set `PRAGMA journal_mode=WAL` + `PRAGMA busy_timeout=5000` via `@event.listens_for(engine.sync_engine, "connect")`. Use `NullPool`.
**Warning signs:** Error only appears under "fast clicking" or multiple tabs; works in sequential pytest but fails with `-n 4`.

### Pitfall 2: Alembic Migration Fails on Schema Change
**What goes wrong:** `alembic upgrade head` fails with `NotSupportedError` on any migration that drops columns, renames columns, or modifies constraints.
**Why it happens:** SQLite `ALTER TABLE` only supports `ADD COLUMN` and `RENAME TABLE`. Alembic generates standard SQL that works on PostgreSQL but not SQLite unless batch mode rewrites it.
**How to avoid:** Add `render_as_batch=True` to BOTH `run_migrations_offline()` and `run_migrations_online()` in `env.py`. Apply at scaffold time before any migrations exist.
**Warning signs:** Migration works on empty DB but fails on DB with existing rows; schema drifts when developers recreate DB instead of migrating.

### Pitfall 3: WAL Pragma Not Applied on Async Engine
**What goes wrong:** WAL mode never activates even though the code looks correct. `PRAGMA journal_mode;` query returns `delete` not `wal`.
**Why it happens:** `@event.listens_for(engine, "connect")` does not fire on the async engine wrapper. Must target `engine.sync_engine`.
**How to avoid:** Always use `@event.listens_for(engine.sync_engine, "connect")`.
**Warning signs:** No error thrown; WAL simply doesn't activate. Check with `SELECT * FROM pragma_journal_mode;`.

### Pitfall 4: pytest-asyncio 1.x `event_loop` Fixture Removed
**What goes wrong:** Tests using `event_loop` fixture fail with `fixture 'event_loop' not found` after upgrading to pytest-asyncio 1.x.
**Why it happens:** pytest-asyncio 1.0 removed the `event_loop` fixture entirely. Default mode is now `strict` (not `auto`).
**How to avoid:** Set `asyncio_mode = "auto"` in `pyproject.toml`. Replace any `event_loop` usage with `asyncio.get_running_loop()`. Use `loop_scope` parameter for scoped fixtures.
**Warning signs:** `fixture 'event_loop' not found` error; async tests silently pass as sync tests in strict mode without markers.

### Pitfall 5: shadcn/ui Tailwind v4 Animation Dependency
**What goes wrong:** `tailwindcss-animate` import errors or missing animation utilities after `shadcn init` with Tailwind v4.
**Why it happens:** shadcn/ui v4 support deprecated `tailwindcss-animate` in favor of `tw-animate-css`. New projects default to `tw-animate-css`.
**How to avoid:** After `npx shadcn@latest init`, verify the installed animation library. If using Tailwind v4, ensure `tw-animate-css` is present (not `tailwindcss-animate`).
**Warning signs:** Animation utility classes (`animate-*`) don't work; console errors about missing CSS imports.

### Pitfall 6: SQLModel Models Not Imported Before Alembic Autogenerate
**What goes wrong:** `alembic revision --autogenerate` produces empty migrations even though models exist.
**Why it happens:** SQLModel registers tables in `SQLModel.metadata` only when the model class is imported. If `env.py` never imports the model files, `target_metadata` is empty.
**How to avoid:** In `alembic/env.py`, explicitly import all model modules before `target_metadata = SQLModel.metadata`. Use a wildcard import from a `models/__init__.py` that re-exports all models.
**Warning signs:** `alembic revision --autogenerate -m "init"` generates a migration with no `op.create_table()` calls.

### Pitfall 7: CORS Missing `allow_credentials=True` Breaks Auth Cookies
**What goes wrong:** Browser SSE connections or fetch requests with `credentials: "include"` fail with CORS error despite origins being configured.
**Why it happens:** `allow_credentials=True` is required for cookies and Authorization headers. With wildcard `allow_origins=["*"]`, credentials are not supported — must use explicit origins.
**How to avoid:** Use explicit origin list (`["http://localhost:3000"]`) AND `allow_credentials=True`. Load from environment variable for deploy flexibility.
**Warning signs:** Auth works on same origin but fails when browser connects directly to port 8000; preflight OPTIONS returns 200 but actual request fails.

---

## Code Examples

Verified patterns from official and authoritative sources:

### Backend: pyproject.toml Configuration

```toml
[project]
name = "forge-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]>=0.135.1",
    "uvicorn[standard]>=0.42.0",
    "sqlmodel>=0.0.37",
    "alembic>=1.18.4",
    "aiosqlite>=0.22.1",
    "httpx>=0.28.1",
    "pydantic-settings>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=9.0.2",
    "pytest-asyncio>=1.3.0",
    "pytest-cov",
    "httpx",
    "ruff>=0.15.7",
    "black>=26.3.1",
    "mypy>=1.19.1",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["app/tests"]

[tool.ruff]
target-version = "py312"
line-length = 88
select = ["E", "F", "I", "UP", "N", "S", "B", "A"]

[tool.black]
target-version = ["py312"]
line-length = 88

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true
```

### Backend: Async Test Client Setup (conftest.py)

```python
# Source: https://fastapi.tiangolo.com/advanced/async-tests/
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from app.main import create_app
from app.core.database import get_session

@pytest.fixture
async def app():
    # Use in-memory SQLite for tests — StaticPool keeps one connection
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_session():
        async with test_session_factory() as session:
            yield session

    application = create_app()
    application.dependency_overrides[get_session] = override_get_session
    yield application

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await test_engine.dispose()

@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
```

### Frontend: TypeScript strict tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### Frontend: next.config.ts (SSE streaming safety)

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Disable compression so SSE tokens are not buffered
  // Browser connects directly to FastAPI for SSE; this applies to any
  // Next.js route handlers that might proxy responses.
  compress: false,
};

export default nextConfig;
```

### Frontend: Skeleton Test (placeholder.test.tsx)

```typescript
// src/__tests__/placeholder.test.tsx
import { describe, it, expect } from "vitest";

describe("placeholder", () => {
  it("test infrastructure is working", () => {
    expect(true).toBe(true);
  });
});
```

### Backend: Skeleton Test (test_health.py)

```python
# app/tests/test_health.py
import pytest

async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| passlib for password hashing | pwdlib[bcrypt] | 2023 | passlib abandoned; breaks on Python 3.12+ |
| `@app.on_event("startup")` | `@asynccontextmanager lifespan` | FastAPI 0.95 (2023) | on_event deprecated; lifespan is the current pattern |
| sse-starlette for SSE | FastAPI native `EventSourceResponse` | FastAPI 0.135.0 (2025) | sse-starlette now redundant; native SSE is preferred |
| pytest-asyncio event_loop fixture | `asyncio.get_running_loop()` + loop_scope param | pytest-asyncio 1.0 (2025) | Hard removal; existing code using event_loop fixture breaks |
| tailwindcss-animate | tw-animate-css | shadcn/ui v4 support (2025) | tailwindcss-animate deprecated in Tailwind v4 projects |
| `next-auth v4` | Custom JWT or `auth.js` (v5) | 2024 | next-auth v4 deprecated; v5 has major API changes |
| SQLModel 0.0.21 (SA 1.4) | SQLModel 0.0.22+ (SA 2.0) | 2024 | SA 2.0 async patterns required; SA 1.4 no longer maintained |

**Deprecated/outdated:**
- `@app.on_event("startup")` / `@app.on_event("shutdown")`: deprecated, use lifespan
- `event_loop` pytest fixture: removed in pytest-asyncio 1.0
- `chromadb.Client()` (library mode): deprecated, use `chromadb.PersistentClient()` or `chromadb.HttpClient()`

---

## Open Questions

1. **pytest-asyncio 1.3.0 `asyncio_default_fixture_loop_scope`**
   - What we know: `asyncio_mode = "auto"` is confirmed working; the `asyncio_default_fixture_loop_scope` setting suppresses a deprecation warning in 1.x.
   - What's unclear: Whether `"function"` (default) or `"session"` is more appropriate for the DB session fixture pattern used in conftest.py.
   - Recommendation: Default to `"function"` for isolation; upgrade to `"session"` scoped fixtures only if test suite becomes slow.

2. **uv workspace vs. independent pyproject.toml**
   - What we know: uv supports workspaces (`[tool.uv.workspace]`) for true monorepos. For a frontend + backend split, the backend can be a standalone uv project within the repo.
   - What's unclear: Whether to use a root-level `pyproject.toml` with workspace config or let `backend/pyproject.toml` be self-contained.
   - Recommendation: Keep `backend/pyproject.toml` self-contained (no workspace config) — frontend is npm, not Python. Workspace tooling is for multi-package Python repos.

3. **Alembic `--autogenerate` with SQLModel relationship fields**
   - What we know: SQLModel 0.0.37 targets SA 2.0; `--autogenerate` works for table/column changes. Relationship fields are not reflected in migrations.
   - What's unclear: Whether any SQLModel 0.0.37-specific metadata behavior changed versus 0.0.22.
   - Recommendation: Test autogenerate against the first model (e.g., a `HealthCheck` stub table) before building real models.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Backend Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Frontend Framework | Vitest 4.1.0 |
| Backend config file | `backend/pyproject.toml` `[tool.pytest.ini_options]` |
| Frontend config file | `frontend/vitest.config.ts` |
| Backend quick run | `cd backend && uv run pytest app/tests/ -x` |
| Backend full suite | `cd backend && uv run pytest --cov=app` |
| Frontend quick run | `cd frontend && npx vitest run` |
| Frontend full suite | `cd frontend && npx vitest run --coverage` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-04 | `make lint` passes ruff + black + ESLint + Prettier with zero violations | smoke | `cd backend && uv run ruff check . && uv run black --check .` | ❌ Wave 0 |
| TEST-04 | `make type-check` passes mypy --strict + tsc --noEmit | smoke | `cd backend && uv run mypy app/ --strict` | ❌ Wave 0 |
| TEST-04 | pytest runs with zero failures on skeleton suite | unit | `cd backend && uv run pytest app/tests/ -x` | ❌ Wave 0 |
| TEST-04 | Vitest runs with zero failures on skeleton suite | unit | `cd frontend && npx vitest run` | ❌ Wave 0 |
| TEST-04 | Alembic `upgrade head` completes without error | integration | `cd backend && uv run alembic upgrade head` | ❌ Wave 0 |
| TEST-04 | SQLite WAL mode is active after engine creation | unit | `cd backend && uv run pytest app/tests/test_db.py -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `cd backend && uv run pytest app/tests/ -x` and `cd frontend && npx vitest run`
- **Per wave merge:** Full suite — `uv run pytest --cov=app` + `npx vitest run --coverage` + `mypy` + `tsc --noEmit`
- **Phase gate:** All of: lint, type-check, pytest, vitest, `alembic upgrade head` passing before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `backend/app/tests/conftest.py` — async test client fixture, in-memory DB override
- [ ] `backend/app/tests/test_health.py` — skeleton: GET /health returns 200
- [ ] `backend/app/tests/test_db.py` — verifies WAL mode enabled, busy_timeout set
- [ ] `backend/app/tests/test_migrations.py` — runs `alembic upgrade head` + `alembic downgrade base` against in-memory equivalent
- [ ] `frontend/src/__tests__/setup.ts` — @testing-library/jest-dom import
- [ ] `frontend/src/__tests__/placeholder.test.tsx` — skeleton: Vitest infrastructure check
- [ ] `frontend/vitest.config.ts` — jsdom environment, path aliases, setupFiles

---

## Sources

### Primary (HIGH confidence)

- PyPI fastapi 0.135.1 — version confirmed, native SSE, Pydantic v2
- PyPI sqlmodel 0.0.37 — version confirmed, SA 2.0 target
- PyPI alembic 1.18.4 — version confirmed
- PyPI aiosqlite 0.22.1 — version confirmed
- PyPI pytest-asyncio 1.3.0 — version confirmed, 1.x breaking changes verified
- PyPI ruff 0.15.7, black 26.3.1, mypy 1.19.1 — versions confirmed
- npm next 16.2.1 — version confirmed
- npm tailwindcss 4.2.2 — version confirmed
- npm vitest 4.1.0, @testing-library/react 16.3.2, @playwright/test 1.58.2 — confirmed
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/) — app factory + lifespan pattern
- [FastAPI CORS docs](https://fastapi.tiangolo.com/tutorial/cors/) — CORSMiddleware configuration
- [FastAPI async tests](https://fastapi.tiangolo.com/advanced/async-tests/) — httpx AsyncClient pattern
- [Alembic batch mode docs](https://alembic.sqlalchemy.org/en/latest/batch.html) — render_as_batch usage
- [SQLAlchemy 2.0 dialects/sqlite](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html) — pool and connect_args
- [shadcn/ui Next.js installation](https://ui.shadcn.com/docs/installation/next) — `npx shadcn@latest init -t next`
- [shadcn/ui Tailwind v4](https://ui.shadcn.com/docs/tailwind-v4) — OKLCH colors, tw-animate-css, @theme directive
- [pytest-asyncio 1.3.0 configuration](https://pytest-asyncio.readthedocs.io/en/stable/reference/configuration.html) — asyncio_mode
- [pytest-asyncio v1 migration guide](https://thinhdanggroup.github.io/pytest-asyncio-v1-migrate/) — event_loop removal, loop_scope

### Secondary (MEDIUM confidence)

- [STACK.md](.planning/research/STACK.md) — pre-existing stack research with version notes (HIGH confidence internally)
- [PITFALLS.md](.planning/research/PITFALLS.md) — pre-existing pitfalls research (HIGH confidence internally)
- [FastAPI best practices 2025](https://orchestrator.dev/blog/2025-1-30-fastapi-production-patterns/) — app factory pattern
- [Vitest + Next.js guide 2026](https://noqta.tn/en/tutorials/vitest-react-testing-library-nextjs-unit-testing-2026) — Vitest config patterns
- [SQLite WAL async SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy/discussions/12767) — sync_engine event hook pattern

### Tertiary (LOW confidence — needs validation)

- uv workspace configuration for mixed frontend/backend monorepos — project approach (standalone pyproject.toml) recommended but workspace pattern less studied

---

## Metadata

**Confidence breakdown:**

- Standard stack versions: HIGH — all verified against PyPI and npm registries on 2026-03-21
- Architecture patterns: HIGH — cross-referenced with FastAPI official docs, SQLAlchemy docs, pytest-asyncio docs
- Pitfalls: HIGH — sourced from PITFALLS.md (multi-source verified) plus pytest-asyncio 1.x migration guide
- Test infrastructure: MEDIUM — pytest-asyncio 1.x `asyncio_default_fixture_loop_scope` behavior unverified in production; safest defaults documented

**Research date:** 2026-03-21
**Valid until:** 2026-06-21 (90 days — stack is stable; FastAPI/SQLModel/pytest-asyncio may have point releases but no breaking changes expected)
