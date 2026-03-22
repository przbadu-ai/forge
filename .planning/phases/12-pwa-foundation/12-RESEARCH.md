# Phase 12: PWA Foundation - Research

**Researched:** 2026-03-22
**Domain:** Progressive Web App infrastructure (service worker, manifest, offline fallback)
**Confidence:** HIGH

## Summary

Phase 12 transforms Forge into an installable Progressive Web App by adding a web app manifest, service worker with app shell caching, PWA icons, and an offline fallback page. The stack decision is locked: use `@serwist/next` (webpack plugin) with `serwist` (SW runtime). Next.js 16.2.1 natively supports `app/manifest.ts` for type-safe manifest generation, and the Dockerfile already copies `public/` into the standalone output.

The critical integration concern is SSE streaming. Forge uses Server-Sent Events for chat token streaming, and service workers can intercept and buffer fetch requests. The solution is `NetworkOnly` for all `/api/*` routes, which the `defaultCache` from Serwist does NOT do by default -- it uses `NetworkFirst` for cross-origin requests. We must explicitly add a `NetworkOnly` rule for `/api/*` BEFORE spreading `defaultCache`, since Serwist uses first-match routing.

**Primary recommendation:** Use `@serwist/next` with webpack for production builds. Keep default `next dev` (Turbopack) for daily development (SW not needed in dev). Add `dev:pwa` script using `next dev --webpack` for PWA testing. The offline fallback route should be at `/~offline` (Serwist convention, not a real navigable page).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Use Serwist (`@serwist/next`) for service worker generation -- maintained successor to next-pwa
- StaleWhileRevalidate caching for JS/CSS/fonts -- instant load from cache, background update
- NetworkOnly for all `/api/*` routes -- preserves SSE streaming, no API caching
- Add `dev:pwa` npm script using `--webpack` for PWA testing; keep default `dev` on Turbopack
- Use Next.js `app/manifest.ts` for type-safe dynamic manifest generation
- Theme color matches Forge brand dark theme primary color from Tailwind config
- Generate icons from a single SVG source: 192x192, 512x512, Apple touch icon, favicon
- Display mode: `standalone` -- removes browser chrome for native app feel
- Branded static page with Forge logo, "You're offline" message, and retry button
- Inline CSS for self-contained rendering (no dependency on cached stylesheets)
- Place at `app/offline/page.tsx` and precache in service worker
- Auto-retry on browser `online` event plus manual retry button

