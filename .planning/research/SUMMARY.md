# Project Research Summary

**Project:** Forge v2.1 — PWA Capabilities
**Domain:** Progressive Web App integration into existing Next.js 16 AI chat application
**Researched:** 2026-03-22
**Confidence:** HIGH

## Executive Summary

Forge v2.1 adds PWA capabilities to a fully functional v1.0 AI chat application built on Next.js 16 App Router, React 19, Tailwind CSS v4, and a FastAPI backend. The scope is precisely defined: installability, mobile responsiveness, and offline shell — not full offline-first functionality. Forge requires a live backend (Ollama, OpenAI, or other LLM APIs) for all meaningful operations, so the service worker's role is limited to caching the app shell for instant loads and providing graceful degradation when the backend is unreachable. This architectural constraint simplifies the caching strategy considerably and eliminates the need for complex offline data sync.

The recommended approach uses `@serwist/next` (the maintained successor to the abandoned `next-pwa`) for service worker generation, Next.js's built-in `app/manifest.ts` convention for the web app manifest, and existing Tailwind CSS breakpoints for responsive layout. Total new dependencies are exactly three packages. Most PWA infrastructure (install prompt, offline detection, standalone mode detection) is implemented using native browser APIs with no additional libraries. This keeps the footprint minimal and avoids build-tool conflicts with Next.js 16's Turbopack dev server.

The most significant risks center on the service worker's interaction with Forge's existing SSE streaming architecture. Forge uses `fetch()` + `ReadableStream` for token-by-token AI responses — a pattern that looks like a normal POST request to the service worker and will be intercepted unless explicitly bypassed. This is the highest-priority technical risk and must be validated first in Phase 1. Secondary risks include the service worker missing from Docker deployments (standalone output mode requires explicit `public/` copying in the Dockerfile) and users stuck on old cached versions after deployment (solved with `skipWaiting()` + `clients.claim()` plus an update notification banner).

## Key Findings

### Recommended Stack

The existing stack requires minimal additions. `@serwist/next@^9.5.7` handles service worker generation and Next.js build integration. `serwist@^9.5.7` (devDependency) provides the service worker runtime API for writing typed `sw.ts`. `@serwist/turbopack@^9.5.6` enables Turbopack-compatible SW generation for local development. The `next-pwa` package — the most commonly found search result — is abandoned (last release 2022), incompatible with Next.js 15+, and must not be used.

**Core technologies:**
- `@serwist/next@^9.5.7`: Service worker generation via Next.js build — maintained successor to next-pwa, verified working with App Router and standalone output
- `serwist@^9.5.7` (dev): Service worker runtime — Workbox-based, type-safe SW authoring, compiles `sw.ts` to `public/sw.js`
- `@serwist/turbopack@^9.5.6`: Turbopack dev compatibility — enables SW testing without requiring `--webpack` flag fallback
- Native `app/manifest.ts`: Web app manifest — built into Next.js 16, no library needed, TypeScript-typed
- Browser APIs only: Install prompt, offline detection, standalone detection — ~40-60 lines of React code, zero additional packages

**Do not use:** `next-pwa` (abandoned, webpack-only), `@ducanh2912/next-pwa` (superseded by Serwist), raw `workbox-*` imports, `web-push`/VAPID keys (out of scope), any IndexedDB wrappers (offline sync is an anti-feature for Forge).

### Expected Features

The research distinguishes sharply between PWA table stakes (required for the app to be genuinely installable and mobile-usable) and differentiators (features that put Forge ahead of competitors like Open WebUI and Claude.ai, which are not PWAs at all).

**Must have (table stakes — P1):**
- Web App Manifest with name, icons (192x192 + 512x512 + maskable), display mode, theme_color — installability gate
- Service worker with app shell caching — installability gate and instant load foundation
- Install prompt UX for Chrome/Edge (`beforeinstallprompt`) and iOS (manual "Add to Home Screen" instructions)
- Responsive chat layout with collapsible sidebar — the current fixed `w-64` sidebar is completely broken on mobile
- Responsive header with hamburger menu and mobile Sheet drawer — navigation must work on small screens
- Offline shell with clear "you're offline" state — graceful degradation when backend unreachable
- Theme color meta tags, app icons, security headers for SW, viewport meta verification

