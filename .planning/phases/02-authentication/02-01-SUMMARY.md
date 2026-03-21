---
phase: 02-authentication
plan: 01
subsystem: backend-auth
tags: [auth, jwt, user-model, security, fastapi]
dependency_graph:
  requires: [01-01, 01-02]
  provides: [user-model, jwt-auth, protected-routes, auth-endpoints]
  affects: [02-02, 03-01]
tech_stack:
  added: [pwdlib-bcrypt, python-jose-cryptography]
  patterns: [fastapi-dependency-injection, jwt-access-refresh, httponly-cookie]
key_files:
  created:
    - backend/app/models/user.py
    - backend/app/core/security.py
    - backend/app/api/v1/auth.py
    - backend/app/api/v1/deps.py
    - backend/alembic/versions/0002_add_user_table.py
    - backend/.env.example
    - backend/app/tests/test_security.py
    - backend/app/tests/test_auth.py
  modified:
    - backend/app/core/config.py
    - backend/app/api/v1/router.py
    - backend/app/main.py
    - backend/app/tests/conftest.py
    - backend/app/tests/test_health.py
    - backend/pyproject.toml
decisions:
  - "Used BcryptHasher explicitly instead of PasswordHash.recommended() -- recommended() requires argon2 which is not installed"
  - "Used SQLAlchemy AsyncSession.execute() instead of SQLModel session.exec() for async compatibility"
  - "Added lifespan_context to test conftest so DB tables and seed user are created before tests"
  - "Added B008 to ruff ignore list -- B008 is a false positive for FastAPI Depends() pattern"
  - "Used datetime.UTC instead of timezone.utc per UP017 rule"
metrics:
  duration: 6min
  completed: "2026-03-21T15:26:00Z"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 18
  tests_total: 22
---

# Phase 2 Plan 1: Backend Authentication Summary

JWT auth with access/refresh token rotation using python-jose, bcrypt password hashing via pwdlib, User model with Alembic migration, four auth endpoints, and FastAPI dependency-based route protection.

## What Was Built

### User Model (backend/app/models/user.py)
- SQLModel with id, username (unique, indexed), hashed_password, is_active, created_at
- Alembic migration 0002_add_user_table (chains from 46b781f3b083)

### Security Module (backend/app/core/security.py)
- hash_password / verify_password using pwdlib BcryptHasher
- create_access_token (15 min expiry) / create_refresh_token (7 day expiry) using python-jose
- decode_token with JWTError propagation for invalid/expired tokens

### Auth Endpoints (backend/app/api/v1/auth.py)
- POST /api/v1/auth/login -- validates credentials, returns access_token JSON, sets forge_refresh httpOnly cookie
- POST /api/v1/auth/refresh -- exchanges refresh cookie for new access token
- POST /api/v1/auth/logout -- clears forge_refresh cookie
- GET /api/v1/auth/me -- returns current user info (requires Bearer token)

### Route Protection (backend/app/api/v1/deps.py)
- get_current_user FastAPI dependency: extracts Bearer token, decodes JWT, validates type=access, fetches user from DB
- Applied to /health endpoint -- returns 401 without valid token

### User Seeding (backend/app/main.py)
- seed_admin_user() runs in app lifespan after create_db_and_tables()
- Creates admin user from ADMIN_USERNAME/ADMIN_PASSWORD env vars (defaults: admin/changeme)
- Only seeds if no users exist in DB

### Configuration (backend/app/core/config.py)
- Added: secret_key, algorithm, access_token_expire_minutes, refresh_token_expire_days, admin_username, admin_password
- All configurable via .env file

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] pwdlib PasswordHash.recommended() requires argon2**
- Found during: Task 1
- Issue: PasswordHash.recommended() raises HasherNotAvailable because argon2 is not installed
- Fix: Used PasswordHash((BcryptHasher(),)) to explicitly use bcrypt hasher
- Files modified: backend/app/core/security.py

**2. [Rule 1 - Bug] AsyncSession has no .exec() method**
- Found during: Task 2
- Issue: SQLModel's .exec() is sync-only; AsyncSession needs .execute() + .scalars()
- Fix: Changed session.exec() to session.execute() + .scalars().first() in auth.py and main.py
- Files modified: backend/app/api/v1/auth.py, backend/app/main.py

**3. [Rule 3 - Blocking] Test client lifespan not running**
- Found during: Task 2
- Issue: httpx ASGITransport does not run FastAPI lifespan by default; DB tables never created
- Fix: Added explicit lifespan_context(app) in conftest.py client fixture
- Files modified: backend/app/tests/conftest.py

**4. [Rule 1 - Bug] Ruff and mypy violations**
- Found during: Task 2 verification
- Issue: B008 false positive for FastAPI Depends, unused import, missing raise-from, timezone.utc deprecation, missing type annotations
- Fix: Added B008 to ruff ignore, fixed all violations
- Files modified: backend/pyproject.toml, backend/app/core/security.py, backend/app/api/v1/deps.py, backend/app/api/v1/auth.py

## Test Results

- test_security.py: 8 tests (hash, verify, JWT create/decode)
- test_auth.py: 10 tests (login success/failure, refresh, logout, me, health auth)
- test_health.py: 1 test (updated to use auth_client)
- test_database.py: 3 tests (existing, unchanged)
- Total: 22 passed, 0 failed

## Verification

- ruff check: All checks passed
- black --check: All files formatted
- mypy: No issues found in 19 source files
- alembic upgrade head: Migration chain intact (46b781f3b083 -> 0002_add_user_table)
- pytest: 22/22 tests pass
