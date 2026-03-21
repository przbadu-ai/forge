# Phase 2: Authentication - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Single-user authentication with JWT sessions. User can log in, stay logged in across refresh, log out, and all API routes are protected. No signup flow — single user is seeded on first startup.

</domain>

<decisions>
## Implementation Decisions

### Auth flow
- **D-01:** Single user seeded on first startup (username/password from env vars or defaults)
- **D-02:** JWT access tokens (short-lived, 15 min) + refresh tokens (long-lived, 7 days)
- **D-03:** Access token stored in memory (React state), refresh token in httpOnly cookie
- **D-04:** pwdlib[bcrypt] for password hashing (not passlib — deprecated)
- **D-05:** python-jose for JWT encoding/decoding

### Backend auth
- **D-06:** POST /api/v1/auth/login — returns access token, sets refresh cookie
- **D-07:** POST /api/v1/auth/refresh — refreshes access token using cookie
- **D-08:** POST /api/v1/auth/logout — clears refresh cookie
- **D-09:** GET /api/v1/auth/me — returns current user info
- **D-10:** FastAPI dependency `get_current_user` protects all routes

### Frontend auth
- **D-11:** Login page at /login with username + password form (shadcn/ui)
- **D-12:** Auth context provider wraps the app, manages token state
- **D-13:** Next.js middleware redirects unauthenticated users to /login
- **D-14:** Automatic token refresh before expiry using the refresh endpoint

### User seeding
- **D-15:** On first startup, if no user exists, create one from env vars (ADMIN_USERNAME, ADMIN_PASSWORD)
- **D-16:** Default credentials: admin / changeme (documented in .env.example)

### Claude's Discretion
- Exact JWT claims structure
- Token refresh timing strategy
- Login form styling details
- Error message wording

</decisions>

<specifics>
## Specific Ideas

- Keep auth simple — this is a single-user local app, not enterprise auth
- Login page should be clean and minimal — just username, password, submit
- No registration page needed — user is seeded from env

</specifics>

<canonical_refs>
## Canonical References

### Stack
- `.planning/research/STACK.md` — pwdlib, python-jose versions and usage patterns
- `.planning/research/PITFALLS.md` — passlib deprecation warning

### Phase 1 outputs
- `backend/app/core/config.py` — Pydantic Settings (add auth config here)
- `backend/app/core/database.py` — Async session factory (use for user queries)
- `backend/app/main.py` — App factory with lifespan (add user seeding here)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/core/config.py` — Settings class to extend with auth config
- `backend/app/core/database.py` — AsyncSessionFactory and get_session dependency
- `backend/app/api/v1/router.py` — Router to add auth endpoints
- `frontend/src/lib/utils.ts` — cn() helper for styling

### Established Patterns
- FastAPI app factory with lifespan (add user seeding in startup)
- Pydantic Settings from .env (add SECRET_KEY, token expiry)
- pytest with async client (test auth endpoints)

### Integration Points
- User model needs Alembic migration
- Auth middleware wraps all existing routes
- Frontend auth context wraps the app layout

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-authentication*
*Context gathered: 2026-03-21*
