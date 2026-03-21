---
phase: 01-infrastructure-foundation
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/pyproject.toml
  - backend/uv.lock
  - backend/app/__init__.py
  - backend/app/main.py
  - backend/app/core/__init__.py
  - backend/app/core/config.py
  - backend/app/api/__init__.py
  - backend/app/api/v1/__init__.py
  - backend/app/api/v1/router.py
  - backend/app/models/__init__.py
  - backend/app/tests/__init__.py
  - backend/app/tests/conftest.py
  - backend/app/tests/test_health.py
  - frontend/package.json
  - frontend/tsconfig.json
  - frontend/next.config.ts
  - frontend/src/app/page.tsx
  - frontend/src/app/layout.tsx
  - frontend/src/lib/utils.ts
  - frontend/src/__tests__/setup.ts
  - frontend/src/__tests__/placeholder.test.tsx
  - frontend/vitest.config.ts
  - frontend/.prettierrc
autonomous: true
requirements:
  - TEST-04

must_haves:
  truths:
    - "Backend FastAPI app starts and GET /health returns 200 JSON"
    - "Frontend Next.js app starts and renders a page at localhost:3000"
    - "pytest skeleton suite passes with zero failures"
    - "Vitest skeleton suite passes with zero failures"
    - "Ruff, Black, mypy pass on backend with zero violations"
    - "ESLint, Prettier, TypeScript strict pass on frontend with zero violations"
  artifacts:
    - path: "backend/pyproject.toml"
      provides: "uv project config, ruff/black/mypy/pytest settings"
      contains: "asyncio_mode = \"auto\""
    - path: "backend/app/main.py"
      provides: "FastAPI create_app() factory with CORS and lifespan"
      exports: ["create_app", "app"]
    - path: "backend/app/core/config.py"
      provides: "Pydantic Settings reading .env"
      exports: ["settings"]
    - path: "backend/app/tests/test_health.py"
      provides: "Skeleton test: GET /health returns 200"
    - path: "frontend/vitest.config.ts"
      provides: "Vitest configuration with jsdom + React plugin + path aliases"
    - path: "frontend/src/__tests__/placeholder.test.tsx"
      provides: "Skeleton Vitest test that passes"
  key_links:
    - from: "backend/app/main.py"
      to: "backend/app/api/v1/router.py"
      via: "include_router(api_router, prefix='/api/v1')"
    - from: "backend/app/tests/conftest.py"
      to: "backend/app/main.py"
      via: "AsyncClient(transport=ASGITransport(app=create_app()))"
---

<objective>
Plans 01-01 and 01-03: Backend and frontend project scaffolds — established concurrently.

01-01 creates the FastAPI backend skeleton: uv environment, pyproject.toml with all quality tool configs, app factory pattern, CORS for browser SSE, pydantic settings, skeleton health endpoint, and a passing pytest suite.

01-03 creates the Next.js 16 frontend skeleton: TypeScript strict mode, shadcn/ui initialization, Tailwind v4, ESLint + Prettier, Vitest configured for jsdom + React + path aliases, and a passing test suite.

Purpose: Establish both foundations in parallel before the database layer (01-02) and dev tooling (01-04) are wired together.
Output: Working backend at localhost:8000 and frontend at localhost:3000 with zero linting/test failures.
</objective>

<execution_context>
Read and follow all patterns from the research files before implementing. The research defines exact patterns to use — do not deviate.
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/01-infrastructure-foundation/1-CONTEXT.md
@.planning/phases/01-infrastructure-foundation/RESEARCH.md
@.planning/research/STACK.md
@.planning/research/PITFALLS.md
</context>

<tasks>

<!-- ═══════════════════════════════════════════════════════════════
     PLAN 01-01: Backend Project Scaffold
     Wave 1 — runs parallel with Plan 01-03
     ═══════════════════════════════════════════════════════════════ -->

<task type="auto">
  <name>Task 01-01-A: Initialize uv backend project and install dependencies</name>
  <files>
    backend/pyproject.toml
    backend/uv.lock
    backend/.python-version
  </files>
  <action>
From the repo root, create the backend directory and initialize the uv project:

```bash
mkdir -p backend
cd backend
uv init --name forge-backend --python 3.12
```

Then add all runtime and dev dependencies:

```bash
# Runtime
uv add "fastapi[standard]" "uvicorn[standard]" sqlmodel alembic aiosqlite httpx pydantic-settings

# Dev/test
uv add --dev pytest pytest-asyncio pytest-cov httpx ruff black mypy
```

After uv init, the generated pyproject.toml will have a minimal `[project]` section. Replace or augment it so pyproject.toml contains the following complete configuration. Keep the `[project]` section that uv generated (it will have the correct name, version, and dependencies list from `uv add`) and ADD the following tool sections:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
ignore = ["E501"]

[tool.black]
line-length = 100
target-version = ["py312"]

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
testpaths = ["app/tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

IMPORTANT: `asyncio_mode = "auto"` is required for pytest-asyncio 1.x (the version installed). Without it, async tests will silently not be collected in strict mode (the new default). Do not use `asyncio_mode = "strict"`.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && uv run python -c "import fastapi, sqlmodel, alembic, aiosqlite; print('deps ok')"</automated>
  </verify>
  <done>All backend runtime and dev dependencies install without errors. pyproject.toml contains ruff, black, mypy, and pytest tool sections with asyncio_mode = "auto".</done>
</task>

<task type="auto">
  <name>Task 01-01-B: Create FastAPI app factory with CORS, settings, and health endpoint</name>
  <files>
    backend/app/__init__.py
    backend/app/main.py
    backend/app/core/__init__.py
    backend/app/core/config.py
    backend/app/api/__init__.py
    backend/app/api/v1/__init__.py
    backend/app/api/v1/router.py
    backend/app/models/__init__.py
  </files>
  <action>
Create the directory structure and files exactly as specified below.

**backend/app/__init__.py** — empty file

**backend/app/core/__init__.py** — empty file

**backend/app/api/__init__.py** — empty file

**backend/app/api/v1/__init__.py** — empty file

**backend/app/models/__init__.py** — empty file for now; Alembic env.py will import this

**backend/app/core/config.py**:
```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Forge"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]
    database_url: str = "sqlite+aiosqlite:///./forge.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

Note: use `model_config` (Pydantic v2 style), NOT the inner `class Config` (Pydantic v1 style). pydantic-settings is a separate package from pydantic v2.

**backend/app/api/v1/router.py**:
```python
from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "forge-api"}
```

**backend/app/main.py**:
```python
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: initialize DB tables in later plans
    yield
    # Shutdown: dispose engine in later plans


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Type", "Cache-Control"],  # required for SSE
    )

    application.include_router(api_router, prefix="/api/v1")

    return application


