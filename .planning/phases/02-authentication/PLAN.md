---
phase: 02-authentication
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/models/user.py
  - backend/app/core/config.py
  - backend/app/core/security.py
  - backend/app/api/v1/auth.py
  - backend/app/api/v1/deps.py
  - backend/app/api/v1/router.py
  - backend/app/main.py
  - backend/alembic/versions/0002_add_user_table.py
  - backend/.env.example
autonomous: true
requirements:
  - AUTH-01
  - AUTH-04

must_haves:
  truths:
    - "POST /api/v1/auth/login returns 200 with access_token JSON and sets forge_refresh httpOnly cookie"
    - "POST /api/v1/auth/login returns 401 for invalid credentials"
    - "POST /api/v1/auth/refresh returns new access_token using refresh cookie"
    - "POST /api/v1/auth/logout clears the forge_refresh cookie"
    - "GET /api/v1/auth/me returns current user info when called with valid Bearer token"
    - "GET /api/v1/health returns 401 without a valid Bearer token after auth middleware is applied"
    - "User is seeded on first startup from ADMIN_USERNAME / ADMIN_PASSWORD env vars (defaults: admin / changeme)"
  artifacts:
    - path: "backend/app/models/user.py"
      provides: "User SQLModel with id, username, hashed_password, is_active, created_at"
      exports: ["User"]
    - path: "backend/app/core/security.py"
      provides: "password hashing (pwdlib[bcrypt]), JWT encode/decode (python-jose)"
      exports: ["hash_password", "verify_password", "create_access_token", "create_refresh_token", "decode_token"]
    - path: "backend/app/api/v1/auth.py"
      provides: "Login, refresh, logout, me endpoints"
      exports: ["router"]
    - path: "backend/app/api/v1/deps.py"
      provides: "get_current_user FastAPI dependency"
      exports: ["get_current_user"]
    - path: "backend/alembic/versions/0002_add_user_table.py"
      provides: "Migration creating user table"
      contains: "op.create_table('user'"
  key_links:
    - from: "backend/app/api/v1/auth.py"
      to: "backend/app/core/security.py"
      via: "verify_password and create_access_token calls"
      pattern: "verify_password|create_access_token"
    - from: "backend/app/api/v1/deps.py"
      to: "backend/app/core/security.py"
      via: "decode_token to extract user_id from Bearer"
      pattern: "decode_token"
    - from: "backend/app/main.py"
      to: "backend/app/models/user.py"
      via: "lifespan seed_admin_user call"
      pattern: "seed_admin_user"
---

<objective>
Implement the complete backend authentication system: User model, Alembic migration, password hashing, JWT token generation/validation, auth endpoints, and FastAPI dependency for route protection.

Purpose: Provides the secured API foundation that all future phases depend on. Without this, every route is unauthenticated and the application is unusable.
Output: Working /auth endpoints, protected routes returning 401, single admin user seeded on startup.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/02-authentication/2-CONTEXT.md

Key constraints from context:
- pwdlib[bcrypt] for hashing (NOT passlib — deprecated/broken on Python 3.12+)
- python-jose[cryptography] for JWT (NOT PyJWT)
- Access tokens: 15 min expiry; refresh tokens: 7 days expiry
- Refresh token goes in httpOnly cookie named "forge_refresh"
- Access token returned in response JSON only (not in cookie)
- Single user seeded from ADMIN_USERNAME / ADMIN_PASSWORD env vars
- Default credentials: admin / changeme (documented in .env.example)
</context>

<interfaces>
<!-- Existing code the executor needs. No exploration required. -->

From backend/app/core/config.py:
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

From backend/app/core/database.py:
```python
AsyncSessionFactory: async_sessionmaker[AsyncSession]

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session
```

From backend/app/main.py:
```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await create_db_and_tables()
    yield

def create_app() -> FastAPI: ...
app = create_app()
```

From backend/app/api/v1/router.py:
```python
from fastapi import APIRouter
api_router = APIRouter()

@api_router.get("/health")
async def health_check() -> dict[str, str]: ...
```

Existing migration: backend/alembic/versions/46b781f3b083_initial_empty_schema.py
  - revision: '46b781f3b083'
  - down_revision: None (base migration)
</interfaces>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: User model, security module, and Alembic migration</name>
  <files>
    backend/app/models/__init__.py
    backend/app/models/user.py
    backend/app/core/config.py
    backend/app/core/security.py
    backend/alembic/versions/0002_add_user_table.py
    backend/.env.example
  </files>
  <behavior>
    - hash_password("secret") returns a bcrypt hash string (starts with "$2b$")
    - verify_password("secret", hash) returns True for matching, False for mismatch
    - create_access_token({"sub": "1"}) returns a JWT string, decode reveals sub="1" and exp within 15 min
    - create_refresh_token({"sub": "1"}) returns a JWT string, decode reveals sub="1" and exp within 7 days
    - decode_token(valid_jwt) returns the payload dict
    - decode_token(expired_jwt) raises JWTError
    - decode_token(tampered_jwt) raises JWTError
  </behavior>
  <action>
1. Install missing dependencies in backend/pyproject.toml:
   ```
   uv add "python-jose[cryptography]" "pwdlib[bcrypt]"
   ```
   Verify they appear in pyproject.toml dependencies section.

2. Create backend/app/models/__init__.py (empty, marks as package).

3. Create backend/app/models/user.py:
   ```python
   from datetime import datetime
   from sqlmodel import Field, SQLModel

   class User(SQLModel, table=True):
       id: int | None = Field(default=None, primary_key=True)
       username: str = Field(unique=True, index=True, max_length=50)
       hashed_password: str
       is_active: bool = Field(default=True)
       created_at: datetime = Field(default_factory=datetime.utcnow)
   ```

4. Extend backend/app/core/config.py — add auth fields to Settings:
   ```python
   secret_key: str = "change-me-in-production-32-chars-min"
   algorithm: str = "HS256"
   access_token_expire_minutes: int = 15
   refresh_token_expire_days: int = 7
   admin_username: str = "admin"
   admin_password: str = "changeme"
   ```
   Keep existing fields. Add to model_config if needed for .env loading.