### Claude's Discretion
- Exact Serwist configuration options and precache manifest entries
- Specific icon dimensions beyond the required 192/512/Apple touch
- SW registration timing and lifecycle management details

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PWA-01 | App serves a valid web app manifest with name, icons, theme color, display: standalone, and start_url | Next.js `app/manifest.ts` generates `/manifest.webmanifest` automatically. Type-safe via `MetadataRoute.Manifest`. |
| PWA-02 | Service worker registers on app load with Serwist, caches app shell assets, and bypasses /api/* routes (preserving SSE streaming) | `@serwist/next` wraps next.config.ts, generates SW from `app/sw.ts`. Custom `NetworkOnly` rule for `/api/*` placed before `defaultCache` entries. |
| PWA-03 | App provides PWA icons (192x192, 512x512 PNG) and Apple touch icon | `sharp` already available via Next.js. Script or manual generation from source SVG. Icons placed in `public/icons/`. |
| PWA-04 | Offline fallback page displays when user has no network connection | Serwist `fallbacks.entries` config serves precached `/~offline` route when navigation requests fail. |
| PWA-05 | Docker standalone build includes service worker and manifest in output | Dockerfile already copies `public/` directory. SW output to `public/sw.js` is included. Manifest generated at build time by Next.js. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@serwist/next` | 9.5.7 | Webpack plugin for SW generation in Next.js | Maintained successor to next-pwa. Handles precache manifest injection, SW compilation from TypeScript source. |
| `serwist` | 9.5.7 | SW authoring runtime (devDependency) | Core library for writing `sw.ts`. Provides `Serwist` class, caching strategies, precache manifest type. Compiled into SW bundle at build time. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `sharp` | 0.34.5 | PWA icon generation | Already installed via Next.js. Use for one-time icon generation script from SVG source. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `@serwist/next` (webpack) | `@serwist/turbopack` | Turbopack support exists but adds `esbuild` dependency and uses route handler approach. Webpack is proven, production builds use webpack anyway. Turbopack variant can be added later if needed. |
| `app/manifest.ts` (dynamic) | `public/manifest.json` (static) | Dynamic allows theme_color to adapt. Static is simpler but less flexible. Dynamic is the Next.js recommended approach. |

**Installation:**
```bash
cd frontend
npm install @serwist/next@^9.5.7
npm install -D serwist@^9.5.7
```

**Version verification:** Verified 2026-03-22 via `npm view`:
- `@serwist/next`: 9.5.7
- `serwist`: 9.5.7
- `@serwist/turbopack`: 9.5.7 (not installing -- webpack approach chosen)
- `sharp`: 0.34.5 (already installed via Next.js)

## Architecture Patterns

### Recommended Project Structure
```
frontend/
├── src/app/
│   ├── manifest.ts              # Dynamic web app manifest (NEW)
│   ├── sw.ts                    # Service worker source (NEW)
│   ├── ~offline/
│   │   └── page.tsx             # Offline fallback page (NEW)
│   └── layout.tsx               # Add manifest metadata + viewport
├── src/components/
│   └── sw-register.tsx          # SW registration client component (NEW)
├── public/
│   ├── icons/
│   │   ├── icon-192x192.png     # PWA icon (NEW)
│   │   ├── icon-512x512.png     # PWA icon (NEW)
│   │   └── apple-touch-icon.png # Apple touch icon (NEW)
│   ├── sw.js                    # Generated (gitignored)
│   └── swe-worker-*.js          # Generated (gitignored)
├── scripts/
│   └── generate-icons.mjs       # One-time icon generation (NEW)
└── next.config.ts               # Wrapped with withSerwist
```

### Pattern 1: Serwist Webpack Plugin Wrapping next.config.ts
**What:** Wrap the existing Next.js config with `withSerwistInit` to enable SW generation during builds.
**When to use:** Always -- this is the entry point for Serwist integration.
**Example:**
```typescript
// Source: https://serwist.pages.dev/docs/next/getting-started
import { spawnSync } from "node:child_process";
import withSerwistInit from "@serwist/next";
import type { NextConfig } from "next";

const revision =
  spawnSync("git", ["rev-parse", "HEAD"], { encoding: "utf-8" }).stdout?.trim() ??
  crypto.randomUUID();

const withSerwist = withSerwistInit({
  swSrc: "app/sw.ts",
  swDest: "public/sw.js",
  additionalPrecacheEntries: [{ url: "/~offline", revision }],
});

const nextConfig: NextConfig = {
  output: "standalone",
  compress: false, // Required: prevents Next.js from buffering SSE responses
};

export default withSerwist(nextConfig);
```

### Pattern 2: Service Worker with Custom API Bypass
**What:** Custom `sw.ts` that uses `defaultCache` but prepends a `NetworkOnly` rule for `/api/*` to prevent SSE interference.
**When to use:** Always -- SSE streaming is core to Forge.
**Example:**
```typescript
// Source: https://serwist.pages.dev/docs/next/getting-started + custom for Forge
import { defaultCache } from "@serwist/next/worker";
import type { PrecacheEntry, SerwistGlobalConfig } from "serwist";
import { Serwist, NetworkOnly } from "serwist";

declare global {
  interface WorkerGlobalScope extends SerwistGlobalConfig {
    __SW_MANIFEST: (PrecacheEntry | string)[] | undefined;
  }
}

declare const self: ServiceWorkerGlobalScope;

const serwist = new Serwist({
  precacheEntries: self.__SW_MANIFEST,
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  runtimeCaching: [
    // MUST be first: bypass SW for all API routes (SSE streaming)
    {
      urlPattern: /\/api\/.*/,
      handler: new NetworkOnly(),
      method: "GET",
    },
    {
      urlPattern: /\/api\/.*/,
      handler: new NetworkOnly(),
      method: "POST",
    },
    ...defaultCache,
  ],
  fallbacks: {
    entries: [
      {
        url: "/~offline",
        matcher({ request }) {
          return request.destination === "document";
        },
      },
    ],
  },
});

