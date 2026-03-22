# Stack Research: PWA Capabilities for Forge v2.1

**Domain:** Progressive Web App features for existing Next.js 16 App Router application
**Researched:** 2026-03-22
**Confidence:** HIGH (verified against Next.js official docs, npm registry, Serwist docs)

## Scope

This research covers ONLY the stack additions needed for PWA capabilities. The existing stack (Next.js 16.2.1, React 19.2.4, Tailwind CSS v4, shadcn/ui, FastAPI backend) is validated and locked from v1.0.

---

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

These PWA features use NO additional libraries:

| Feature | Implementation | Why No Library |
|---------|---------------|----------------|
| Responsive layout | Tailwind CSS v4 breakpoints (`sm:`, `md:`, `lg:`) | Already installed. Responsive design is CSS-only work on existing components. |
| Install prompt | Browser `beforeinstallprompt` API + `useState`/`useEffect` | ~40 lines of client component code. No library needed. |
| iOS install instructions | `navigator.userAgent` detection + UI component | Chromium fires `beforeinstallprompt`; iOS requires manual "Add to Home Screen" instructions. |
| Offline detection | `navigator.onLine` + `online`/`offline` events | Native browser API. Show banner when backend unreachable. |
| Standalone mode detection | `window.matchMedia('(display-mode: standalone)')` | Native CSS media query. Hide install prompt when already installed. |

---

## Installation

```bash
cd frontend

# Core PWA: service worker management
npm install @serwist/next

# Dev: SW compilation (compiles sw.ts -> public/sw.js)
npm install -D serwist

# Turbopack support for dev server
npm install @serwist/turbopack
```

**Total new packages: 3.** Minimal footprint, focused scope.

---

## Integration Points with Existing Stack

### 1. next.config.ts Modification

Current config:
```typescript
const nextConfig: NextConfig = {
  output: "standalone",
  compress: false,  // Required: prevents Next.js from buffering SSE responses
};
```

Updated config with Serwist:
```typescript
import withSerwistInit from "@serwist/next";

const withSerwist = withSerwistInit({
  swSrc: "app/sw.ts",
  swDest: "public/sw.js",
});

export default withSerwist({
  output: "standalone",
  compress: false, // MUST preserve: SSE streaming requires unbuffered responses
});
```

**Critical:** `output: "standalone"` and `compress: false` MUST be preserved. Serwist's wrapper does not interfere with these settings.

For Turbopack dev mode, the `@serwist/turbopack` package provides an alternative `withSerwist` import that works with Turbopack's bundling. See Serwist docs for the dual-config pattern.

### 2. Web App Manifest (app/manifest.ts)

No library needed. Next.js 16 natively supports this file convention:

```typescript
import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Forge",
    short_name: "Forge",
    description: "Local-first AI assistant",
    start_url: "/",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#0a0a0a",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
      { src: "/icons/icon-maskable.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
```

### 3. Service Worker (app/sw.ts)

Serwist compiles `app/sw.ts` into `public/sw.js` at build time. The service worker handles:

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

**Key architectural decision:** Forge is NOT an offline-first app. It requires a running backend for all meaningful functionality (LLM calls, chat, RAG). The service worker's job is to: (1) make the app shell load instantly, (2) show a graceful offline page when backend is unreachable. Do NOT attempt offline data sync or cached chat.

### 5. Responsive Layout

No new dependencies. Use existing Tailwind CSS v4 breakpoints on existing components:

- `sm:` (640px) -- mobile landscape
- `md:` (768px) -- tablet, sidebar collapse point
- `lg:` (1024px) -- desktop, full sidebar

This is CSS-only work: adding responsive classes to the existing sidebar, chat area, and settings layouts.

### 6. Install Prompt

Pure browser API. Two paths:

- **Chromium (Chrome, Edge, etc.):** Capture `beforeinstallprompt` event, show custom install button
- **Safari/iOS:** Detect iOS via user agent, show manual "Add to Home Screen" instructions

Note: Next.js official docs say they "do not recommend" custom `beforeinstallprompt` buttons because they are not cross-browser. However, for Forge (a developer tool primarily used on desktop Chrome), a custom install button provides good UX. Include iOS fallback instructions for completeness.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `@serwist/next` for service worker | Hand-written `public/sw.js` (no build tool) | Only for trivial SWs (push notifications only, no precaching). Next.js official guide shows this simpler approach but it lacks precaching, versioning, and cache management. |
| `@serwist/turbopack` for dev | `next dev --webpack` flag | If `@serwist/turbopack` has compatibility issues with Next.js 16.2.1. Webpack fallback always works but dev server is slower. |
| Tailwind breakpoints for responsive | CSS Container Queries | If individual components need to respond to container size rather than viewport. Tailwind v4 supports `@container` but viewport breakpoints should cover Forge's layout needs. |
| Dynamic `app/manifest.ts` | Static `public/manifest.json` | If you never need dynamic manifest values. Dynamic is better because it can adapt `theme_color` to match light/dark theme. |

---

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

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `@serwist/next@^9.5` | Next.js 14-16, App Router | Production builds use webpack (standard for Next.js). Verified working with App Router. |
| `@serwist/turbopack@^9.5` | Next.js 15-16 | Dev server only. Production builds still use webpack via `@serwist/next`. |
| `serwist@^9.5` | `@serwist/next@^9.5` | Must match major+minor version with `@serwist/next`. Always install same version. |
| `manifest.ts` (built-in) | Next.js 13.4+ (App Router) | Part of Next.js metadata file conventions. No version concern with 16.2.1. |

---

## Development Workflow Impact

### Turbopack + Service Worker

Next.js 16 defaults to Turbopack for `next dev`. Two paths for SW development:

1. **`@serwist/turbopack`** (recommended): Import `withSerwist` from `@serwist/turbopack` for dev config. SW is generated during Turbopack dev builds.
2. **`next dev --webpack`**: Falls back to webpack. Slower dev server but guaranteed Serwist compatibility. Good fallback if Turbopack integration has issues.

Production builds (`next build`) always use webpack, so `@serwist/next` always works for production.

### .gitignore Additions

```
# Serwist generated service worker
public/sw.js
public/sw.js.map
public/swe-worker-*.js
```

### Testing PWA Features

- **Localhost is secure:** Service workers work on `localhost` without HTTPS.
- **LAN testing:** Use `next dev --experimental-https` for testing on mobile devices over local network.
- **Playwright:** Test SW registration via `page.evaluate(() => navigator.serviceWorker.ready)`.
- **Manifest validation:** Chrome DevTools > Application > Manifest panel.
- **Lighthouse:** Run PWA audit to verify installability criteria.

### Security Headers

Add to `next.config.ts` headers for the service worker:

```typescript
async headers() {
  return [{
    source: "/sw.js",
    headers: [
      { key: "Content-Type", value: "application/javascript; charset=utf-8" },
      { key: "Cache-Control", value: "no-cache, no-store, must-revalidate" },
      { key: "Content-Security-Policy", value: "default-src 'self'; script-src 'self'" },
    ],
  }];
}
```

SW must never be cached by the browser -- `no-cache, no-store, must-revalidate` ensures the browser always checks for updates.

---

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

---
*Stack research for: Forge v2.1 PWA milestone*
*Researched: 2026-03-22*