5. Create backend/app/core/security.py:
   ```python
   from datetime import datetime, timedelta, timezone
   from jose import JWTError, jwt
   from pwdlib import PasswordHash
   from app.core.config import settings

   password_hash = PasswordHash.recommended()

   def hash_password(password: str) -> str:
       return password_hash.hash(password)

   def verify_password(plain: str, hashed: str) -> bool:
       return password_hash.check(plain, hashed)

   def create_access_token(data: dict) -> str:
       payload = data.copy()
       expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
       payload.update({"exp": expire, "type": "access"})
       return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

   def create_refresh_token(data: dict) -> str:
       payload = data.copy()
       expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
       payload.update({"exp": expire, "type": "refresh"})
       return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

   def decode_token(token: str) -> dict:
       # Raises JWTError if invalid or expired
       return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
   ```

6. Create Alembic migration backend/alembic/versions/0002_add_user_table.py:
   ```python
   """add_user_table

   Revision ID: 0002_add_user_table
   Revises: 46b781f3b083
   Create Date: 2026-03-21

   """
   from typing import Sequence, Union
   from alembic import op
   import sqlalchemy as sa

   revision: str = '0002_add_user_table'
   down_revision: Union[str, Sequence[str], None] = '46b781f3b083'
   branch_labels = None
   depends_on = None

   def upgrade() -> None:
       with op.batch_alter_table('user', schema=None) as batch_op:
           pass
       op.create_table(
           'user',
           sa.Column('id', sa.Integer(), nullable=False),
           sa.Column('username', sa.String(length=50), nullable=False),
           sa.Column('hashed_password', sa.String(), nullable=False),
           sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
           sa.Column('created_at', sa.DateTime(), nullable=False),
           sa.PrimaryKeyConstraint('id'),
       )
       op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)

   def downgrade() -> None:
       op.drop_index(op.f('ix_user_username'), table_name='user')
       op.drop_table('user')
   ```

7. Create backend/.env.example:
   ```
   # Application
   DEBUG=false
   CORS_ORIGINS=["http://localhost:3000"]

   # Database
   DATABASE_URL=sqlite+aiosqlite:///./forge.db

   # Authentication — CHANGE THESE IN PRODUCTION
   SECRET_KEY=change-me-in-production-use-openssl-rand-hex-32
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=15
   REFRESH_TOKEN_EXPIRE_DAYS=7

   # Admin user seeded on first startup
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=changeme
   ```

8. Write tests in backend/app/tests/test_security.py (TDD — write tests first, then verify security.py passes them):
   - test_hash_password_produces_bcrypt_hash
   - test_verify_password_correct
   - test_verify_password_wrong
   - test_create_access_token_has_correct_claims
   - test_create_refresh_token_has_correct_claims
   - test_decode_token_valid
   - test_decode_token_invalid_raises
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/test_security.py -v</automated>
  </verify>
  <done>
    All security tests pass. Migration file exists with correct down_revision='46b781f3b083'. User model is importable. Security functions handle bcrypt and JWT correctly.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Auth endpoints, FastAPI dependency, user seeding, and router wiring</name>
  <files>
    backend/app/api/v1/auth.py
    backend/app/api/v1/deps.py
    backend/app/api/v1/router.py
    backend/app/main.py
    backend/app/tests/test_auth.py
  </files>
  <behavior>
    - POST /api/v1/auth/login with {"username":"admin","password":"changeme"} returns 200 with {"access_token": "...", "token_type": "bearer"} and Set-Cookie: forge_refresh=...; HttpOnly; Path=/api/v1/auth/refresh
    - POST /api/v1/auth/login with wrong credentials returns 401 {"detail": "Incorrect username or password"}
    - POST /api/v1/auth/refresh with valid refresh cookie returns 200 with new access_token
    - POST /api/v1/auth/refresh with missing/invalid cookie returns 401
    - POST /api/v1/auth/logout returns 200 and clears forge_refresh cookie (Set-Cookie with max-age=0)
    - GET /api/v1/auth/me with valid Bearer token returns {"id": 1, "username": "admin", "is_active": true}
    - GET /api/v1/auth/me without Bearer token returns 401
    - GET /api/v1/health without Bearer token returns 401 (route is now protected)
    - Admin user exists in DB after app startup (seed ran in lifespan)
  </behavior>
  <action>
1. Create backend/app/api/v1/deps.py:
   ```python
   from fastapi import Depends, HTTPException, status
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   from jose import JWTError
   from sqlmodel.ext.asyncio.session import AsyncSession
   from app.core.database import get_session
   from app.core.security import decode_token
   from app.models.user import User
   from sqlmodel import select

   bearer_scheme = HTTPBearer()

   async def get_current_user(
       credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
       session: AsyncSession = Depends(get_session),
   ) -> User:
       credentials_exception = HTTPException(
           status_code=status.HTTP_401_UNAUTHORIZED,
           detail="Could not validate credentials",
           headers={"WWW-Authenticate": "Bearer"},
       )
       try:
           payload = decode_token(credentials.credentials)
           user_id: int | None = payload.get("sub")
           if user_id is None:
               raise credentials_exception
           if payload.get("type") != "access":
               raise credentials_exception
       except JWTError:
           raise credentials_exception
       user = await session.get(User, int(user_id))
       if user is None or not user.is_active:
           raise credentials_exception
       return user
   ```

2. Create backend/app/api/v1/auth.py with four endpoints:

   POST /auth/login:
   - Accepts form body: LoginRequest(username: str, password: str)
   - Queries User by username, verifies password
   - Returns TokenResponse(access_token, token_type="bearer")
   - Sets httpOnly cookie "forge_refresh" with refresh token, path="/api/v1/auth/refresh", samesite="lax", secure=False (localhost)
   - Returns 401 on failure (use same message to prevent username enumeration)

   POST /auth/refresh:
   - Reads "forge_refresh" cookie from request
   - Decodes it, verifies type=="refresh"
   - Fetches user from DB, verifies is_active
   - Returns new TokenResponse with fresh access token
   - Returns 401 if cookie missing or invalid

   POST /auth/logout:
   - Clears forge_refresh cookie (set max_age=0, same path)
   - Returns {"message": "Logged out"}

   GET /auth/me:
   - Depends(get_current_user)
   - Returns UserResponse(id, username, is_active, created_at)

   Pydantic schemas (define in same file or separate schemas/auth.py):
   ```python
   class LoginRequest(BaseModel):
       username: str
       password: str

   class TokenResponse(BaseModel):
       access_token: str
       token_type: str = "bearer"

   class UserResponse(BaseModel):
       id: int
       username: str
       is_active: bool
       created_at: datetime
   ```