app = create_app()
```

Type annotation `AsyncGenerator[None, None]` from `collections.abc` is required for mypy strict mode — do not use `Generator` or leave untyped.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && uv run uvicorn app.main:app --port 8000 &amp; sleep 2 &amp;&amp; curl -s http://localhost:8000/api/v1/health &amp;&amp; kill %1</automated>
  </verify>
  <done>GET /api/v1/health returns {"status": "ok", "service": "forge-api"}. FastAPI app starts without import errors.</done>
</task>

<task type="auto">
  <name>Task 01-01-C: Create pytest skeleton suite with conftest and health test</name>
  <files>
    backend/app/tests/__init__.py
    backend/app/tests/conftest.py
    backend/app/tests/test_health.py
  </files>
  <action>
**backend/app/tests/__init__.py** — empty file

**backend/app/tests/conftest.py**:
```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import create_app


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Async test client for FastAPI app. Uses ASGITransport — no running server needed."""
    async with AsyncClient(
        transport=ASGITransport(app=create_app()),
        base_url="http://test",
    ) as ac:
        yield ac
```

Use `pytest_asyncio.fixture` (not `pytest.fixture`) for async fixtures. This is required in pytest-asyncio 1.x auto mode.

**backend/app/tests/test_health.py**:
```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "forge-api"
```

Then verify linting and type-checking pass:

```bash
cd backend
uv run ruff check app/
uv run black --check app/
uv run mypy app/
```

Fix any mypy or ruff violations before marking done. Common mypy issues:
- Missing return type annotations → add `-> None` or `-> dict[str, str]` as appropriate
- `list[str]` in Python 3.9 type hints is fine (no `List` import needed in 3.10+, and we target 3.12)
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && uv run pytest app/tests/ -v</automated>
  </verify>
  <done>pytest reports 1 passed, 0 failed. ruff, black --check, and mypy all exit 0 with zero violations.</done>
</task>


<!-- ═══════════════════════════════════════════════════════════════
     PLAN 01-03: Frontend Project Scaffold
     Wave 1 — runs parallel with Plan 01-01
     ═══════════════════════════════════════════════════════════════ -->

<task type="auto">
  <name>Task 01-03-A: Scaffold Next.js 16 app with TypeScript strict, Tailwind, ESLint</name>
  <files>
    frontend/package.json
    frontend/tsconfig.json
    frontend/next.config.ts
    frontend/src/app/layout.tsx
    frontend/src/app/page.tsx
    frontend/src/app/globals.css
    frontend/src/lib/utils.ts
    frontend/.eslintrc.json (or eslint.config.mjs for ESLint 9)
    frontend/.prettierrc
    frontend/prettier.config.mjs
  </files>
  <action>
From the repo root, create and scaffold the frontend:

```bash
mkdir -p frontend
cd frontend
npx create-next-app@latest . --typescript --app --tailwind --eslint --src-dir --no-git --import-alias "@/*"
```

This creates the Next.js 16 project. After it completes:

1. **Verify tsconfig.json has strict mode.** Open `frontend/tsconfig.json` and confirm `"strict": true` is present in `compilerOptions`. It should be there by default from create-next-app. If missing, add it.

2. **Configure next.config.ts** to disable compression (required to prevent SSE token buffering later):
```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  compress: false,  // Required: prevents Next.js from buffering SSE responses
};

export default nextConfig;
```

3. **Install shadcn/ui**:
```bash
cd frontend
npx shadcn@latest init --defaults
```
When prompted, accept all defaults (New York style, neutral color, CSS variables: yes). This creates `src/components/ui/` and `src/lib/utils.ts` with the `cn()` helper.

If shadcn init is not interactive (CI mode), use: `npx shadcn@latest init -d` (defaults flag).

After shadcn init, `src/lib/utils.ts` will contain:
```typescript
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

4. **Install Prettier with Tailwind plugin**:
```bash
npm install -D prettier prettier-plugin-tailwindcss
```

Create `frontend/.prettierrc`:
```json
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "es5",
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

5. **Add format script to package.json** (scripts section):
```json
"format": "prettier --write \"src/**/*.{ts,tsx,css}\"",
"format:check": "prettier --check \"src/**/*.{ts,tsx,css}\""
```

6. **Update src/app/page.tsx** to a minimal valid page (remove boilerplate Next.js content):
```tsx
export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center">
      <h1 className="text-2xl font-bold">Forge</h1>
    </main>
  );
}
```

Run ESLint and TypeScript check to verify zero violations:
```bash
cd frontend
npm run lint
npx tsc --noEmit
```

Fix any violations before proceeding.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npm run lint &amp;&amp; npx tsc --noEmit</automated>
  </verify>
  <done>create-next-app scaffolds successfully. shadcn/ui initializes with src/lib/utils.ts present. npm run lint and tsc --noEmit both exit 0 with zero violations. next.config.ts has compress: false.</done>
</task>

<task type="auto">
  <name>Task 01-03-B: Configure Vitest with jsdom, React plugin, path aliases, and skeleton test</name>
  <files>
    frontend/vitest.config.ts
    frontend/src/__tests__/setup.ts
    frontend/src/__tests__/placeholder.test.tsx
  </files>
  <action>
Install Vitest and testing dependencies:

```bash
cd frontend
npm install -D vitest @vitejs/plugin-react @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom vite-tsconfig-paths @playwright/test
```

Note: install `@testing-library/jest-dom` (provides `expect(...).toBeInTheDocument()` etc.), NOT `jest-dom` alone.

**frontend/vitest.config.ts**:
```typescript
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

**frontend/src/__tests__/setup.ts**:
```typescript
import "@testing-library/jest-dom";
```

**frontend/src/__tests__/placeholder.test.tsx**:
```tsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import Home from "../app/page";

describe("Home page", () => {
  it("renders the Forge heading", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: /forge/i })).toBeInTheDocument();
  });
});
```

Add the test script to `frontend/package.json` scripts:
```json
"test": "vitest run",
"test:watch": "vitest"
```

Also add vitest types to tsconfig.json so TypeScript recognizes `describe`, `it`, `expect` globals. In `frontend/tsconfig.json`, add to `compilerOptions`:
```json
"types": ["vitest/globals"]
```

Run the test to confirm it passes:
```bash
cd frontend && npm test
```
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npm test</automated>
  </verify>
  <done>Vitest reports 1 passed, 0 failed. vitest.config.ts exists with jsdom environment and react plugin. @testing-library/jest-dom is configured in setup.ts.</done>
</task>

</tasks>

---
---
phase: 01-infrastructure-foundation
plan: 02
type: execute
wave: 2
depends_on:
  - 01-01
files_modified:
  - backend/app/core/database.py
  - backend/app/main.py
  - backend/alembic.ini
  - backend/alembic/env.py
  - backend/alembic/script.py.mako
  - backend/alembic/versions/.gitkeep
  - backend/app/tests/test_database.py
autonomous: true
requirements:
  - TEST-04

must_haves:
  truths:
    - "Async SQLite engine starts with WAL mode and busy_timeout=5000ms — no lock errors"
    - "alembic upgrade head runs without error on a fresh database"
    - "alembic downgrade base runs cleanly (initial migration is reversible)"
    - "create_db_and_tables() creates the SQLModel schema on startup"
    - "Concurrent async requests do not produce sqlite3.OperationalError: database is locked"
  artifacts:
    - path: "backend/app/core/database.py"
      provides: "async engine with WAL pragma hook, session factory, get_session dependency"
      exports: ["engine", "AsyncSessionFactory", "get_session", "create_db_and_tables"]
    - path: "backend/alembic/env.py"
      provides: "Alembic env.py with SQLModel metadata and render_as_batch=True in BOTH offline and online paths"
      contains: "render_as_batch=True"
    - path: "backend/app/tests/test_database.py"
      provides: "Tests: WAL mode pragma, concurrent write test"
  key_links:
    - from: "backend/app/main.py"
      to: "backend/app/core/database.py"
      via: "lifespan calls create_db_and_tables()"
    - from: "backend/alembic/env.py"
      to: "backend/app/models/__init__.py"
      via: "import app.models — populates SQLModel.metadata"
---

<objective>
Plan 01-02: Database layer.

Creates the async SQLite engine with WAL mode and busy_timeout=5000ms, configures Alembic with batch mode for SQLite ALTER TABLE compatibility, and writes a skeleton migration plus database tests verifying correct PRAGMA settings.

Purpose: Prevent "database is locked" errors under concurrent async FastAPI requests (Pitfall 4). Establish batch mode before the first schema change (Pitfall 7).
Output: Working async database layer with Alembic initialized, first empty migration created, and pytest tests confirming WAL + busy_timeout are active.
</objective>

<execution_context>
Read Pattern 2 (SQLite WAL engine) and Pattern 3 (Alembic env.py) from RESEARCH.md before implementing. These patterns are exact — copy them rather than improvising.
</execution_context>

<context>
@.planning/phases/01-infrastructure-foundation/RESEARCH.md
@.planning/phases/01-infrastructure-foundation/01-infrastructure-foundation-01-SUMMARY.md
</context>

<tasks>

<task type="auto">
  <name>Task 01-02-A: Create async database engine with WAL pragma hook and session factory</name>
  <files>
    backend/app/core/database.py
    backend/app/main.py
  </files>
  <action>
**backend/app/core/database.py** — implement exactly as Pattern 2 from RESEARCH.md:

```python
from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,  # prevents sharing connections across coroutines with aiosqlite
)


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection: object, connection_record: object) -> None:
    """Enable WAL mode and set busy_timeout to avoid database locked errors."""
    cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA synchronous=NORMAL")  # safe with WAL; improves write speed
    cursor.close()


AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async database session per request."""
    async with AsyncSessionFactory() as session:
        yield session


