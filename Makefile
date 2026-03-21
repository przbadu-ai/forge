.PHONY: dev backend-dev frontend-dev \
        test backend-test frontend-test \
        lint backend-lint frontend-lint \
        type-check backend-type-check frontend-type-check \
        format migrate build

# ── Development ────────────────────────────────────────────
dev:
	make -j 2 backend-dev frontend-dev

backend-dev:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

frontend-dev:
	cd frontend && npm run dev

# ── Testing ────────────────────────────────────────────────
test:
	make -j 2 backend-test frontend-test

backend-test:
	cd backend && uv run pytest app/tests/ -v

frontend-test:
	cd frontend && npm test

# ── Linting ────────────────────────────────────────────────
lint:
	$(MAKE) backend-lint
	$(MAKE) frontend-lint

backend-lint:
	cd backend && uv run ruff check app/ && uv run black --check app/

frontend-lint:
	cd frontend && npm run lint

# ── Type Checking ──────────────────────────────────────────
type-check:
	$(MAKE) backend-type-check
	$(MAKE) frontend-type-check

backend-type-check:
	cd backend && uv run mypy app/

frontend-type-check:
	cd frontend && npx tsc --noEmit

# ── Formatting ─────────────────────────────────────────────
format:
	cd backend && uv run ruff check --fix app/ && uv run black app/
	cd frontend && npm run format

# ── Database ───────────────────────────────────────────────
migrate:
	cd backend && uv run alembic upgrade head

migrate-down:
	cd backend && uv run alembic downgrade -1

# ── Build ──────────────────────────────────────────────────
build:
	cd frontend && npm run build