3. Update backend/app/api/v1/router.py to:
   - Import and include auth router: `api_router.include_router(auth_router, prefix="/auth", tags=["auth"])`
   - Add `Depends(get_current_user)` to the health endpoint (all non-auth routes must be protected)

4. Update backend/app/main.py lifespan to seed admin user:
   ```python
   from app.core.database import create_db_and_tables, AsyncSessionFactory
   from app.core.security import hash_password, verify_password
   from app.core.config import settings
   from app.models.user import User
   from sqlmodel import select

   @asynccontextmanager
   async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
       await create_db_and_tables()
       await seed_admin_user()
       yield

   async def seed_admin_user() -> None:
       async with AsyncSessionFactory() as session:
           result = await session.exec(select(User))
           existing = result.first()
           if existing is None:
               user = User(
                   username=settings.admin_username,
                   hashed_password=hash_password(settings.admin_password),
               )
               session.add(user)
               await session.commit()
   ```

5. Write tests in backend/app/tests/test_auth.py using AsyncClient:
   - test_login_success: POST /api/v1/auth/login with admin/changeme → 200 + access_token + forge_refresh cookie set
   - test_login_wrong_password: → 401
   - test_login_unknown_user: → 401
   - test_refresh_success: login first, use cookie in POST /api/v1/auth/refresh → 200 + new access_token
   - test_refresh_no_cookie: → 401
   - test_logout: login, then POST /api/v1/auth/logout → 200, cookie cleared
   - test_me_authenticated: login, use token in GET /api/v1/auth/me → 200 + username=admin
   - test_me_unauthenticated: no token → 401
   - test_health_requires_auth: GET /api/v1/health without token → 401
   - test_health_authenticated: with valid token → 200

   Update conftest.py to add fixtures:
   ```python
   @pytest_asyncio.fixture
   async def auth_client(client: AsyncClient) -> AsyncClient:
       """Client with admin credentials pre-logged-in; Authorization header set."""
       resp = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "changeme"})
       token = resp.json()["access_token"]
       client.headers["Authorization"] = f"Bearer {token}"
       return client
   ```
   Note: The test client fixture creates a fresh app per test — the lifespan (including seeding) runs for each test client. This ensures the admin user exists for auth tests.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/test_auth.py -v</automated>
  </verify>
  <done>
    All auth endpoint tests pass. Login returns token + cookie. Refresh returns new token. Logout clears cookie. /me returns user info. /health returns 401 without auth. Admin user seeded in lifespan.
  </done>
</task>

</tasks>

<verification>
Run the full backend test suite to confirm no regressions:

```bash
cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/ -v
```

Verify Alembic migration chain is intact:
```bash
cd /Users/przbadu/dev/claude-clone/backend && alembic upgrade head
```

Verify mypy passes:
```bash
cd /Users/przbadu/dev/claude-clone/backend && mypy app/
```

Spot-check the running API (optional, requires server up):
```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"changeme"}' | python3 -m json.tool
```
</verification>

<success_criteria>
- pytest passes all tests in app/tests/ including test_security.py and test_auth.py
- alembic upgrade head completes without error (user table created)
- All 5 auth endpoints respond correctly (login, refresh, logout, me, 401 on protected routes)
- Admin user exists in DB after app startup
- mypy reports no errors on the auth modules
</success_criteria>

<output>
After completion, create `.planning/phases/02-authentication/02-01-SUMMARY.md` with:
- What was built (endpoints, models, migration)
- Key implementation decisions (cookie name, token format, seed logic)
- Actual files created/modified
- Any deviations from plan and why
</output>

---
phase: 02-authentication
plan: 02
type: execute
wave: 2
depends_on:
  - 02-01
files_modified:
  - frontend/src/app/login/page.tsx
  - frontend/src/app/(protected)/layout.tsx
  - frontend/src/lib/auth.ts
  - frontend/src/lib/api.ts
  - frontend/src/context/auth-context.tsx
  - frontend/src/proxy.ts
  - frontend/src/app/layout.tsx
  - frontend/src/app/page.tsx
autonomous: true
requirements:
  - AUTH-01
  - AUTH-02
  - AUTH-03

must_haves:
  truths:
    - "Visiting /login shows a clean form with username and password fields and a submit button"
    - "Submitting valid credentials redirects to / (home) and stores the access token in memory"
    - "Submitting invalid credentials shows an inline error message without page reload"
    - "Access token is refreshed automatically before expiry using the httpOnly refresh cookie"
    - "Visiting any non-/login route while unauthenticated redirects to /login"
    - "A logout button clears the in-memory token, calls /auth/logout, and redirects to /login"
    - "After browser refresh, the auth context automatically attempts token refresh to restore session"
  artifacts:
    - path: "frontend/src/context/auth-context.tsx"
      provides: "AuthContext with user, token, login, logout, refreshToken state"
      exports: ["AuthProvider", "useAuth"]
    - path: "frontend/src/lib/auth.ts"
      provides: "API functions for login, refresh, logout, me calls"
      exports: ["loginApi", "refreshApi", "logoutApi", "meApi"]
    - path: "frontend/src/lib/api.ts"
      provides: "Base fetch wrapper that injects Authorization header from auth context"
      exports: ["apiFetch"]
    - path: "frontend/src/proxy.ts"
      provides: "Route protection — redirects unauthenticated users to /login"
      contains: "export default async function proxy"
    - path: "frontend/src/app/login/page.tsx"
      provides: "Login form using base-ui Button + native inputs styled with Tailwind"
  key_links:
    - from: "frontend/src/proxy.ts"
      to: "backend /api/v1/auth/refresh"
      via: "reads forge_refresh cookie, calls refresh endpoint to validate session"
      pattern: "forge_refresh"
    - from: "frontend/src/context/auth-context.tsx"
      to: "frontend/src/lib/auth.ts"
      via: "loginApi, refreshApi, logoutApi calls"
      pattern: "loginApi|refreshApi|logoutApi"
    - from: "frontend/src/app/(protected)/layout.tsx"
      to: "frontend/src/context/auth-context.tsx"
      via: "useAuth hook to check authentication state"
      pattern: "useAuth"