async def create_db_and_tables() -> None:
    """Create all SQLModel tables. Called at app startup via lifespan."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
```

CRITICAL NOTE on the `@event.listens_for` decorator: it must target `engine.sync_engine`, not `engine` directly. The async engine wraps a sync engine internally; the "connect" event fires on the sync layer.

The `NullPool` prevents the common error "SQLite objects created in a thread can only be used in that same thread" when using aiosqlite with FastAPI's async request handling.

**Update backend/app/main.py** lifespan to call `create_db_and_tables()`:

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import create_db_and_tables
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await create_db_and_tables()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Type", "Cache-Control"],
    )

    application.include_router(api_router, prefix="/api/v1")

    return application


app = create_app()
```
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && uv run python -c "import asyncio; from app.core.database import create_db_and_tables; asyncio.run(create_db_and_tables()); print('DB init ok')"</automated>
  </verify>
  <done>create_db_and_tables() runs without error. forge.db is created. mypy passes on database.py with zero violations.</done>
</task>

<task type="auto">
  <name>Task 01-02-B: Initialize Alembic with SQLModel metadata and batch mode</name>
  <files>
    backend/alembic.ini
    backend/alembic/env.py
    backend/alembic/script.py.mako
    backend/alembic/versions/.gitkeep
  </files>
  <action>
From the backend directory, initialize Alembic:

```bash
cd backend
uv run alembic init alembic
```

This creates `alembic.ini` and `alembic/` directory. Now configure it:

**1. Update alembic.ini** — set the sqlalchemy.url:
```ini
sqlalchemy.url = sqlite+aiosqlite:///./forge.db
```

**2. Replace alembic/env.py completely** with the async + SQLModel + batch mode pattern from RESEARCH.md Pattern 3:

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from sqlmodel import SQLModel

# IMPORTANT: import all SQLModel table models here so their metadata is populated.
# This module must be updated whenever a new model file is added.
import app.models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (for generating SQL scripts)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # REQUIRED for SQLite ALTER TABLE support
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: object) -> None:
    context.configure(
        connection=connection,  # type: ignore[arg-type]
        target_metadata=target_metadata,
        render_as_batch=True,  # REQUIRED for SQLite ALTER TABLE support
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using the async SQLAlchemy engine."""
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