**Should have (differentiators — P2, add after core passes Lighthouse):**
- Offline conversation history (read-only cached API responses)
- Smart reconnection UX (auto-retry + "back online" toast)
- Swipe gestures for sidebar toggle on touch devices
- Settings page touch-target and stacking adjustments
- Standalone mode navigation verification (back button behavior without browser chrome)

**Defer (v3+):**
- Push notifications — requires VAPID keys + notification server; no value for synchronous single-user chat
- Background sync / full offline chat — backend dependency makes this a false promise
- IndexedDB data mirror — full offline-first would require mirroring a complex SQLite schema
- Bottom navigation bar — design paradigm conflict with existing top header + sidebar
- Voice/audio input — product feature, not PWA infrastructure

**Key competitive insight:** Claude.ai and Open WebUI are NOT PWAs. ChatGPT is the only major AI chat with full PWA support. Making Forge installable puts it ahead of most self-hosted alternatives.

### Architecture Approach

The PWA integration adds a thin infrastructure layer over the existing Next.js App Router structure. Three new files are purely additive (`manifest.ts`, `sw.ts`, `~offline/page.tsx`). Two new components handle SW lifecycle in isolation (`ServiceWorkerRegistration.tsx` in `providers.tsx`, `InstallPrompt.tsx`). The responsive layout changes modify three existing files (`chat/layout.tsx`, `app-header.tsx`, `settings/layout.tsx`) and introduce one new hook (`useSidebar`).

The critical architectural decisions are: (1) NetworkOnly for all `/api/*` routes in the service worker — SSE streaming cannot be cached and chat data must always be fresh; (2) CSS-first responsive design using Tailwind breakpoints (`hidden md:block`) with JS state only for drawer open/close toggle — prevents hydration mismatches from server/client layout divergence; (3) SW registration in a dedicated client component inside `providers.tsx`, never in root layout (a server component).

**Major components:**
1. `sw.ts` / `public/sw.js` — Service worker with precache manifest, NetworkOnly for `/api/*`, StaleWhileRevalidate for app shell, offline fallback to `/~offline`
2. `manifest.ts` — Dynamic TypeScript manifest with theme-aware `theme_color`, `start_url: "/chat"`, icon references
3. `ServiceWorkerRegistration.tsx` — Client component in providers; registers SW, handles update detection and notification
4. `InstallPrompt.tsx` — Client component; captures `beforeinstallprompt` for Chromium, detects iOS, hides when `display-mode: standalone`
5. `useSidebar` hook — Manages mobile drawer open/close state; CSS breakpoints control desktop visibility without JS
6. Modified `chat/layout.tsx` — Sidebar hidden on mobile via `hidden md:block`, renders in shadcn Sheet drawer triggered by hamburger button
7. `~offline/page.tsx` — Static server component served as offline fallback; matches Forge visual style

**Key pattern:** Forge's cross-origin API architecture (frontend port 3000, backend port 8000) means the service worker cannot intercept API calls even if you wanted it to — the SW scope is same-origin only. This is a feature: the SW handles only the app shell, and API responses are never cached.

### Critical Pitfalls

1. **SSE streaming intercepted by service worker** — Forge uses `fetch()` + `ReadableStream` for token streaming, which looks like a normal POST to the SW (not `text/event-stream` Accept header, so standard SSE bypass checks fail). The SW buffers or corrupts the stream. Prevention: place `NetworkOnly` rule for `/api/*` first in `runtimeCaching` array so it matches before default rules. Validate immediately after SW registration — this is the most likely regression.

2. **SW missing from Docker standalone output** — `output: "standalone"` does NOT copy `public/` into the Docker image. SW works in dev, is silently absent in production. Prevention: add `COPY --from=builder /app/public ./public` to Dockerfile. Verify with `curl /sw.js` in the running container.