---

<objective>
Implement frontend authentication: login page, auth context managing token state, automatic refresh, route protection via proxy.ts, and logout.

Purpose: Completes the user-facing auth flow. After this plan, users can log in, stay logged in across refresh, and are automatically redirected to /login when unauthenticated.
Output: Working login page, auth context provider, proxy.ts route guard, logout action.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/02-authentication/2-CONTEXT.md
@.planning/phases/02-authentication/02-01-SUMMARY.md

Key constraints from context:
- Next.js 16 uses proxy.ts (NOT middleware.ts — that file convention is DEPRECATED in Next.js 16)
- The file is src/proxy.ts (same level as src/app)
- Default exported function must be named `proxy` (not `middleware`)
- Access token stored in React state (memory) only — never in localStorage
- Refresh token is httpOnly cookie set by backend — frontend never touches it directly
- Automatic refresh: attempt token refresh on page load and before each API call if token near expiry
- Auth context wraps the entire app via layout.tsx
- UI uses @base-ui/react Button (already installed) + native HTML inputs styled with Tailwind
- Do NOT install next-auth — custom JWT flow via FastAPI backend
- Login page at /login (public route), all other routes protected
</context>

<interfaces>
<!-- Key interfaces from Plan 01 output and existing frontend code. -->

Backend API contracts (from Plan 01):
```
POST /api/v1/auth/login
  Body: { username: string, password: string }
  Response 200: { access_token: string, token_type: "bearer" }
  Side-effect: Sets forge_refresh httpOnly cookie
  Error 401: { detail: "Incorrect username or password" }

POST /api/v1/auth/refresh
  Cookies: forge_refresh (httpOnly, set automatically by browser)
  Response 200: { access_token: string, token_type: "bearer" }
  Error 401: { detail: "..." }

POST /api/v1/auth/logout
  Response 200: { message: "Logged out" }
  Side-effect: Clears forge_refresh cookie

GET /api/v1/auth/me
  Headers: Authorization: Bearer {access_token}
  Response 200: { id: number, username: string, is_active: boolean, created_at: string }
  Error 401: { detail: "..." }
```

Existing frontend code:
```typescript
// frontend/src/lib/utils.ts
export function cn(...inputs: ClassValue[]): string  // clsx + tailwind-merge

// frontend/src/components/ui/button.tsx
// Uses @base-ui/react/button with CVA variants
// Import: import { Button } from "@/components/ui/button"
// Props: variant ("default"|"outline"|"secondary"|"ghost"|"destructive"|"link"), size

// frontend/src/app/layout.tsx — wraps everything, needs AuthProvider added
```

Proxy convention (Next.js 16 — read from node_modules/next/dist/docs):
```typescript
// src/proxy.ts (NOT src/middleware.ts)
import { NextRequest, NextResponse } from 'next/server'

export default async function proxy(req: NextRequest) {
  // ... redirect logic
  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|.*\\.png$).*)'],
}
```
</interfaces>

<tasks>

<task type="auto">
  <name>Task 1: Auth API lib, auth context, and proxy route guard</name>
  <files>
    frontend/src/lib/auth.ts
    frontend/src/lib/api.ts
    frontend/src/context/auth-context.tsx
    frontend/src/proxy.ts
    frontend/src/app/layout.tsx
  </files>
  <action>
1. Create frontend/src/lib/auth.ts — raw fetch calls to backend auth endpoints:
   ```typescript
   const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

   export interface TokenResponse {
     access_token: string
     token_type: string
   }

   export interface UserResponse {
     id: number
     username: string
     is_active: boolean
     created_at: string
   }

   export async function loginApi(username: string, password: string): Promise<TokenResponse> {
     const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
       method: "POST",
       headers: { "Content-Type": "application/json" },
       credentials: "include",  // needed for refresh cookie
       body: JSON.stringify({ username, password }),
     })
     if (!res.ok) {
       const err = await res.json().catch(() => ({}))
       throw new Error(err.detail ?? "Login failed")
     }
     return res.json()
   }

   export async function refreshApi(): Promise<TokenResponse> {
     const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
       method: "POST",
       credentials: "include",  // sends forge_refresh cookie
     })
     if (!res.ok) throw new Error("Refresh failed")
     return res.json()
   }

   export async function logoutApi(): Promise<void> {
     await fetch(`${API_BASE}/api/v1/auth/logout`, {
       method: "POST",
       credentials: "include",
     })
   }

   export async function meApi(token: string): Promise<UserResponse> {
     const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
       headers: { Authorization: `Bearer ${token}` },
     })
     if (!res.ok) throw new Error("Unauthorized")
     return res.json()
   }
   ```

2. Create frontend/src/lib/api.ts — base fetch wrapper that injects auth token:
   ```typescript
   // apiFetch wraps fetch with Authorization header injection.
   // Token is passed in explicitly (consumers get it from useAuth).
   const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

   export async function apiFetch(
     path: string,
     token: string,
     options: RequestInit = {}
   ): Promise<Response> {
     return fetch(`${API_BASE}${path}`, {
       ...options,
       credentials: "include",
       headers: {
         "Content-Type": "application/json",
         Authorization: `Bearer ${token}`,
         ...(options.headers ?? {}),
       },
     })
   }
   ```