serwist.addEventListeners();
```

### Pattern 3: Dynamic Manifest via app/manifest.ts
**What:** Type-safe manifest generation using Next.js built-in convention.
**When to use:** Always -- generates `/manifest.webmanifest` at build time.
**Example:**
```typescript
// Source: https://nextjs.org/docs/app/api-reference/file-conventions/metadata/manifest
import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Forge",
    short_name: "Forge",
    description: "AI interaction platform",
    start_url: "/",
    display: "standalone",
    background_color: "#0a0a0a",   // dark theme background
    theme_color: "#0a0a0a",        // matches dark mode --background
    icons: [
      {
        src: "/icons/icon-192x192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/icons/icon-512x512.png",
        sizes: "512x512",
        type: "image/png",
      },
      {
        src: "/icons/apple-touch-icon.png",
        sizes: "180x180",
        type: "image/png",
      },
    ],
  };
}
```

### Pattern 4: SW Registration in Client Component
**What:** Register the service worker from a client component placed inside `providers.tsx`.
**When to use:** Always -- SW registration must happen client-side.
**Example:**
```typescript
// Source: https://nextjs.org/docs/app/guides/progressive-web-apps
"use client";

import { useEffect } from "react";

export function ServiceWorkerRegister() {
  useEffect(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js", {
        scope: "/",
        updateViaCache: "none",
      });
    }
  }, []);

  return null;
}
```

### Pattern 5: Offline Fallback Page with Inline Styles
**What:** Self-contained offline page that renders without external CSS.
**When to use:** When user navigates while offline and page is not cached.
**Example:**
```typescript
// app/~offline/page.tsx
export default function OfflinePage() {
  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      minHeight: "100vh",
      backgroundColor: "#0a0a0a",
      color: "#fafafa",
      fontFamily: "system-ui, sans-serif",
      padding: "2rem",
      textAlign: "center",
    }}>
      {/* Forge logo/icon inline SVG */}
      <h1 style={{ fontSize: "1.5rem", marginBottom: "1rem" }}>
        You are offline
      </h1>
      <p style={{ color: "#a1a1a1", marginBottom: "2rem" }}>
        Forge needs a connection to your backend to work.
        Check your network and try again.
      </p>
      <button
        onClick={() => window.location.reload()}
        style={{
          padding: "0.75rem 1.5rem",
          backgroundColor: "#fafafa",
          color: "#0a0a0a",
          border: "none",
          borderRadius: "0.5rem",
          cursor: "pointer",
          fontSize: "1rem",
        }}
      >
        Retry
      </button>
      <script dangerouslySetInnerHTML={{ __html: `
        window.addEventListener("online", () => window.location.reload());
      ` }} />
    </div>
  );
}
```

### Anti-Patterns to Avoid
- **Caching API responses in SW:** Forge requires live backend for LLM calls. Never use `CacheFirst` or `StaleWhileRevalidate` for `/api/*`.
- **SW registration in root layout (server component):** `navigator` is not available server-side. Must use a `"use client"` component.
- **Forgetting to gitignore SW output:** `public/sw.js` and `public/swe-worker-*.js` are generated at build time and must not be committed.
- **Using `app/offline/page.tsx` path:** Serwist convention is `~offline` (tilde prefix). Using a regular path may conflict with app routing expectations.
- **Relying on cached stylesheets for offline page:** If CSS bundles are not yet cached (first visit offline scenario), the offline page must render with inline styles only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Precache manifest | Custom file-listing script | `@serwist/next` webpack plugin | Manifest must match build output hashes exactly. Plugin injects `__SW_MANIFEST` automatically. |
| Cache versioning | Manual cache-busting | Serwist revision-based precaching | Incorrect cache invalidation causes stale content. Serwist handles this with content hashes. |
| SW lifecycle management | Raw `navigator.serviceWorker` API | Serwist `skipWaiting` + `clientsClaim` | Activation race conditions are subtle. Library handles waiting/claiming correctly. |
| Icon generation | Manual Photoshop/Figma export | `sharp` script or online generator | Need exact dimensions, proper PNG optimization. One-time script is sufficient. |
| Manifest file | Static JSON in public/ | `app/manifest.ts` | Next.js generates the link tag automatically and type-checks the manifest shape. |

**Key insight:** Service worker lifecycle management (install, activate, claim, update) has dozens of edge cases. Serwist encapsulates Workbox-proven patterns. Hand-rolling a service worker that correctly handles all browsers, cache versions, and update flows would take weeks.

## Common Pitfalls

### Pitfall 1: SSE Streams Buffered by Service Worker
**What goes wrong:** Service worker intercepts SSE fetch requests and buffers the response, breaking real-time token streaming.
**Why it happens:** Default `StaleWhileRevalidate` or `NetworkFirst` strategies read the full response body before caching/forwarding.
**How to avoid:** Use `NetworkOnly` for ALL `/api/*` routes. Place this rule FIRST in `runtimeCaching` array (Serwist uses first-match).
**Warning signs:** Chat responses appear all-at-once instead of token-by-token after SW registration.

### Pitfall 2: SW Not Included in Docker Standalone Output
**What goes wrong:** `public/sw.js` is generated during build but not copied to standalone output.
**Why it happens:** Next.js standalone output only includes files that exist in `public/` at build time. Since Serwist generates `sw.js` during the build, the Dockerfile must ensure `public/` is copied AFTER build.
**How to avoid:** The existing Dockerfile already has `COPY --from=build /app/public ./public` which runs after `RUN npm run build`. This should work correctly since `sw.js` is written to `public/` during build.
**Warning signs:** `curl http://localhost:3000/sw.js` returns 404 in Docker container.

### Pitfall 3: TypeScript Errors from SW Types
**What goes wrong:** `app/sw.ts` uses `ServiceWorkerGlobalScope` and `WorkerGlobalScope` which conflict with DOM types.
**Why it happens:** tsconfig includes both `"dom"` and `"webworker"` libs, but SW runs in a worker context, not DOM.
**How to avoid:** Add `"@serwist/next/typings"` to tsconfig types. Exclude `"public/sw.js"` from tsconfig. The Serwist typings augment the correct global scope.
**Warning signs:** TypeScript errors about `self` or `ServiceWorkerGlobalScope` not found.

### Pitfall 4: Stale SW Serving Old App Shell
**What goes wrong:** Users see an old version of the app after deployment.
**Why it happens:** Service worker caches app shell aggressively. Browser checks for SW updates on navigation but may take up to 24 hours.
**How to avoid:** Use `skipWaiting: true` and `clientsClaim: true` in Serwist config. This makes new SW take control immediately. Phase 13 (Install UX) will add update notification.
**Warning signs:** Users report seeing old UI after deployment.

### Pitfall 5: Offline Page Not Precached
**What goes wrong:** Offline fallback shows browser error instead of branded page.
**Why it happens:** The `/~offline` route was not added to `additionalPrecacheEntries` in next.config.ts.
**How to avoid:** Ensure `additionalPrecacheEntries: [{ url: "/~offline", revision }]` is set. Use git HEAD as revision for cache-busting.
**Warning signs:** Disconnecting network shows Chrome dinosaur instead of Forge offline page.

### Pitfall 6: next.config.ts Import Syntax
**What goes wrong:** Build fails when importing `withSerwistInit` from `@serwist/next`.
**Why it happens:** Serwist docs show `.mjs` imports. Forge uses `.ts` config which may need different import syntax.
**How to avoid:** Use `import withSerwistInit from "@serwist/next"` in `.ts` file. If ESM/CJS issues arise, check if default export matches.
**Warning signs:** "Cannot find module" or "not a function" errors at build time.

### Pitfall 7: Manifest Not Linked in HTML
**What goes wrong:** Lighthouse PWA audit fails because manifest is not discoverable.
**Why it happens:** Using `app/manifest.ts` should auto-generate the `<link rel="manifest">` tag, but metadata config may need explicit reference.
**How to avoid:** Next.js App Router automatically adds the manifest link when `app/manifest.ts` exists. Verify with `view-source` on the rendered page.
**Warning signs:** Chrome DevTools > Application > Manifest shows "No manifest detected".

## Code Examples

### next.config.ts (Complete)
```typescript
// Source: https://serwist.pages.dev/docs/next/getting-started
import { spawnSync } from "node:child_process";
import withSerwistInit from "@serwist/next";
import type { NextConfig } from "next";

const revision =
  spawnSync("git", ["rev-parse", "HEAD"], { encoding: "utf-8" }).stdout?.trim() ??
  crypto.randomUUID();

const withSerwist = withSerwistInit({
  swSrc: "app/sw.ts",
  swDest: "public/sw.js",
  additionalPrecacheEntries: [{ url: "/~offline", revision }],
});

const nextConfig: NextConfig = {
  output: "standalone",
  compress: false, // Required: prevents Next.js from buffering SSE responses
};

export default withSerwist(nextConfig);
```

### tsconfig.json Changes
```json
{
  "compilerOptions": {
    "types": ["vitest/globals", "@serwist/next/typings"],
    "lib": ["dom", "dom.iterable", "esnext", "webworker"]
  },
  "exclude": ["node_modules", "public/sw.js"]
}
```

### .gitignore Additions
```
# Serwist generated service worker
public/sw*
public/swe-worker*
```

### package.json Script Additions
```json
{
  "scripts": {
    "dev": "next dev --hostname 0.0.0.0",
    "dev:pwa": "next dev --webpack --hostname 0.0.0.0",
    "build": "next build",
    "start": "next start"
  }
}
```

### Security Headers for SW (in next.config.ts headers())
```typescript
// Source: https://nextjs.org/docs/app/guides/progressive-web-apps
async headers() {
  return [
    {
      source: "/sw.js",
      headers: [
        {
          key: "Content-Type",
          value: "application/javascript; charset=utf-8",
        },
        {
          key: "Cache-Control",
          value: "no-cache, no-store, must-revalidate",
        },
        {
          key: "Content-Security-Policy",
          value: "default-src 'self'; script-src 'self'",
        },
      ],
    },
  ];
},
```

### Layout Metadata Update
```typescript
// Source: https://serwist.pages.dev/docs/next/getting-started
import type { Metadata, Viewport } from "next";

export const metadata: Metadata = {
  title: "Forge",
  description: "AI interaction platform",
  applicationName: "Forge",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Forge",
  },
  formatDetection: { telephone: false },
};

export const viewport: Viewport = {
  themeColor: "#0a0a0a",
};
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `next-pwa` | `@serwist/next` | 2024 | next-pwa abandoned, Serwist is maintained fork with App Router support |
| Static `public/manifest.json` | `app/manifest.ts` | Next.js 13.4 | Type-safe, dynamic manifest via file conventions |
| Webpack-only dev server | Turbopack default in Next.js 16 | 2025 | Dev server uses Turbopack; `--webpack` flag needed for SW testing in dev |
| Manual SW registration | Library-managed lifecycle | Ongoing | Serwist handles skipWaiting, clientsClaim, precache versioning |

**Deprecated/outdated:**
- `next-pwa`: Abandoned 2+ years, does not support App Router
- `@ducanh2912/next-pwa`: Fork superseded by Serwist
- Raw `workbox-*` imports: Serwist wraps Workbox with better Next.js integration

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.0 (unit) + Playwright 1.58.2 (E2E) |
| Config file | `frontend/vitest.config.ts` + `frontend/playwright.config.ts` |
| Quick run command | `cd frontend && npm test` |
| Full suite command | `cd frontend && npm test && npx playwright test` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PWA-01 | Manifest served with correct fields | E2E | `npx playwright test tests/pwa.spec.ts --grep "manifest"` | No -- Wave 0 |
| PWA-02 | SW registers and caches app shell; /api/* bypassed | E2E | `npx playwright test tests/pwa.spec.ts --grep "service worker"` | No -- Wave 0 |
| PWA-03 | PWA icons exist at correct paths | unit | `npm test -- --grep "pwa-icons"` | No -- Wave 0 |
| PWA-04 | Offline fallback page renders | E2E | `npx playwright test tests/pwa.spec.ts --grep "offline"` | No -- Wave 0 |
| PWA-05 | Docker build includes SW and manifest | manual-only | `docker compose up --build && curl localhost:3000/sw.js` | N/A |

### Sampling Rate
- **Per task commit:** `cd frontend && npm test`
- **Per wave merge:** `cd frontend && npm test && npx playwright test`
- **Phase gate:** Full suite green + manual Lighthouse PWA audit

### Wave 0 Gaps
- [ ] `frontend/tests/pwa.spec.ts` -- Playwright E2E tests for manifest, SW registration, offline fallback
- [ ] `frontend/src/__tests__/pwa-icons.test.ts` -- Unit test verifying icon files exist at expected paths
- [ ] Playwright needs `--service-workers=allow` context option for SW testing

## Open Questions

1. **`defaultCache` exact contents**
   - What we know: `defaultCache` from `@serwist/next/worker` provides standard caching strategies for Next.js assets (JS, CSS, images, fonts). It likely uses `StaleWhileRevalidate` or `CacheFirst` for static assets.
   - What's unclear: Exact list of URL patterns and strategies in `defaultCache`. May include a `NetworkFirst` for cross-origin that could interfere with API routes if backend is on a different origin.
   - Recommendation: After installing Serwist, inspect `node_modules/@serwist/next/worker` to see exact `defaultCache` entries. Ensure custom `/api/*` NetworkOnly rule is placed BEFORE the spread.

2. **`swSrc` path resolution**
   - What we know: Serwist docs show `swSrc: "app/sw.ts"`. Forge uses `src/app/` directory structure (with `@/*` alias mapped to `./src/*`).
   - What's unclear: Whether `swSrc` resolves relative to project root or `src/`. Need to test `"src/app/sw.ts"` vs `"app/sw.ts"`.
   - Recommendation: Try `"src/app/sw.ts"` first since that matches the actual file location. Fall back to `"app/sw.ts"` if it fails.

3. **Forge branding asset for icons**
   - What we know: No existing Forge logo/icon SVG found in `public/`. Only default Next.js SVGs exist.
   - What's unclear: Whether a brand asset needs to be created or a simple geometric icon is sufficient.
   - Recommendation: Create a simple, recognizable Forge icon (anvil/hammer motif or letter "F"). Can be refined later. The important thing is having correct dimensions for PWA requirements.

## Sources

### Primary (HIGH confidence)
- [Next.js PWA Guide](https://nextjs.org/docs/app/guides/progressive-web-apps) -- Official guide, updated 2026-02-11
- [Next.js manifest.ts API Reference](https://nextjs.org/docs/app/api-reference/file-conventions/metadata/manifest) -- Built-in manifest support
- [Serwist Getting Started (webpack)](https://serwist.pages.dev/docs/next/getting-started) -- Official Serwist docs, verified working with Next.js App Router
- npm registry: `@serwist/next@9.5.7`, `serwist@9.5.7`, `@serwist/turbopack@9.5.7` -- versions verified 2026-03-22
- Next.js 16.2.1 CLI: `next build --webpack` and `next dev --webpack` flags verified locally

### Secondary (MEDIUM confidence)
- [Serwist NetworkOnly strategy](https://serwist.pages.dev/docs/serwist/runtime-caching/caching-strategies/network-only) -- API route bypass pattern
- [Serwist routing (first-match)](https://serwist.pages.dev/docs/serwist/runtime-caching/routing) -- Route registration order matters
- [Serwist GitHub Issue #187](https://github.com/serwist/serwist/issues/187) -- Removing runtime caching for specific endpoints

### Tertiary (LOW confidence)
- `defaultCache` exact contents -- not inspected directly, inferred from docs and community discussions. Needs verification after install.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- versions verified on npm, Serwist docs match Next.js App Router setup
- Architecture: HIGH -- patterns sourced from official Serwist docs and Next.js PWA guide
- Pitfalls: HIGH -- SSE/SW interference is well-documented; Docker standalone output pattern verified in existing Dockerfile
- Validation: MEDIUM -- Playwright SW testing requires specific configuration not yet verified

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (stable -- Serwist 9.x is mature, Next.js 16.x PWA support is documented)
