.PHONY: setup backend-setup frontend-setup \
        dev kill-ports backend-dev frontend-dev \
        test backend-test frontend-test \
        lint backend-lint frontend-lint \
        type-check backend-type-check frontend-type-check \
        format migrate build e2e

# ── Setup ─────────────────────────────────────────────────
setup: check-node install-uv backend-setup frontend-setup setup-env migrate
	@echo ""
	@echo "✓ Setup complete. Run 'make dev' to start."

check-node:
	@command -v node >/dev/null 2>&1 || { \
		echo "Error: Node.js is not installed."; \
		echo ""; \
		echo "Install it from: https://nodejs.org/ (LTS recommended)"; \
		echo "  macOS:   brew install node"; \
		echo "  Ubuntu:  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt-get install -y nodejs"; \
		echo "  Or use nvm: https://github.com/nvm-sh/nvm"; \
		exit 1; \
	}

install-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo "uv not found. Installing..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}
	@echo "✓ uv is installed"

backend-setup:
	cd backend && uv sync --all-extras
	@echo "✓ Backend dependencies installed"

frontend-setup:
	cd frontend && npm ci
	@echo "✓ Frontend dependencies installed"

setup-env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env from .env.example"; \
		printf "Generate a random SECRET_KEY? [Y/n] "; \
		read -r answer; \
		if [ "$$answer" != "n" ] && [ "$$answer" != "N" ]; then \
			secret=$$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))"); \
			if [ "$$(uname)" = "Darwin" ]; then \
				sed -i '' "s|^SECRET_KEY=.*|SECRET_KEY=$$secret|" .env; \
			else \
				sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$$secret|" .env; \
			fi; \
			echo "✓ Generated SECRET_KEY"; \
		else \
			echo "⚠ Skipped — update SECRET_KEY in .env before production use"; \
		fi; \
	else \
		echo "✓ .env already exists"; \
	fi

# ── Development ────────────────────────────────────────────
dev: kill-ports
	make -j 2 backend-dev frontend-dev

kill-ports:
	@lsof -ti :8000 | xargs kill -9 2>/dev/null || true
	@lsof -ti :3000 | xargs kill -9 2>/dev/null || true
	@echo "✓ Ports 8000 and 3000 cleared"

backend-dev:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

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

# ── E2E Testing ───────────────────────────────────────────
e2e:
	cd frontend && npx playwright test --reporter=list

# ── Build ──────────────────────────────────────────────────
build:
	cd frontend && npm run build