3. Create frontend/src/context/auth-context.tsx:
   ```typescript
   "use client"

   import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react"
   import { loginApi, logoutApi, refreshApi } from "@/lib/auth"
   import type { UserResponse } from "@/lib/auth"

   interface AuthState {
     token: string | null
     user: UserResponse | null
     isLoading: boolean
   }

   interface AuthContextValue extends AuthState {
     login: (username: string, password: string) => Promise<void>
     logout: () => Promise<void>
   }

   const AuthContext = createContext<AuthContextValue | null>(null)

   export function AuthProvider({ children }: { children: React.ReactNode }) {
     const [state, setState] = useState<AuthState>({ token: null, user: null, isLoading: true })
     const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

     // Schedule next refresh 1 minute before expiry (14 min for 15 min tokens)
     const scheduleRefresh = useCallback((delayMs: number = 14 * 60 * 1000) => {
       if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
       refreshTimerRef.current = setTimeout(async () => {
         try {
           const data = await refreshApi()
           setState(prev => ({ ...prev, token: data.access_token }))
           scheduleRefresh()
         } catch {
           setState({ token: null, user: null, isLoading: false })
         }
       }, delayMs)
     }, [])

     // On mount: attempt refresh to restore session
     useEffect(() => {
       refreshApi()
         .then(async (data) => {
           // Fetch user info with new token
           const { meApi } = await import("@/lib/auth")
           const user = await meApi(data.access_token)
           setState({ token: data.access_token, user, isLoading: false })
           scheduleRefresh()
         })
         .catch(() => {
           setState({ token: null, user: null, isLoading: false })
         })
       return () => {
         if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
       }
     }, [scheduleRefresh])

     const login = useCallback(async (username: string, password: string) => {
       const data = await loginApi(username, password)
       const { meApi } = await import("@/lib/auth")
       const user = await meApi(data.access_token)
       setState({ token: data.access_token, user, isLoading: false })
       scheduleRefresh()
     }, [scheduleRefresh])

     const logout = useCallback(async () => {
       if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
       await logoutApi()
       setState({ token: null, user: null, isLoading: false })
     }, [])

     return (
       <AuthContext.Provider value={{ ...state, login, logout }}>
         {children}
       </AuthContext.Provider>
     )
   }

   export function useAuth(): AuthContextValue {
     const ctx = useContext(AuthContext)
     if (!ctx) throw new Error("useAuth must be used inside AuthProvider")
     return ctx
   }
   ```

4. Create frontend/src/proxy.ts (IMPORTANT: NOT middleware.ts — that is deprecated in Next.js 16):
   ```typescript
   import { NextRequest, NextResponse } from "next/server"

   const PUBLIC_PATHS = ["/login"]

   export default async function proxy(req: NextRequest): Promise<NextResponse> {
     const { pathname } = req.nextUrl

     // Allow public paths through
     if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
       return NextResponse.next()
     }

     // Check for refresh cookie — if present, user may have a valid session
     // Proxy cannot call FastAPI here (would add latency on every route).
     // We do an optimistic check: if forge_refresh cookie exists, let through.
     // The AuthContext in the browser will call /auth/refresh on mount to verify.
     // If that fails, the (protected) layout redirects to /login client-side.
     const refreshCookie = req.cookies.get("forge_refresh")
     if (!refreshCookie) {
       const loginUrl = new URL("/login", req.nextUrl)
       loginUrl.searchParams.set("from", pathname)
       return NextResponse.redirect(loginUrl)
     }

     return NextResponse.next()
   }

   export const config = {
     matcher: ["/((?!api|_next/static|_next/image|favicon.ico|.*\\.png$).*)"],
   }
   ```

5. Update frontend/src/app/layout.tsx to wrap children with AuthProvider:
   - Import AuthProvider from "@/context/auth-context"
   - Wrap {children} with <AuthProvider>{children}</AuthProvider> inside the body
   - Keep existing font configuration and metadata
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit 2>&1 | head -30</automated>
  </verify>
  <done>
    TypeScript compiles without errors. src/proxy.ts exists (not middleware.ts). AuthProvider wraps layout. auth.ts and api.ts export the documented functions.
  </done>
</task>

<task type="auto">
  <name>Task 2: Login page, protected layout, and logout integration</name>
  <files>
    frontend/src/app/login/page.tsx
    frontend/src/app/(protected)/layout.tsx
    frontend/src/app/(protected)/page.tsx
    frontend/src/app/page.tsx
  </files>
  <action>
1. Create frontend/src/app/login/page.tsx — login form:
   ```typescript
   "use client"

   import { useState, useTransition } from "react"
   import { useRouter, useSearchParams } from "next/navigation"
   import { useAuth } from "@/context/auth-context"
   import { Button } from "@/components/ui/button"

   export default function LoginPage() {
     const { login } = useAuth()
     const router = useRouter()
     const searchParams = useSearchParams()
     const [error, setError] = useState<string | null>(null)
     const [isPending, startTransition] = useTransition()

     function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
       e.preventDefault()
       const form = e.currentTarget
       const username = (form.elements.namedItem("username") as HTMLInputElement).value
       const password = (form.elements.namedItem("password") as HTMLInputElement).value

       startTransition(async () => {
         try {
           setError(null)
           await login(username, password)
           const from = searchParams.get("from") ?? "/"
           router.push(from)
         } catch (err) {
           setError(err instanceof Error ? err.message : "Login failed")
         }
       })
     }

     return (
       <main className="flex min-h-screen items-center justify-center bg-background">
         <div className="w-full max-w-sm space-y-6 rounded-xl border border-border bg-card p-8 shadow-sm">
           <div className="space-y-1 text-center">
             <h1 className="text-2xl font-semibold tracking-tight">Forge</h1>
             <p className="text-sm text-muted-foreground">Sign in to continue</p>
           </div>

           <form onSubmit={handleSubmit} className="space-y-4">
             <div className="space-y-1.5">
               <label htmlFor="username" className="text-sm font-medium">
                 Username
               </label>
               <input
                 id="username"
                 name="username"
                 type="text"
                 required
                 autoComplete="username"
                 autoFocus
                 className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                 placeholder="admin"
               />
             </div>

             <div className="space-y-1.5">
               <label htmlFor="password" className="text-sm font-medium">
                 Password
               </label>
               <input
                 id="password"
                 name="password"
                 type="password"
                 required
                 autoComplete="current-password"
                 className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
               />
             </div>

             {error && (
               <p className="text-sm text-destructive" role="alert">
                 {error}
               </p>
             )}

             <Button type="submit" className="w-full" disabled={isPending}>
               {isPending ? "Signing in..." : "Sign in"}
             </Button>
           </form>
         </div>
       </main>
     )
   }
   ```