**3. Create the initial (empty) migration**:

```bash
cd backend
uv run alembic revision --autogenerate -m "initial_empty_schema"
```

This creates a file in `alembic/versions/` — verify it contains `render_as_batch` is honored (the env.py sets it globally, so the migration itself is clean).

**4. Run the migration**:
```bash
uv run alembic upgrade head
```

**5. Verify downgrade works**:
```bash
uv run alembic downgrade base
uv run alembic upgrade head
```

Both must complete without error.

**6. Create alembic/versions/.gitkeep** so the versions directory is tracked even before any migrations exist.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && uv run alembic downgrade base &amp;&amp; uv run alembic upgrade head &amp;&amp; echo "migrations ok"</automated>
  </verify>
  <done>alembic upgrade head and alembic downgrade base both complete without error. alembic/env.py contains render_as_batch=True in both offline and online paths. alembic/versions/ directory has the initial migration file.</done>
</task>

<task type="auto">
  <name>Task 01-02-C: Write database tests verifying WAL mode and concurrent access</name>
  <files>
    backend/app/tests/test_database.py
  </files>
  <action>
**backend/app/tests/test_database.py**:

```python
"""Tests verifying SQLite WAL mode, busy_timeout, and concurrent access safety."""
import asyncio

import pytest
from sqlalchemy import text

from app.core.database import AsyncSessionFactory, engine


@pytest.mark.asyncio
async def test_wal_mode_enabled() -> None:
    """PRAGMA journal_mode should return 'wal' after engine creation."""
    async with engine.connect() as conn:
        result = await conn.execute(text("PRAGMA journal_mode"))
        mode = result.scalar()
    assert mode == "wal", f"Expected WAL mode but got: {mode}"


@pytest.mark.asyncio
async def test_busy_timeout_set() -> None:
    """PRAGMA busy_timeout should be 5000ms (avoids database locked errors)."""
    async with engine.connect() as conn:
        result = await conn.execute(text("PRAGMA busy_timeout"))
        timeout = result.scalar()
    assert timeout == 5000, f"Expected busy_timeout=5000 but got: {timeout}"


@pytest.mark.asyncio
async def test_concurrent_sessions_no_lock_error() -> None:
    """Five concurrent read sessions must not raise OperationalError."""

    async def read_session() -> str:
        async with AsyncSessionFactory() as session:
            result = await session.execute(text("SELECT 1"))
            return str(result.scalar())

    results = await asyncio.gather(*[read_session() for _ in range(5)])
    assert all(r == "1" for r in results)
```

