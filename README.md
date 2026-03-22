# Forge

A local-first, self-hosted AI assistant with streaming chat, tool use visibility, MCP integrations, and skills.

## What This Is

Forge connects to any OpenAI-compatible LLM endpoint (Ollama, LM Studio, vLLM, or remote APIs) and provides a full-featured chat interface with execution trace visibility. Every AI interaction — chat, tool call, MCP action, skill execution — is visible, persisted, and reviewable. Built for solo developers running local LLM infrastructure who want transparency and control over their AI workflows.

## Stack

| Layer    | Technologies                                                        |
|----------|---------------------------------------------------------------------|
| Frontend | Next.js (App Router), TypeScript, shadcn/ui, Tailwind CSS          |
| Backend  | Python 3.11+, FastAPI, SQLModel/SQLAlchemy, Alembic, SQLite, ChromaDB |

## Prerequisites

- **Node.js 22+** and npm
- **Python 3.12+**
- **uv** (installed automatically by `make setup` if missing)

## Setup

One command installs everything:

```bash
make setup
```

This will:
1. Check that Node.js is installed (fails with install instructions if missing)
2. Install `uv` if not already present
3. Install backend Python dependencies (`uv sync`)
4. Install frontend Node dependencies (`npm ci`)
5. Create `.env` from `.env.example` if it doesn't exist
6. Run database migrations (`alembic upgrade head`)

Then edit `.env` with your LLM endpoint and secret key.

## Network Access

Both servers bind to `0.0.0.0` by default, so you can access Forge from other devices on your network. Find your local IP and add it to `CORS_ORIGINS` in `.env`:

```bash
# .env
CORS_ORIGINS=["http://localhost:3000","http://192.168.1.100:3000"]
```

Then access `http://<your-ip>:3000` from any device on the same network.

## Running

```bash
# Both services in parallel
make dev

# Individually
make backend-dev    # FastAPI on :8000
make frontend-dev   # Next.js on :3000
```

## Testing

```bash
make test             # both backend and frontend
make backend-test     # pytest
make frontend-test    # vitest
```

## Other Commands

| Command                  | Description                                  |
|--------------------------|----------------------------------------------|
| `make lint`              | Run linters for both backend and frontend    |
| `make backend-lint`      | Ruff + Black check on backend                |
| `make frontend-lint`     | ESLint on frontend                           |
| `make type-check`        | Type-check both backend and frontend         |
| `make backend-type-check`| mypy on backend                              |
| `make frontend-type-check`| TypeScript `tsc --noEmit` on frontend       |
| `make format`            | Auto-format both backend and frontend        |
| `make migrate`           | Run Alembic migrations (upgrade head)        |
| `make migrate-down`      | Roll back one Alembic migration              |
| `make build`             | Production build of the frontend             |
| `make setup`             | Full project setup (deps, env, migrations)   |

## Docker

Run the full application without installing Python or Node.js locally.

### Quick Start

```bash
cp .env.example .env   # configure your LLM endpoint and secret key
docker compose up --build
```

The backend will be available at `http://localhost:8000` and the frontend at `http://localhost:3000`.

### Production

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

This adds restart policies (`unless-stopped`) and log rotation.

### Data Persistence

SQLite database and uploaded files are stored in Docker named volumes (`backend-data` and `backend-uploads`) and persist across container restarts.

### Environment

Copy `.env.example` to `.env` and configure before running. The `DATABASE_URL` is overridden inside the container to use the mounted volume path.