2. Create frontend/src/app/(protected)/layout.tsx — client-side auth guard for all protected routes:
   ```typescript
   "use client"

   import { useEffect } from "react"
   import { useRouter } from "next/navigation"
   import { useAuth } from "@/context/auth-context"

   export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
     const { token, isLoading } = useAuth()
     const router = useRouter()

     useEffect(() => {
       if (!isLoading && !token) {
         router.replace("/login")
       }
     }, [token, isLoading, router])

     if (isLoading) {
       return (
         <div className="flex min-h-screen items-center justify-center">
           <span className="text-sm text-muted-foreground">Loading...</span>
         </div>
       )
     }

     if (!token) return null  // redirect in progress

     return <>{children}</>
   }
   ```

3. Create frontend/src/app/(protected)/page.tsx — home page with logout:
   ```typescript
   "use client"

   import { useRouter } from "next/navigation"
   import { useAuth } from "@/context/auth-context"
   import { Button } from "@/components/ui/button"

   export default function HomePage() {
     const { user, logout } = useAuth()
     const router = useRouter()

     async function handleLogout() {
       await logout()
       router.push("/login")
     }

     return (
       <main className="flex min-h-screen flex-col items-center justify-center gap-4">
         <h1 className="text-2xl font-bold">Forge</h1>
         {user && (
           <p className="text-sm text-muted-foreground">Signed in as {user.username}</p>
         )}
         <Button variant="outline" onClick={handleLogout}>
           Sign out
         </Button>
       </main>
     )
   }
   ```

4. Update frontend/src/app/page.tsx — root page now redirects to protected home:
   The route group (protected) handles / — remove the old page.tsx content and instead redirect to the home inside the protected group, OR move the root page.tsx into (protected)/page.tsx and have root page redirect:
   ```typescript
   // frontend/src/app/page.tsx
   import { redirect } from "next/navigation"

   export default function RootPage() {
     redirect("/")  // The (protected) layout wraps /, so just render redirect
   }
   ```
   Actually, since (protected)/page.tsx IS the "/" route (Next.js route groups don't add path segments), the original app/page.tsx conflicts. Replace app/page.tsx content with the home page content (which will be in (protected)/page.tsx), OR keep (protected)/page.tsx as the home and delete/empty app/page.tsx if it conflicts. Verify: with route group `(protected)`, the file `(protected)/page.tsx` maps to `/`. The file `app/page.tsx` also maps to `/` — this creates a conflict. Solution: remove app/page.tsx entirely (its content moved to (protected)/page.tsx).
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit 2>&1 | head -30 && npm run lint 2>&1 | tail -10</automated>
  </verify>
  <done>
    TypeScript and ESLint both pass. Login page exists at /login. Protected layout wraps all routes under (protected). Logout button is visible on home page. No page.tsx conflict (root app/page.tsx removed or redirects correctly).
  </done>
</task>

</tasks>

<verification>
TypeScript check:
```bash
cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit
```

ESLint check:
```bash
cd /Users/przbadu/dev/claude-clone/frontend && npm run lint
```

Build check (catches route conflicts and import errors):
```bash
cd /Users/przbadu/dev/claude-clone/frontend && npm run build 2>&1 | tail -30
```
</verification>

<success_criteria>
- `npx tsc --noEmit` passes with no errors
- `npm run lint` passes with no errors
- `npm run build` succeeds (no route conflicts, no missing imports)
- src/proxy.ts exists (not middleware.ts)
- Login page renders at /login with username/password form
- AuthProvider wraps the layout
- Protected layout redirects to /login when no token
</success_criteria>

<output>
After completion, create `.planning/phases/02-authentication/02-02-SUMMARY.md` with:
- What was built (pages, context, proxy)
- Key implementation decisions (proxy vs middleware, cookie handling, token refresh timing)
- Actual files created/modified
- Any deviations from plan and why
</output>

---
phase: 02-authentication
plan: 03
type: execute
wave: 3
depends_on:
  - 02-01
  - 02-02
files_modified:
  - backend/app/tests/test_auth_integration.py
  - frontend/src/__tests__/auth.test.tsx
  - frontend/tests/auth.spec.ts
  - frontend/playwright.config.ts
autonomous: true
requirements:
  - AUTH-02
  - AUTH-03
  - AUTH-04

must_haves:
  truths:
    - "pytest auth integration tests pass: login, refresh, logout, me, route protection"
    - "Vitest component tests pass: login form renders, submits, shows errors, handles loading state"
    - "Playwright E2E tests pass: full login flow, session persists after refresh, logout redirects"
  artifacts:
    - path: "backend/app/tests/test_auth_integration.py"
      provides: "Integration tests verifying the full auth token lifecycle"
      contains: "test_token_refresh_cycle"
    - path: "frontend/src/__tests__/auth.test.tsx"
      provides: "Component tests for login page behavior"
      contains: "renders login form"
    - path: "frontend/tests/auth.spec.ts"
      provides: "Playwright E2E: login, persist session, logout"
      contains: "redirects to login when unauthenticated"
    - path: "frontend/playwright.config.ts"
      provides: "Playwright config targeting localhost:3000"
  key_links:
    - from: "frontend/tests/auth.spec.ts"
      to: "backend FastAPI app"
      via: "Real HTTP calls to localhost:8000 during E2E tests"
      pattern: "localhost:8000"
---

<objective>
Implement auth test coverage: backend integration tests for the full token lifecycle, Vitest component tests for the login page, and Playwright E2E tests for the complete auth flow.

Purpose: Validates AUTH-02 (session persistence), AUTH-03 (logout), AUTH-04 (route protection) end-to-end. Provides regression protection for all future phases.
Output: Passing pytest integration tests, Vitest component tests, Playwright E2E tests.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/02-authentication/2-CONTEXT.md
@.planning/phases/02-authentication/02-01-SUMMARY.md
@.planning/phases/02-authentication/02-02-SUMMARY.md
</context>

<interfaces>
<!-- Key interfaces from Plans 01 and 02. -->

Backend test fixtures (from backend/app/tests/conftest.py):
```python
@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as ac:
        yield ac

# Added by Plan 01:
@pytest_asyncio.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    resp = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "changeme"})
    token = resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

Frontend auth functions (from Plan 02):
```typescript
// src/lib/auth.ts
export function loginApi(username: string, password: string): Promise<TokenResponse>
export function refreshApi(): Promise<TokenResponse>
export function logoutApi(): Promise<void>

// src/context/auth-context.tsx
export function AuthProvider({ children }: { children: React.ReactNode })
export function useAuth(): { token, user, isLoading, login, logout }
```

Backend auth endpoints (from Plan 01):
```
POST /api/v1/auth/login → 200 | 401
POST /api/v1/auth/refresh → 200 | 401 (uses forge_refresh cookie)
POST /api/v1/auth/logout → 200 (clears cookie)
GET /api/v1/auth/me → 200 | 401
GET /api/v1/health → 401 (protected)
```
</interfaces>

<tasks>

<task type="auto">
  <name>Task 1: Backend integration tests for full token lifecycle</name>
  <files>
    backend/app/tests/test_auth_integration.py
  </files>
  <action>
Create backend/app/tests/test_auth_integration.py with integration tests covering the full auth lifecycle. These tests are distinct from the unit tests in test_auth.py — they test multi-step flows:

```python
"""
Integration tests for auth token lifecycle:
- Full login → protected call → refresh → protected call cycle
- Cookie handling across requests
- Token expiry simulation
- Concurrent request behavior
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_token_lifecycle(client: AsyncClient) -> None:
    """Login, use access token, refresh, use new token."""
    # 1. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "changeme"},
    )
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]
    assert "forge_refresh" in login_resp.cookies

    # 2. Access protected endpoint
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "admin"

    # 3. Refresh token — httpx AsyncClient propagates cookies automatically
    refresh_resp = await client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 200
    new_access_token = refresh_resp.json()["access_token"]
    assert new_access_token != access_token  # new token issued

    # 4. Use new access token
    me_resp2 = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {new_access_token}"},
    )
    assert me_resp2.status_code == 200


@pytest.mark.asyncio
async def test_logout_invalidates_session(client: AsyncClient) -> None:
    """After logout, refresh cookie is cleared and refresh returns 401."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "changeme"},
    )
    assert login_resp.status_code == 200

    logout_resp = await client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200

    # Refresh should now fail — cookie was cleared
    refresh_resp = await client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_without_token(client: AsyncClient) -> None:
    """All protected routes return 401 when no Bearer token provided."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_malformed_token(client: AsyncClient) -> None:
    """Malformed Bearer token returns 401."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.valid.jwt"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_without_cookie(client: AsyncClient) -> None:
    """Refresh endpoint returns 401 when no cookie is present."""
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_correct_user_data(auth_client: AsyncClient) -> None:
    """GET /auth/me returns expected fields."""
    response = await auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "hashed_password" not in data  # sensitive field must not be exposed
