---
phase: 12-pwa-foundation
plan: 01
subsystem: pwa
tags: [serwist, service-worker, manifest, pwa, next-js, offline]

# Dependency graph
requires:
  - phase: 12-00
    provides: "Wave 0 tests (manifest.test.ts, sw-registration.test.tsx)"
provides:
  - "Web app manifest at /manifest.webmanifest with Forge branding"
  - "Service worker with app shell caching and /api/* NetworkOnly bypass"
  - "PWA icons (192x192, 512x512, apple-touch-icon)"
  - "SW registration client component wired into providers"
  - "Serwist webpack plugin integration in next.config.ts"
affects: [12-02-offline-page, 12-03-install-prompt, docker-build]

# Tech tracking
tech-stack:
  added: ["@serwist/next@^9.5.7", "serwist@^9.5.7"]
  patterns: ["Serwist webpack plugin wrapping next.config.ts", "NetworkOnly for SSE-safe API bypass", "Client component for SW registration inside providers"]

key-files:
  created:
    - frontend/src/app/manifest.ts
    - frontend/src/app/sw.ts
    - frontend/src/components/sw-register.tsx
    - frontend/scripts/generate-icons.mjs
    - frontend/public/icons/icon-192x192.png
    - frontend/public/icons/icon-512x512.png
    - frontend/public/icons/apple-touch-icon.png
  modified:
    - frontend/next.config.ts
    - frontend/tsconfig.json
    - frontend/.gitignore
    - frontend/src/components/providers.tsx
    - frontend/src/app/layout.tsx
    - frontend/package.json

key-decisions:
  - "Use 'matcher' property instead of 'urlPattern' for Serwist v9 RuntimeCaching API"
  - "Force --webpack flag for builds since Serwist requires webpack plugin for SW generation"
  - "Add turbopack:{} to next.config.ts to silence Next.js 16 Turbopack warning"

patterns-established:
  - "PWA service worker: sw.ts in src/app/ compiled by Serwist webpack plugin to public/sw.js"
  - "API routes bypass: NetworkOnly matcher for /api/* BEFORE defaultCache in runtimeCaching"
  - "SW registration: dedicated client component in providers tree, not in layout"

requirements-completed: [PWA-01, PWA-02, PWA-03, PWA-05]

# Metrics
duration: 5min
completed: 2026-03-22
---

# Phase 12 Plan 01: Serwist PWA Integration Summary

**Serwist service worker with app shell caching, NetworkOnly API bypass for SSE, web app manifest, and PWA icons for installable Forge app**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-22T11:03:31Z
- **Completed:** 2026-03-22T11:08:32Z
- **Tasks:** 3
- **Files modified:** 13

## Accomplishments
- Installed @serwist/next and serwist for service worker generation and caching
- Created manifest.ts with display:standalone, Forge branding, and 3 icon sizes
- Created sw.ts with NetworkOnly for /api/* (SSE-safe) before defaultCache
- Generated PWA icons (192x192, 512x512, apple-touch-icon) via sharp script
- Wired SW registration into providers.tsx via dedicated client component
- Added PWA metadata (applicationName, appleWebApp, viewport themeColor) to layout
- Build succeeds with --webpack flag and produces public/sw.js

## Task Commits

Each task was committed atomically:

1. **Task 1: Install Serwist, create manifest, icons, and SW source** - `f8854e2` (feat)
2. **Task 2a: Wire Serwist into Next.js config, update tsconfig and gitignore** - `f24d84a` (chore)
3. **Task 2b: Create SW registration, wire into providers, update layout metadata** - `ba31edb` (feat)

## Files Created/Modified
- `frontend/src/app/manifest.ts` - Dynamic web app manifest with Forge branding
- `frontend/src/app/sw.ts` - Service worker with NetworkOnly API bypass and defaultCache
- `frontend/src/components/sw-register.tsx` - Client component for SW registration
- `frontend/scripts/generate-icons.mjs` - Sharp-based icon generation script
- `frontend/public/icons/icon-192x192.png` - PWA icon 192x192
- `frontend/public/icons/icon-512x512.png` - PWA icon 512x512
- `frontend/public/icons/apple-touch-icon.png` - Apple touch icon 180x180
- `frontend/next.config.ts` - Wrapped with withSerwist plugin, added SW headers
- `frontend/tsconfig.json` - Added @serwist/next/typings, webworker lib, sw.js exclude
- `frontend/.gitignore` - Added Serwist generated file patterns
- `frontend/src/components/providers.tsx` - Added ServiceWorkerRegister component
- `frontend/src/app/layout.tsx` - Added PWA metadata and viewport export
- `frontend/package.json` - Added serwist deps, dev:pwa script, --webpack build flag

## Decisions Made
- Used `matcher` property instead of `urlPattern` for Serwist v9 RuntimeCaching API (plan had incorrect property name)
- Added `--webpack` flag to build script because Next.js 16 defaults to Turbopack which does not support Serwist's webpack plugin for SW generation
- Added `turbopack: {}` to next.config.ts to silence Next.js 16 warning about webpack config without turbopack config

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed RuntimeCaching property name from urlPattern to matcher**
- **Found during:** Task 2b (build verification)
- **Issue:** Plan specified `urlPattern` property in sw.ts runtimeCaching entries, but Serwist v9 uses `matcher`
- **Fix:** Changed `urlPattern` to `matcher` in both /api/* entries
- **Files modified:** frontend/src/app/sw.ts
- **Verification:** TypeScript compilation succeeds, build passes
- **Committed in:** ba31edb (Task 2b commit)

**2. [Rule 3 - Blocking] Added --webpack flag to build script for Serwist compatibility**
- **Found during:** Task 2b (build verification)
- **Issue:** Next.js 16 defaults to Turbopack for builds, but Serwist only generates SW via webpack plugin. Build succeeded but sw.js was not produced.
- **Fix:** Updated build script from `next build` to `next build --webpack`, added `turbopack: {}` to config
- **Files modified:** frontend/package.json, frontend/next.config.ts
- **Verification:** Build produces public/sw.js, Serwist logs "Bundling the service worker script"
- **Committed in:** ba31edb (Task 2b commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes necessary for correctness. Serwist v9 API differs from plan's assumed API, and Next.js 16 Turbopack default required explicit webpack flag. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- PWA foundation complete with working service worker and manifest
- Ready for 12-02 (offline page) which will provide the /~offline precached route
- Ready for 12-03 (install prompt and responsive layout)
- Docker standalone build already copies public/ so sw.js will be included

## Self-Check: PASSED

All 7 created files verified present. All 3 task commits (f8854e2, f24d84a, ba31edb) verified in git log.

---
*Phase: 12-pwa-foundation*
*Completed: 2026-03-22*
