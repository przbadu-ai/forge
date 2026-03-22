---
phase: quick
plan: 260322-hna
type: execute
wave: 1
depends_on: []
files_modified:
  - Dockerfile
  - docker-compose.yml
  - docker-compose.prod.yml
  - .dockerignore
  - backend/Dockerfile
  - frontend/Dockerfile
autonomous: true
requirements: []
must_haves:
  truths:
    - "User can run `docker compose up` and have the full app running"
    - "Backend serves API on port 8000 inside container"
    - "Frontend serves UI on port 3000 inside container"
    - "SQLite database persists across container restarts via volume"
    - "Uploaded files persist across container restarts via volume"
    - "Environment variables are configurable via .env file"
  artifacts:
    - path: "backend/Dockerfile"
      provides: "Backend container image build"
    - path: "frontend/Dockerfile"
      provides: "Frontend container image build with standalone output"
    - path: "docker-compose.yml"
      provides: "Development docker compose (with hot reload)"
    - path: "docker-compose.prod.yml"
      provides: "Production docker compose (optimized images)"
    - path: ".dockerignore"
      provides: "Excludes node_modules, .venv, .next, .git from build context"
  key_links:
    - from: "docker-compose.yml"
      to: ".env"
      via: "env_file directive"
    - from: "frontend container"
      to: "backend container"
      via: "NEXT_PUBLIC_API_URL=http://backend:8000 for SSR, browser uses localhost:8000"
---

<objective>
Add Docker setup for production deployment so users can quickly spin up the full application (FastAPI backend + Next.js frontend) with a single `docker compose` command.

Purpose: Enable one-command deployment without needing to install Python, Node.js, or uv locally.
Output: Dockerfiles for backend and frontend, docker-compose files for dev and production.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@Makefile
@.env.example
@backend/pyproject.toml
@frontend/package.json
@frontend/next.config.ts
@backend/app/core/config.py
@frontend/src/lib/api.ts
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create Dockerfiles for backend and frontend</name>
  <files>backend/Dockerfile, frontend/Dockerfile, .dockerignore</files>
  <action>
Create `.dockerignore` at project root:
```
.git
.planning
.claude
*.db
*.db-wal
*.db-shm
__pycache__
.venv
.mypy_cache
.pytest_cache
.ruff_cache
node_modules
.next
frontend/out
.env
.env.local
*.md
!README.md
```

Create `backend/Dockerfile`:
- Base: `python:3.12-slim`
- Install `curl` for healthcheck (apt-get, clean up after)
- Install uv: `COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/`
- WORKDIR `/app`
- Copy `pyproject.toml` and `uv.lock` first for layer caching
- Run `uv sync --frozen --no-dev` to install production deps only
- Copy `alembic.ini` and `alembic/` directory
- Copy `app/` source code
- Create `/app/uploads` directory and `/app/data` directory for SQLite
- EXPOSE 8000
- CMD: Run alembic upgrade head, then start uvicorn on 0.0.0.0:8000 with `uv run`
- Use a shell entrypoint script inline: `CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]`
- HEALTHCHECK: `curl -f http://localhost:8000/api/v1/health || exit 1` (interval 30s, timeout 10s, retries 3)
- Note: The DATABASE_URL env var will override config.py default. For Docker, use `sqlite+aiosqlite:///./data/forge.db` to persist in mounted volume.

Create `frontend/Dockerfile`:
- Stage 1 (deps): `node:22-alpine`, WORKDIR `/app`, copy `package.json` and `package-lock.json`, run `npm ci`
- Stage 2 (build): Copy source, set `NEXT_PUBLIC_API_URL` as ARG with empty default (browser will use window.location origin or localhost:8000 fallback from api.ts), run `npm run build`
- Stage 3 (runner): `node:22-alpine`, WORKDIR `/app`
  - Copy standalone output from build stage: `.next/standalone`, `.next/static`, `public` (if exists)
  - Note: next.config.ts needs `output: "standalone"` for this to work. Add it in Task 2.
  - EXPOSE 3000
  - ENV NODE_ENV=production
  - CMD `["node", "server.js"]`