3. **Users stuck on stale cached app version** — SW lifecycle holds users on old versions indefinitely after deployment. Prevention: `skipWaiting()` + `clients.claim()` in the SW, plus an "Update available" toast with user-triggered reload. Register SW with `updateViaCache: 'none'`.

4. **Cached authenticated API responses served cross-session** — If any `/api/*` route is accidentally cached, stale or wrong-user data appears after logout/login. Prevention: never cache API responses in the SW. Clear all caches on logout via `postMessage`.

5. **Manifest + cookie auth — PWA opens to login screen** — `SameSite=Strict` cookies are not sent on PWA standalone launches. Prevention: set refresh token cookie to `SameSite=Lax`. Test full install-close-reopen cycle to verify auth persists.

## Implications for Roadmap

Based on research, the architecture file's suggested 3-phase build order aligns precisely with feature dependencies and pitfall mitigation priorities. Phases are independent enough to deploy incrementally, with Phase 1 carrying the highest config-change risk and Phase 3 touching the most existing code.

### Phase 1: PWA Foundation

**Rationale:** Service worker and manifest are technical prerequisites for install prompt, offline features, and Lighthouse audit compliance. This phase has zero visual impact on existing desktop users and can be safely deployed to production independently. Config changes to `next.config.ts` carry the most risk of breaking the build — doing this first surfaces issues before other work depends on it.

**Delivers:** Fully installable PWA passing Lighthouse PWA audit. App shell loads instantly from cache. Offline fallback page shown instead of browser error. No user-visible behavior change for existing desktop users.

**Addresses:** Web App Manifest, App Icons, Service Worker + App Shell Caching, Offline Shell with Graceful Degradation, Security Headers for SW, Theme Color Meta Tags, Viewport Meta, `~offline` page

**Avoids:**
- Pitfall 1 (SSE streaming intercepted) — NetworkOnly rule for `/api/*` implemented and tested here
- Pitfall 2 (cached auth data) — caching architecture decided here: only app shell, never API responses
- Pitfall 3 (SW missing from Docker) — Dockerfile verified here before any deployment assumption is made
- Pitfall 7 (next-pwa abandoned) — technology decision already made; Serwist selected

**Steps:** Install `@serwist/next` + `serwist` + `@serwist/turbopack`, wrap `next.config.ts`, add webworker types to `tsconfig.json`, create `sw.ts` with NetworkOnly for `/api/*`, create `manifest.ts`, generate PWA icons, create `~offline/page.tsx`, update `.gitignore`, add `dev:pwa` npm script.

**Needs research:** No — official Next.js PWA guide and Serwist docs are complete and current for Next.js 16.2.1. Implementation is copy-pasteable.

### Phase 2: Install UX and Offline Experience

**Rationale:** Depends on Phase 1 (SW must be registered before `beforeinstallprompt` fires; offline features require cached shell assets from Phase 1). Small surface area — new components only, no modifications to existing code. Validates the install flow end-to-end including auth persistence in standalone mode.

**Delivers:** Users can discover and install the PWA on desktop and mobile. Offline state communicated clearly via banner and disabled input. Service worker update lifecycle handled gracefully with user notification.

**Addresses:** Install Prompt UX (Chrome/Edge + iOS), Offline Conversation History (P2), Smart Reconnection UX (P2), SW Update Notification, Standalone Navigation Verification

**Avoids:**
- Pitfall 4 (manifest + auth cookie) — `SameSite=Lax` fix tested and verified here with full install-close-reopen cycle
- Pitfall 5 (cache invalidation) — `skipWaiting()` + update banner implemented here before first production deployment
- Pitfall 6 (silent offline failures) — offline state indicator and disabled send button implemented here

**Steps:** Create `ServiceWorkerRegistration.tsx` + mount in `providers.tsx`, create `InstallPrompt.tsx` (beforeinstallprompt + iOS detection + standalone hide), add online/offline event listeners and status banner in AppHeader, implement SW update notification toast.

**Needs research:** No — standard browser API patterns, well-documented. Auth cookie `SameSite` fix is a one-line backend change.

### Phase 3: Responsive Layout