Run all tests to confirm they pass:
```bash
cd backend && uv run pytest app/tests/ -v
```

Run mypy to confirm zero violations:
```bash
cd backend && uv run mypy app/
```

Run ruff and black:
```bash
cd backend && uv run ruff check app/ && uv run black --check app/
```
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && uv run pytest app/tests/ -v --tb=short</automated>
  </verify>
  <done>All pytest tests pass (health test + 3 database tests). WAL mode and busy_timeout tests confirm correct PRAGMA values. mypy, ruff, and black all exit 0.</done>
</task>

</tasks>

---
---
phase: 01-infrastructure-foundation
plan: 03
type: execute
wave: 3
depends_on:
  - 01-01
  - 01-03
files_modified:
  - Makefile
  - .env.example
  - .env
  - .gitignore
  - .github/workflows/ci.yml
  - backend/app/tests/conftest.py
autonomous: true
requirements:
  - TEST-04

must_haves:
  truths:
    - "make dev starts both backend (port 8000) and frontend (port 3000) concurrently from repo root"
    - "make test runs both pytest and vitest and both pass"
    - "make lint runs ruff + black + ESLint and all pass with zero violations"
    - "make type-check runs mypy + tsc --noEmit and both pass"
    - "CI workflow file exists at .github/workflows/ci.yml with lint, type-check, test, and build jobs"
    - ".env.example documents all required environment variables"
    - ".gitignore excludes forge.db, .env, __pycache__, node_modules, .next"
  artifacts:
    - path: "Makefile"
      provides: "dev, test, lint, type-check, format, migrate targets"
      contains: "make -j 2"
    - path: ".env.example"
      provides: "Configuration contract with all env vars documented"
    - path: ".github/workflows/ci.yml"
      provides: "CI pipeline: lint, type-check, test, build"
    - path: ".gitignore"
      provides: "Ignores forge.db, .env, Python artifacts, Next.js build artifacts"
  key_links:
    - from: "Makefile"
      to: "backend/"
      via: "cd backend && uv run ..."
    - from: "Makefile"
      to: "frontend/"
      via: "cd frontend && npm run ..."
    - from: ".github/workflows/ci.yml"
      to: "Makefile"
      via: "runs make lint, make type-check, make test, make build"
---

<objective>
Plan 01-04: Dev tooling.

Wires together the completed backend (01-01, 01-02) and frontend (01-03) with a Makefile providing single-command access to dev/test/lint/type-check/migrate. Creates .env.example as the configuration contract, a .gitignore, and a GitHub Actions CI workflow that validates all quality gates.

Purpose: Fulfill TEST-04 — CI validates lint, type-check, unit/integration tests, and build. Deliver the success criterion: `make dev` starts both servers from a single command.
Output: Repo is operational for development. Any engineer (or agent) can clone, run `make dev`, and have a working local environment.
</objective>

<execution_context>
Read Pattern 7 (Makefile) from RESEARCH.md before implementing. Use `make -j 2` for concurrency — no npm concurrently dependency.
</execution_context>

<context>
@.planning/phases/01-infrastructure-foundation/RESEARCH.md
@.planning/phases/01-infrastructure-foundation/01-infrastructure-foundation-01-SUMMARY.md
@.planning/phases/01-infrastructure-foundation/01-infrastructure-foundation-02-SUMMARY.md
</context>

<tasks>