```
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/test_auth_integration.py -v</automated>
  </verify>
  <done>
    All integration tests pass. Full lifecycle test verifies login → access → refresh → access works end-to-end. Logout clears session. Protected routes return 401 without credentials.
  </done>
</task>

<task type="auto">
  <name>Task 2: Vitest component tests for login page and Playwright E2E tests</name>
  <files>
    frontend/src/__tests__/auth.test.tsx
    frontend/tests/auth.spec.ts
    frontend/playwright.config.ts
  </files>
  <action>
1. Create frontend/src/__tests__/auth.test.tsx — Vitest component tests for LoginPage:
   Note: These tests mock the auth context to avoid needing a real backend.

   ```typescript
   import { render, screen, waitFor } from "@testing-library/react"
   import userEvent from "@testing-library/user-event"
   import { vi, describe, it, expect, beforeEach } from "vitest"

   // Mock the auth context
   const mockLogin = vi.fn()
   vi.mock("@/context/auth-context", () => ({
     useAuth: () => ({
       login: mockLogin,
       token: null,
       user: null,
       isLoading: false,
       logout: vi.fn(),
     }),
     AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
   }))

   // Mock next/navigation
   const mockPush = vi.fn()
   vi.mock("next/navigation", () => ({
     useRouter: () => ({ push: mockPush, replace: vi.fn() }),
     useSearchParams: () => ({ get: () => null }),
   }))

   import LoginPage from "@/app/login/page"

   describe("LoginPage", () => {
     beforeEach(() => {
       vi.clearAllMocks()
     })

     it("renders username and password fields", () => {
       render(<LoginPage />)
       expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
       expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
       expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument()
     })

     it("calls login with entered credentials on submit", async () => {
       mockLogin.mockResolvedValueOnce(undefined)
       const user = userEvent.setup()
       render(<LoginPage />)

       await user.type(screen.getByLabelText(/username/i), "admin")
       await user.type(screen.getByLabelText(/password/i), "secret")
       await user.click(screen.getByRole("button", { name: /sign in/i }))

       await waitFor(() => {
         expect(mockLogin).toHaveBeenCalledWith("admin", "secret")
       })
     })

     it("redirects to / on successful login", async () => {
       mockLogin.mockResolvedValueOnce(undefined)
       const user = userEvent.setup()
       render(<LoginPage />)

       await user.type(screen.getByLabelText(/username/i), "admin")
       await user.type(screen.getByLabelText(/password/i), "changeme")
       await user.click(screen.getByRole("button", { name: /sign in/i }))

       await waitFor(() => {
         expect(mockPush).toHaveBeenCalledWith("/")
       })
     })

     it("shows error message on login failure", async () => {
       mockLogin.mockRejectedValueOnce(new Error("Incorrect username or password"))
       const user = userEvent.setup()
       render(<LoginPage />)

       await user.type(screen.getByLabelText(/username/i), "admin")
       await user.type(screen.getByLabelText(/password/i), "wrong")
       await user.click(screen.getByRole("button", { name: /sign in/i }))

       await waitFor(() => {
         expect(screen.getByRole("alert")).toHaveTextContent("Incorrect username or password")
       })
     })

     it("disables submit button while login is pending", async () => {
       let resolveLogin!: () => void
       mockLogin.mockReturnValueOnce(new Promise<void>((res) => { resolveLogin = res }))
       const user = userEvent.setup()
       render(<LoginPage />)

       await user.type(screen.getByLabelText(/username/i), "admin")
       await user.type(screen.getByLabelText(/password/i), "changeme")
       await user.click(screen.getByRole("button", { name: /sign in/i }))

       expect(screen.getByRole("button", { name: /signing in/i })).toBeDisabled()
       resolveLogin()
     })
   })
   ```

2. Create frontend/playwright.config.ts if it does not exist:
   ```typescript
   import { defineConfig, devices } from "@playwright/test"

   export default defineConfig({
     testDir: "./tests",
     fullyParallel: false,
     forbidOnly: !!process.env.CI,
     retries: process.env.CI ? 2 : 0,
     workers: 1,
     reporter: "list",
     use: {
       baseURL: "http://localhost:3000",
       trace: "on-first-retry",
     },
     projects: [
       {
         name: "chromium",
         use: { ...devices["Desktop Chrome"] },
       },
     ],
     // Do NOT start webServer automatically — start frontend + backend manually before E2E
   })
   ```

3. Create frontend/tests/auth.spec.ts — Playwright E2E tests:
   These tests require both frontend (localhost:3000) and backend (localhost:8000) running. They test the real auth flow end-to-end.

   ```typescript
   import { test, expect } from "@playwright/test"

   test.describe("Authentication flow", () => {
     test("redirects to /login when unauthenticated", async ({ page }) => {
       // Clear all cookies first
       await page.context().clearCookies()
       await page.goto("/")
       await expect(page).toHaveURL(/\/login/)
     })

     test("shows login form with username and password fields", async ({ page }) => {
       await page.goto("/login")
       await expect(page.getByLabel(/username/i)).toBeVisible()
       await expect(page.getByLabel(/password/i)).toBeVisible()
       await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible()
     })

     test("shows error for invalid credentials", async ({ page }) => {
       await page.goto("/login")
       await page.getByLabel(/username/i).fill("admin")
       await page.getByLabel(/password/i).fill("wrongpassword")
       await page.getByRole("button", { name: /sign in/i }).click()
       await expect(page.getByRole("alert")).toBeVisible()
     })

     test("successful login redirects to home page", async ({ page }) => {
       await page.context().clearCookies()
       await page.goto("/login")
       await page.getByLabel(/username/i).fill("admin")
       await page.getByLabel(/password/i).fill("changeme")
       await page.getByRole("button", { name: /sign in/i }).click()
       await expect(page).toHaveURL("/")
       await expect(page.getByText(/signed in as admin/i)).toBeVisible()
     })

     test("session persists after page refresh", async ({ page }) => {
       // Login first
       await page.context().clearCookies()
       await page.goto("/login")
       await page.getByLabel(/username/i).fill("admin")
       await page.getByLabel(/password/i).fill("changeme")
       await page.getByRole("button", { name: /sign in/i }).click()
       await expect(page).toHaveURL("/")

       // Refresh — auth context should restore session via refresh endpoint
       await page.reload()
       await expect(page).toHaveURL("/")
       await expect(page.getByText(/signed in as admin/i)).toBeVisible()
     })

     test("logout redirects to login and clears session", async ({ page }) => {
       // Login first
       await page.context().clearCookies()
       await page.goto("/login")
       await page.getByLabel(/username/i).fill("admin")
       await page.getByLabel(/password/i).fill("changeme")
       await page.getByRole("button", { name: /sign in/i }).click()
       await expect(page).toHaveURL("/")

       // Click logout
       await page.getByRole("button", { name: /sign out/i }).click()
       await expect(page).toHaveURL(/\/login/)

       // Navigating to protected route should redirect to login again
       await page.goto("/")
       await expect(page).toHaveURL(/\/login/)
     })
   })
   ```

4. Install Playwright browsers if not already installed:
   ```bash
   cd /Users/przbadu/dev/claude-clone/frontend && npx playwright install chromium --with-deps 2>/dev/null || npx playwright install chromium
   ```
   Note: Playwright browsers are installed separately from the npm package. This step is automated — no human action needed.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npx vitest run src/__tests__/auth.test.tsx 2>&1 | tail -20</automated>
  </verify>
  <done>
    Vitest component tests pass (5 tests in auth.test.tsx). playwright.config.ts exists targeting localhost:3000. E2E test file exists with 5 scenarios. Playwright browsers installed for chromium. Note: E2E tests require running servers — they are verified structurally (TypeScript compiles) but run only with `npx playwright test` when servers are live.
  </done>
</task>

</tasks>

<verification>
Backend integration tests:
```bash
cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/ -v 2>&1 | tail -30
```

Frontend component tests:
```bash
cd /Users/przbadu/dev/claude-clone/frontend && npx vitest run 2>&1 | tail -20
```

E2E tests (requires both servers running):
```bash
# Terminal 1: cd backend && uvicorn app.main:app --reload
# Terminal 2: cd frontend && npm run dev
# Terminal 3:
cd /Users/przbadu/dev/claude-clone/frontend && npx playwright test tests/auth.spec.ts --reporter=list
```
</verification>

<success_criteria>
- All backend tests pass: pytest reports 0 failures across test_security.py, test_auth.py, test_auth_integration.py
- Vitest component tests pass: 5 tests in auth.test.tsx all green
- E2E test file compiles (TypeScript passes): `npx tsc --noEmit` succeeds
- Playwright config correctly targets localhost:3000
- E2E tests pass when both servers are running (full auth flow verified)
</success_criteria>

<output>
After completion, create `.planning/phases/02-authentication/02-03-SUMMARY.md` with:
- Test counts and what they cover
- E2E test prerequisites (how to run both servers)
- Any test infrastructure decisions (mocking strategy, fixtures)
- Coverage gaps noted for Phase 11 quality gate
</output>
