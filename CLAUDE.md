<!-- GSD:project-start source:PROJECT.md -->
## Project

**Forge**

A local-first, self-hosted AI assistant application connecting to any OpenAI-compatible LLM endpoint. Forge provides streaming chat with markdown rendering, execution trace visibility for every tool call and MCP action, file upload with RAG retrieval and source attribution, MCP server management, agent skills, and comprehensive settings — all through a polished web interface built for transparency and control.

**Core Value:** Every AI interaction — chat, tool call, MCP action, skill execution — is visible, persisted, and reviewable. The user always knows what happened and why.

### Constraints

- **Frontend stack**: Next.js (App Router), TypeScript, shadcn/ui, Tailwind CSS — fixed
- **Backend stack**: Python 3.11+, FastAPI, Pydantic, SQLModel/SQLAlchemy, Alembic, SQLite, ChromaDB — fixed
- **Testing stack**: Vitest + Testing Library + Playwright (frontend), pytest + httpx + pytest-asyncio (backend) — mandatory
- **Quality gates**: ESLint + Prettier (frontend), Ruff + Black (backend), TypeScript strict mode, mypy — required
- **No agent framework**: Custom orchestration loop only; no LangGraph dependency
- **File storage**: `./uploads` directory served through controlled endpoints (not `./public`)
- **Streaming**: SSE for token streaming and trace events
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Scope
## Recommended Stack Additions
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `@serwist/next` | ^9.5.7 | Service worker integration for Next.js App Router | The maintained successor to next-pwa. Recommended by Next.js official PWA guide for offline support. Handles precaching, runtime caching, and offline fallbacks. Wraps the Next.js config cleanly. |
| `serwist` | ^9.5.7 (devDependency) | Service worker authoring runtime | Core library for writing `sw.ts`. Provides `defaultCache` strategies, precache manifest injection, and runtime caching. Compiled into SW bundle at build time, hence devDependency. |
| `@serwist/turbopack` | ^9.5.6 | Turbopack-compatible Serwist integration | Next.js 16 defaults to Turbopack for dev. Without this, you must use `next dev --webpack` to test SW in development. This package enables native Turbopack support. |
| Next.js built-in `manifest.ts` | native (16.2.1) | Web app manifest generation | App Router natively supports `app/manifest.ts` returning `MetadataRoute.Manifest`. Generates `/manifest.webmanifest` automatically. No library needed. |
### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `sharp` | ^0.33 | PWA icon generation | Generate required icon set (192x192, 512x512, maskable) from a single source image. Likely already installed by Next.js for image optimization -- check before adding. |
### Zero New Dependencies Required
| Feature | Implementation | Why No Library |
|---------|---------------|----------------|
| Responsive layout | Tailwind CSS v4 breakpoints (`sm:`, `md:`, `lg:`) | Already installed. Responsive design is CSS-only work on existing components. |
| Install prompt | Browser `beforeinstallprompt` API + `useState`/`useEffect` | ~40 lines of client component code. No library needed. |
| iOS install instructions | `navigator.userAgent` detection + UI component | Chromium fires `beforeinstallprompt`; iOS requires manual "Add to Home Screen" instructions. |
| Offline detection | `navigator.onLine` + `online`/`offline` events | Native browser API. Show banner when backend unreachable. |
| Standalone mode detection | `window.matchMedia('(display-mode: standalone)')` | Native CSS media query. Hide install prompt when already installed. |
## Installation
# Core PWA: service worker management
# Dev: SW compilation (compiles sw.ts -> public/sw.js)
# Turbopack support for dev server
## Integration Points with Existing Stack
### 1. next.config.ts Modification
### 2. Web App Manifest (app/manifest.ts)
### 3. Service Worker (app/sw.ts)
- **Precaching:** App shell (HTML, CSS, JS bundles) for instant loads
- **Runtime caching:** Configurable per-route strategies
- **Offline fallback:** Serve a cached "Forge is offline" page when backend is unreachable
### 4. Caching Strategy (Architecturally Critical)
| Resource Type | Strategy | Rationale |
|---------------|----------|-----------|
| App shell (HTML/CSS/JS) | `StaleWhileRevalidate` | Fast loads from cache, background update for freshness |
| Static assets (icons, fonts) | `CacheFirst` | Immutable content, cache indefinitely |
| API calls (`/api/*`) | `NetworkOnly` | Forge requires live backend for all LLM functionality |
| SSE streams | `NetworkOnly` | Streaming responses cannot be cached |
| Offline fallback | Precached HTML | Show "Forge is offline -- check your backend" with retry |
### 5. Responsive Layout
- `sm:` (640px) -- mobile landscape
- `md:` (768px) -- tablet, sidebar collapse point
- `lg:` (1024px) -- desktop, full sidebar
### 6. Install Prompt
- **Chromium (Chrome, Edge, etc.):** Capture `beforeinstallprompt` event, show custom install button
- **Safari/iOS:** Detect iOS via user agent, show manual "Add to Home Screen" instructions
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `@serwist/next` for service worker | Hand-written `public/sw.js` (no build tool) | Only for trivial SWs (push notifications only, no precaching). Next.js official guide shows this simpler approach but it lacks precaching, versioning, and cache management. |
| `@serwist/turbopack` for dev | `next dev --webpack` flag | If `@serwist/turbopack` has compatibility issues with Next.js 16.2.1. Webpack fallback always works but dev server is slower. |
| Tailwind breakpoints for responsive | CSS Container Queries | If individual components need to respond to container size rather than viewport. Tailwind v4 supports `@container` but viewport breakpoints should cover Forge's layout needs. |
| Dynamic `app/manifest.ts` | Static `public/manifest.json` | If you never need dynamic manifest values. Dynamic is better because it can adapt `theme_color` to match light/dark theme. |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `next-pwa` | Abandoned 2+ years, does not support App Router, stale Workbox version with known issues | `@serwist/next` (its maintained successor) |
| `@ducanh2912/next-pwa` | Fork with some updates but Serwist has surpassed it in features, maintenance, and community | `@serwist/next` |
| `workbox-*` (direct imports) | Serwist is a Workbox fork with better Next.js integration. Raw Workbox adds unnecessary wiring | `serwist` (wraps Workbox patterns) |
| `web-push` / VAPID keys | Push notifications are out of scope for v2.1. Forge is local-first -- push adds complexity for zero value | Not needed. Defer if ever required. |
| `idb` / `localforage` / IndexedDB wrappers | Offline data sync adds massive complexity. Forge requires live backend for LLM -- cached data is useless | Service worker offline shell is sufficient |
| Any CSS framework additions | Tailwind CSS v4 already handles responsive via breakpoints. Adding Bootstrap, Chakra, etc. would conflict | Tailwind breakpoints + existing shadcn/ui |
| `pwa-asset-generator` | Heavy CLI tool for icon generation. Over-engineered for a one-time task | `sharp` script or online favicon generator |
## Version Compatibility
| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `@serwist/next@^9.5` | Next.js 14-16, App Router | Production builds use webpack (standard for Next.js). Verified working with App Router. |
| `@serwist/turbopack@^9.5` | Next.js 15-16 | Dev server only. Production builds still use webpack via `@serwist/next`. |
| `serwist@^9.5` | `@serwist/next@^9.5` | Must match major+minor version with `@serwist/next`. Always install same version. |
| `manifest.ts` (built-in) | Next.js 13.4+ (App Router) | Part of Next.js metadata file conventions. No version concern with 16.2.1. |
## Development Workflow Impact
### Turbopack + Service Worker
### .gitignore Additions
# Serwist generated service worker
### Testing PWA Features
- **Localhost is secure:** Service workers work on `localhost` without HTTPS.
- **LAN testing:** Use `next dev --experimental-https` for testing on mobile devices over local network.
- **Playwright:** Test SW registration via `page.evaluate(() => navigator.serviceWorker.ready)`.
- **Manifest validation:** Chrome DevTools > Application > Manifest panel.
- **Lighthouse:** Run PWA audit to verify installability criteria.
### Security Headers
## Sources
- [Next.js Official PWA Guide](https://nextjs.org/docs/app/guides/progressive-web-apps) -- Primary source, updated 2026-02-11, HIGH confidence
- [Next.js manifest.ts API Reference](https://nextjs.org/docs/app/api-reference/file-conventions/metadata/manifest) -- Built-in manifest support, HIGH confidence
- [Serwist Getting Started with Next.js](https://serwist.pages.dev/docs/next/getting-started) -- Official Serwist docs, HIGH confidence
- [@serwist/next on npm](https://www.npmjs.com/package/@serwist/next) -- Version 9.5.7, published March 2026, HIGH confidence
- [@serwist/turbopack on npm](https://www.npmjs.com/package/@serwist/turbopack) -- Version 9.5.6, HIGH confidence
- [serwist on npm](https://www.npmjs.com/package/serwist) -- Version 9.5.7, HIGH confidence
- [MDN: beforeinstallprompt](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeinstallprompt_event) -- Browser API reference, HIGH confidence
- [web.dev: Installation Prompt](https://web.dev/learn/pwa/installation-prompt) -- PWA install UX patterns, HIGH confidence
- [LogRocket: Next.js 16 PWA with offline support](https://blog.logrocket.com/nextjs-16-pwa-offline-support/) -- Community verification, MEDIUM confidence
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