<task type="auto">
  <name>Task 01-04-A: Create Makefile, .env.example, and .gitignore</name>
  <files>
    Makefile
    .env.example
    .env
    .gitignore
  </files>
  <action>
**Makefile** at repo root (use hard tabs for indentation — Make requires tabs, NOT spaces):

```makefile
.PHONY: dev backend-dev frontend-dev \
        test backend-test frontend-test \
        lint backend-lint frontend-lint \
        type-check backend-type-check frontend-type-check \
        format migrate build

# ── Development ────────────────────────────────────────────────────────────────

dev:
	make -j 2 backend-dev frontend-dev

backend-dev:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

frontend-dev:
	cd frontend && npm run dev

# ── Testing ────────────────────────────────────────────────────────────────────

test:
	make -j 2 backend-test frontend-test

backend-test:
	cd backend && uv run pytest app/tests/ -v

frontend-test:
	cd frontend && npm test

# ── Linting ────────────────────────────────────────────────────────────────────

lint:
	$(MAKE) backend-lint
	$(MAKE) frontend-lint

backend-lint:
	cd backend && uv run ruff check app/ && uv run black --check app/

frontend-lint:
	cd frontend && npm run lint

# ── Type Checking ──────────────────────────────────────────────────────────────

type-check:
	$(MAKE) backend-type-check
	$(MAKE) frontend-type-check

backend-type-check:
	cd backend && uv run mypy app/

frontend-type-check:
	cd frontend && npx tsc --noEmit

# ── Formatting ─────────────────────────────────────────────────────────────────

format:
	cd backend && uv run ruff check --fix app/ && uv run black app/
	cd frontend && npm run format

# ── Database ───────────────────────────────────────────────────────────────────

migrate:
	cd backend && uv run alembic upgrade head

migrate-down:
	cd backend && uv run alembic downgrade -1

# ── Build ──────────────────────────────────────────────────────────────────────

build:
	cd frontend && npm run build
```

Note: `lint` and `type-check` use sequential `$(MAKE)` calls (not `-j 2`) because sequential failure reporting is clearer for debugging. `dev` and `test` use `-j 2` for speed.

**.env.example** at repo root:

```dotenv
# Forge — Environment Configuration
# Copy this file to .env and fill in your values.
# .env is gitignored; .env.example is committed as the configuration contract.

# ── Application ────────────────────────────────────────────────────────────────
APP_NAME=Forge
DEBUG=false

# ── Database ───────────────────────────────────────────────────────────────────
# SQLite database file path (relative to backend/ directory)
DATABASE_URL=sqlite+aiosqlite:///./forge.db

# ── CORS ───────────────────────────────────────────────────────────────────────
# Comma-separated list of allowed origins for CORS
# Must include the Next.js dev server origin for SSE streaming to work
CORS_ORIGINS=http://localhost:3000

# ── Authentication (Phase 2) ───────────────────────────────────────────────────
# SECRET_KEY=change-me-to-a-random-256-bit-key
# ACCESS_TOKEN_EXPIRE_MINUTES=15
# REFRESH_TOKEN_EXPIRE_DAYS=7

# ── LLM Provider (Phase 3) ────────────────────────────────────────────────────
# LLM_BASE_URL=http://localhost:11434/v1
# LLM_API_KEY=ollama
```

**.env** at repo root (gitignored, initial copy):
```dotenv
APP_NAME=Forge
DEBUG=false
DATABASE_URL=sqlite+aiosqlite:///./forge.db
CORS_ORIGINS=http://localhost:3000
```

**.gitignore** at repo root:

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/
.eggs/

# uv / virtual environments
.venv/
backend/.venv/

# Database files
*.db
*.db-wal
*.db-shm
forge.db

# Environment
.env
.env.local

# Next.js
frontend/.next/
frontend/out/
frontend/node_modules/

# Coverage
.coverage
htmlcov/
.pytest_cache/
backend/.mypy_cache/

# OS
.DS_Store
Thumbs.db