**Rationale:** Technically independent of service worker (can be built in parallel with Phases 1-2), but placed last to allow integration testing on an actually-installed PWA in standalone mode. The sidebar refactor touches the most existing code and has the most risk of visual regression on existing desktop users. Benefits from Phase 1+2 being stable first.

**Delivers:** Forge is fully usable on mobile. Sidebar collapses to a Sheet drawer on screens under 768px. Header adapts with hamburger menu. All existing features (chat, traces, settings, file upload) are usable at 375px width. No horizontal scroll at any breakpoint.

**Addresses:** Responsive Chat Layout (collapsible sidebar drawer), Responsive Header (hamburger + Sheet), Responsive Settings Page, MessageBubble mobile width, Swipe Gestures for sidebar (P2), Touch target audit (>= 44px), Standalone display mode navigation

**Avoids:**
- Anti-pattern: JS-driven responsive layout causing hydration mismatches — CSS-first breakpoints with minimal JS drawer state
- Anti-pattern: `window.innerWidth` checks on server components
- Existing SSE streaming and auth flows are not modified in this phase

**Steps:** Create `useSidebar` hook, modify `chat/layout.tsx` (sidebar `hidden md:block`, Sheet drawer for mobile), modify `app-header.tsx` (hamburger trigger on mobile, responsive nav), adjust `settings/layout.tsx` padding, adjust `MessageBubble.tsx` max-width for mobile, add swipe gesture listeners for drawer.

**Needs research:** No — standard Tailwind responsive patterns; shadcn/ui Sheet component is already installed and documented in the codebase.

### Phase Ordering Rationale

- Phase 1 before Phase 2: `beforeinstallprompt` requires a registered service worker — install UX cannot be tested or built without Phase 1 complete
- Phase 1 before Phase 3: Allows responsive layout testing on an actually-installed PWA in standalone mode — catches navigation issues that only appear without browser chrome
- Phase 3 is independent but last: Responsive layout carries the most visual regression risk (touches the most existing component code); isolating it makes debugging cleaner
- Each phase is independently deployable to production — no phase blocks a release increment
- Pitfalls 1 and 2 (SSE and auth caching) are resolved in Phase 1, preventing them from being introduced by Phase 2 or 3 work

### Research Flags

Phases with standard patterns (no additional research needed):
- **Phase 1:** Official Next.js PWA guide (updated 2026-02-11) + Serwist docs are complete and verified against Next.js 16.2.1. All configuration steps are explicitly documented.
- **Phase 2:** Browser APIs (`beforeinstallprompt`, `navigator.onLine`, `online`/`offline` events) are stable MDN-documented APIs. shadcn/ui Sheet is already installed in the codebase.
- **Phase 3:** Tailwind CSS responsive breakpoints are core framework features. shadcn/ui Sheet/Drawer for mobile navigation is a standard documented pattern.

