---
phase: 02-authentication
plan: "02"
subsystem: frontend-auth
tags: [auth, frontend, login, context, proxy, route-protection]
dependency_graph:
  requires: [02-01-backend-auth]
  provides: [frontend-auth-context, login-page, route-guard]
  affects: [frontend-layout, frontend-routes]
tech_stack:
  added: []
  patterns: [auth-context-provider, proxy-route-guard, token-in-memory, auto-refresh]
key_files:
  created:
    - frontend/src/lib/auth.ts
    - frontend/src/lib/api.ts
    - frontend/src/context/auth-context.tsx
    - frontend/src/proxy.ts
    - frontend/src/app/login/page.tsx
    - frontend/src/app/(protected)/layout.tsx
    - frontend/src/app/(protected)/page.tsx
  modified:
    - frontend/src/app/layout.tsx
    - frontend/src/__tests__/placeholder.test.tsx
  deleted:
    - frontend/src/app/page.tsx
decisions:
  - "proxy.ts (not middleware.ts) for Next.js 16 route guard convention"
  - "Named export `proxy` function (not default export) per Next.js 16 docs"
  - "Access token in React state only, refresh cookie handled by browser"
  - "Optimistic proxy check: cookie presence only, auth verified client-side on mount"
  - "Used @base-ui/react Button (already installed) instead of installing additional shadcn components"
metrics:
  duration: "2min"
  completed: "2026-03-21"
  tasks_completed: 2
  tasks_total: 2
---

# Phase 02 Plan 02: Frontend Authentication Summary

Frontend auth with login page, auth context for token management, proxy route guard, and auto-refresh using httpOnly cookie.

## What Was Built

### Auth API Library (auth.ts)
- `loginApi(username, password)` - POST to /api/v1/auth/login with credentials
- `refreshApi()` - POST to /api/v1/auth/refresh using httpOnly cookie
- `logoutApi()` - POST to /api/v1/auth/logout to clear cookie
- `meApi(token)` - GET /api/v1/auth/me with Bearer token

### API Fetch Wrapper (api.ts)
- `apiFetch(path, token, options)` - Injects Authorization header and credentials

### Auth Context (auth-context.tsx)
- AuthProvider wraps entire app, manages token + user state
- On mount: attempts refresh to restore session after page reload
- Auto-refresh: schedules token refresh 14 minutes after login (1 min before 15 min expiry)
- login/logout callbacks exposed via useAuth hook

### Proxy Route Guard (proxy.ts)
- Next.js 16 convention (middleware.ts is deprecated)
- Checks for `forge_refresh` cookie on non-public paths
- Redirects to /login with `from` query param if no cookie
- Matcher excludes _next/static, _next/image, api, favicon, and .png files

### Login Page (/login)
- Clean form with username/password fields
- Error display for failed login attempts
- Uses useTransition for non-blocking submit
- Redirects to original path (from query param) after login

### Protected Layout
- Client-side auth guard for all routes under (protected)
- Shows loading state during initial auth check
- Redirects to /login if no token after loading completes

### Home Page (/ via protected route group)
- Shows signed-in username
- Sign out button that clears token and redirects to /login

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Route conflict between app/page.tsx and (protected)/page.tsx**
- **Found during:** Task 2
- **Issue:** Both files mapped to `/` causing a Next.js route conflict
- **Fix:** Deleted app/page.tsx entirely since (protected)/page.tsx serves the same route
- **Commit:** 8c61919

**2. [Rule 3 - Blocking] Test imported deleted page component**
- **Found during:** Task 2
- **Issue:** placeholder.test.tsx imported from `../app/page` which was deleted
- **Fix:** Rewrote test to import from `../app/(protected)/page` with proper auth mocking
- **Commit:** 8c61919

**3. [Rule 1 - Bug] Named export for proxy function**
- **Found during:** Task 1
- **Issue:** Plan used `export default async function proxy` but Next.js 16 docs show `export function proxy` as the canonical pattern
- **Fix:** Used named export `export function proxy` (non-async since no await needed) matching docs exactly
- **Commit:** b5a83d6

## Verification Results

- `npx tsc --noEmit` - PASSED
- `npm run lint` - PASSED
- `npm test` - PASSED (3 tests)
- `npm run format:check` - PASSED

## Self-Check: PASSED

All 8 created/modified files verified present on disk. Both commit hashes (b5a83d6, 8c61919) verified in git log.