# Editor
.idea/
.vscode/
*.swp
*.swo
```
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone && make lint &amp;&amp; make type-check</automated>
  </verify>
  <done>Makefile is present with correct tab indentation. make lint exits 0. make type-check exits 0. .env.example documents all current variables. .gitignore excludes forge.db and .env.</done>
</task>

<task type="auto">
  <name>Task 01-04-B: Create GitHub Actions CI workflow</name>
  <files>
    .github/workflows/ci.yml
  </files>
  <action>
Create the CI directory and workflow file:

```bash
mkdir -p .github/workflows
```

**.github/workflows/ci.yml**:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-quality:
    name: Backend — Lint + Type Check
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "latest"

      - name: Set up Python 3.12
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Lint (ruff)
        run: uv run ruff check app/

      - name: Format check (black)
        run: uv run black --check app/

      - name: Type check (mypy)
        run: uv run mypy app/

  backend-test:
    name: Backend — Tests
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "latest"

      - name: Set up Python 3.12
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run migrations
        run: uv run alembic upgrade head

      - name: Run tests
        run: uv run pytest app/tests/ -v --tb=short

  frontend-quality:
    name: Frontend — Lint + Type Check
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Lint (ESLint)
        run: npm run lint

      - name: Type check (tsc)
        run: npx tsc --noEmit

      - name: Format check (prettier)
        run: npm run format:check

  frontend-test:
    name: Frontend — Tests
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Run Vitest
        run: npm test

  frontend-build:
    name: Frontend — Build
    runs-on: ubuntu-latest
    needs: [frontend-quality, frontend-test]
    defaults:
      run:
        working-directory: frontend

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Build Next.js
        run: npm run build
```

After creating the file, verify the YAML is valid by running:
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo "YAML valid"
```

Also do a final full verification of all quality gates from the repo root:
```bash
make lint
make type-check
make test
```

All three must exit 0.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone && python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('CI YAML valid')" &amp;&amp; make lint &amp;&amp; make type-check &amp;&amp; make test</automated>
  </verify>
  <done>.github/workflows/ci.yml is valid YAML with 5 jobs: backend-quality, backend-test, frontend-quality, frontend-test, frontend-build. make lint, make type-check, and make test all exit 0 from repo root.</done>
</task>

</tasks>

<verification>
Phase 1 is complete when ALL of the following pass from the repo root:

1. `make lint` — zero violations (ruff, black --check, eslint)
2. `make type-check` — zero violations (mypy --strict, tsc --noEmit)
3. `make test` — zero failures (pytest: health + WAL + concurrent tests; vitest: placeholder test)
4. `make migrate` — alembic upgrade head completes without error
5. `cd backend && uv run alembic downgrade base && uv run alembic upgrade head` — round-trip migration works
6. Manual: `make dev` starts both servers (Ctrl+C to stop)
   - curl http://localhost:8000/api/v1/health → {"status": "ok", "service": "forge-api"}
   - curl http://localhost:3000 → HTML with "Forge" heading
7. `.github/workflows/ci.yml` exists with lint, type-check, test, build jobs
8. `.env.example` exists and documents DATABASE_URL, CORS_ORIGINS, APP_NAME, DEBUG
</verification>

<success_criteria>
- `make dev` starts both frontend (3000) and backend (8000) from a single command
- SQLite initializes with WAL mode (PRAGMA journal_mode=WAL) and busy_timeout=5000ms — verified by automated test
- Alembic migrations run with batch mode (render_as_batch=True in env.py); alembic upgrade head completes without error
- Ruff, Black --check, ESLint, Prettier --check, mypy --strict, tsc --noEmit all pass with zero violations
- Vitest and pytest execute with zero failures on skeleton suites
- CI pipeline skeleton exists as .github/workflows/ci.yml
</success_criteria>

<output>
After completing all three sub-plans (01-01, 01-02, 01-03), create the phase summary at:
.planning/phases/01-infrastructure-foundation/01-infrastructure-foundation-SUMMARY.md

Include:
- What was built (directory structure created, key files)
- Key decisions confirmed (Python 3.12, uv, async SQLite with WAL, Alembic batch mode, Next.js 16 strict, Vitest)
- Patterns established (app factory, WAL pragma hook, Alembic env.py structure, Makefile targets)
- Quality gate results (all linters/tests passing)
- Any deviations from the plan and why
</output>
