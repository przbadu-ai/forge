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

- Node.js 18+
- npm
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # or
  pip install uv
  ```

## Setup

### Backend

```bash
cd backend
uv sync
cp .env.example .env   # edit with your LLM endpoint + secret key
uv run alembic upgrade head
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL=http://localhost:8000
```

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