No phase requires a `/gsd:research-phase` call — research coverage is comprehensive across all three phases.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verified against Next.js official PWA guide (2026-02-11), npm registry (package publish dates confirm March 2026 currency), and Serwist official docs. Package versions confirmed current. next-pwa abandonment confirmed. |
| Features | HIGH | Based on direct Forge codebase analysis (identified specific files: `chat/layout.tsx`, `app-header.tsx`, `next.config.ts`) + competitor PWA audit (ChatGPT, Claude.ai, Open WebUI). Feature boundaries are clear and well-justified for Forge's specific backend dependency. |
| Architecture | HIGH | Implementation patterns verified against Next.js 16 official guide and Serwist docs. 3-phase build order grounded in component dependency analysis. Anti-patterns are Forge-specific (SSE streaming, cross-origin API, standalone Docker). |
| Pitfalls | HIGH | SSE/SW interaction verified in W3C spec issues (#882, #885). Auth/cookie pitfall verified against real-world OHIF case study. Docker/standalone pitfall documented in Next.js standalone output docs. All pitfalls cross-referenced with Forge codebase analysis. |

**Overall confidence: HIGH**

### Gaps to Address

- **`@serwist/turbopack` compatibility with Next.js 16.2.1:** The package is documented for Next.js 15-16 but the dual-config pattern (dev vs. production) may need testing in the actual project environment. Fallback is `next dev --webpack` — functional but slower. Low risk, fast to verify in Phase 1.

- **iOS PWA auth persistence:** Safari's handling of cookies in standalone PWA mode can differ by iOS version. The `SameSite=Lax` fix is the documented solution but should be verified on an actual iOS device (not just Chrome DevTools mobile emulation). Address in Phase 2 testing.

- **Forge icon assets:** Research assumes Forge has logo/branding assets to generate 192x192 and 512x512 PNG icons from. If no source asset exists, icon creation is a prerequisite for Phase 1 completion that falls outside the technical research scope.

- **`next dev --experimental-https` for LAN mobile testing:** The flag exists in Next.js 16 but certificate trust behavior varies by device and OS. LAN testing on iOS requires trusting a self-signed cert. Acceptable workaround: test install flow via Chrome DevTools device emulation + ngrok for real device testing if needed.

## Sources

### Primary (HIGH confidence)
- [Next.js Official PWA Guide](https://nextjs.org/docs/app/guides/progressive-web-apps) — manifest.ts, SW registration, install prompt, security headers, Serwist recommendation (updated 2026-02-11)
- [Next.js manifest.ts API Reference](https://nextjs.org/docs/app/api-reference/file-conventions/metadata/manifest) — built-in manifest file convention
- [Serwist Getting Started with Next.js](https://serwist.pages.dev/docs/next/getting-started) — `@serwist/next` configuration, `sw.ts` patterns, Turbopack support
- [@serwist/next on npm](https://www.npmjs.com/package/@serwist/next) — version 9.5.7, published March 2026
- [serwist on npm](https://www.npmjs.com/package/serwist) — version 9.5.7, published March 2026
- [@serwist/turbopack on npm](https://www.npmjs.com/package/@serwist/turbopack) — version 9.5.6
- [MDN: beforeinstallprompt](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeinstallprompt_event) — install prompt browser API
- [MDN PWA Best Practices](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Best_practices) — PWA standards reference
- [W3C ServiceWorker Issue #885](https://github.com/w3c/ServiceWorker/issues/885) — SSE bypass behavior in service workers
- [W3C ServiceWorker Issue #882](https://github.com/w3c/ServiceWorker/issues/882) — ReadableStream lifetime in SW context
- Forge codebase: `next.config.ts`, `useChat.ts`, `api.ts`, `auth-context.tsx`, `chat/layout.tsx` — direct analysis of SSE, auth, API patterns, and current layout structure

### Secondary (MEDIUM confidence)
- [web.dev: Installation Prompt](https://web.dev/learn/pwa/installation-prompt) — PWA install UX patterns
- [LogRocket: Next.js 16 PWA with offline support](https://blog.logrocket.com/nextjs-16-pwa-offline-support/) — community verification of Serwist integration
- [Aurora Scharff: Next.js 16 + Serwist](https://aurorascharff.no/posts/dynamically-generating-pwa-app-icons-nextjs-16-serwist/) — Next.js 16-specific integration details
- [OHIF/Viewers Issue #1691](https://github.com/OHIF/Viewers/issues/1691) — real-world cached auth data case study
- [Infinity Interactive: Taming PWA Cache Behavior](https://iinteractive.com/resources/blog/taming-pwa-cache-behavior) — SW update lifecycle problems and solutions
- [Microsoft PWA Best Practices](https://learn.microsoft.com/en-us/microsoft-edge/progressive-web-apps/how-to/best-practices) — additional PWA UX patterns

### Tertiary (LOW confidence)
- [Rich Harris: Stuff I wish I'd known about service workers](https://gist.github.com/Rich-Harris/fd6c3c73e6e707e312d7c5d7d0f3b2f9) — practical SW pitfalls; older but core patterns remain valid
- [The Codeship: Service Worker Pitfalls and Best Practices](https://www.thecodeship.com/web-development/guide-service-worker-pitfalls-best-practices/) — general SW pitfall reference

---
*Research completed: 2026-03-22*
*Ready for roadmap: yes*