- HEALTHCHECK: `wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1`
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone && test -f backend/Dockerfile && test -f frontend/Dockerfile && test -f .dockerignore && echo "All Docker files exist"</automated>
  </verify>
  <done>Backend Dockerfile uses python:3.12-slim with uv, frontend Dockerfile uses multi-stage Node 22 build with standalone output, .dockerignore excludes build artifacts</done>
</task>

<task type="auto">
  <name>Task 2: Create docker-compose files and update next.config.ts</name>
  <files>docker-compose.yml, docker-compose.prod.yml, frontend/next.config.ts</files>
  <action>
Update `frontend/next.config.ts` to add `output: "standalone"` (required for Docker multi-stage build). Keep `compress: false` as-is:
```ts
const nextConfig: NextConfig = {
  output: "standalone",
  compress: false,
};
```

Create `docker-compose.yml` (development with hot reload):
```yaml
services:
  backend:
    build:
      context: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/forge.db
    volumes:
      - backend-data:/app/data
      - backend-uploads:/app/uploads
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      backend:
        condition: service_healthy

volumes:
  backend-data:
  backend-uploads:
```

Create `docker-compose.prod.yml` (production override — can be used with `docker compose -f docker-compose.yml -f docker-compose.prod.yml up`):
```yaml
services:
  backend:
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

Verify the backend has a health endpoint. Check if `/api/v1/health` exists. If not, note in the action that the healthcheck URL may need adjusting — but do NOT create the endpoint (keep Docker setup focused). If no health endpoint exists, use a simpler healthcheck like `curl -f http://localhost:8000/docs || exit 1` or just remove the healthcheck and use a simple `test: ["CMD", "true"]` placeholder with a TODO comment.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone && test -f docker-compose.yml && test -f docker-compose.prod.yml && grep -q "standalone" frontend/next.config.ts && echo "Compose files and standalone config exist"</automated>
  </verify>
  <done>docker-compose.yml orchestrates backend + frontend with volume persistence, docker-compose.prod.yml adds restart policies and log rotation, next.config.ts has output: standalone</done>
</task>

<task type="auto">
  <name>Task 3: Verify Docker build succeeds</name>
  <files></files>
  <action>
Run `docker compose build` from the project root to verify both images build successfully. If Docker is not available on the system, verify the Dockerfiles are syntactically correct by:
1. Checking that all COPY sources exist (pyproject.toml, uv.lock, package.json, package-lock.json, etc.)
2. Checking that the next.config.ts standalone output is set
3. Running `cd frontend && npm run build` to verify the standalone output is generated at `.next/standalone/`

If the build fails, fix the issues. Common issues:
- Missing `uv.lock` file in backend (check it exists)
- Frontend standalone output requires specific next.config.ts setting
- alembic.ini path relative to WORKDIR

After verification, add a "Docker" section to the existing README.md with quick-start instructions:
```
## Docker

### Quick Start
docker compose up --build

### Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

### Environment
Copy .env.example to .env and configure before running.
```
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone && docker compose config --quiet 2>&1 && echo "Compose config valid" || echo "Docker not available or config invalid - manual check needed"</automated>
  </verify>
  <done>Docker images build successfully (or Dockerfiles verified syntactically correct if Docker unavailable), README.md updated with Docker quick-start section</done>
</task>

</tasks>

<verification>
- `docker compose config` validates compose file syntax
- `docker compose build` completes without errors
- `docker compose up` starts both services and they become healthy
- SQLite data persists in named volume across `docker compose down && docker compose up`
</verification>

<success_criteria>
- Users can clone the repo, copy .env.example to .env, and run `docker compose up --build` to get the full app running
- No local Python/Node.js installation required when using Docker
- Database and uploads persist across container restarts via Docker volumes
- Production compose adds restart policies and log rotation
</success_criteria>

<output>
After completion, create `.planning/quick/260322-hna-add-docker-setup-for-production-deployme/260322-hna-SUMMARY.md`
</output>
