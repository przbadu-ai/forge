# Architecture Research: PWA Integration with Forge

**Domain:** Progressive Web App integration into existing Next.js 16 App Router application
**Researched:** 2026-03-22
**Confidence:** HIGH

## System Overview

```
                         EXISTING                              NEW (PWA)
                         --------                              ---------

Root Layout (app/layout.tsx)
  |-- <html> + <body>
  |-- Providers (theme, query, auth)           + viewport export
  |                                            + manifest.ts (linked via metadata)
  |
  +-- /login (public)
  |
  +-- (protected)/layout.tsx                   (no changes needed)
  |     |-- AppHeader                          ~ responsive: hamburger on mobile
  |     |-- <main>
  |     |
  |     +-- /chat/layout.tsx
  |     |     |-- <aside> w-64 sidebar         ~ responsive: drawer on mobile
  |     |     |-- <main> chat area             ~ full-width on mobile
  |     |     +-- /chat/[id]/page.tsx
  |     |
  |     +-- /settings/layout.tsx               ~ responsive: stack on mobile
  |           +-- /settings/page.tsx
  |
  +-- /~offline/page.tsx                       + NEW: offline fallback page
  |
  +-- manifest.ts                              + NEW: web app manifest
  |
  +-- sw.ts                                    + NEW: service worker source

public/
  |-- icon-192x192.png                         + NEW: PWA icons
  |-- icon-512x512.png                         + NEW: PWA icons
  |-- sw.js                                    + NEW: generated (gitignored)
  |-- swe-worker-*.js                          + NEW: generated (gitignored)

next.config.ts                                 ~ wrap with withSerwist
tsconfig.json                                  ~ add webworker lib + serwist types
```

## Integration Points with Existing Architecture

### 1. next.config.ts -- Serwist Wrapper

**Current state:** Minimal config with `output: "standalone"` and `compress: false`.

**Change:** Wrap with `withSerwist` from `@serwist/next`. The `output: "standalone"` and `compress: false` settings are preserved inside the wrapped config.

```typescript
import withSerwistInit from "@serwist/next";

const withSerwist = withSerwistInit({
  swSrc: "src/app/sw.ts",
  swDest: "public/sw.js",
  additionalPrecacheEntries: [{ url: "/~offline", revision: "initial" }],
});

export default withSerwist({
  output: "standalone",
  compress: false,
});
```

**Risk:** LOW. Serwist wraps the config non-destructively. The `compress: false` for SSE streaming is preserved.

### 2. app/layout.tsx -- Metadata + Viewport

**Current state:** Exports `metadata` with title/description. No viewport export.

**Change:** Add `viewport` export for `themeColor`. Add `applicationName` and `appleWebApp` to metadata. Next.js automatically links the manifest when `app/manifest.ts` exists.

```typescript
export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0a0a" },
  ],
};

export const metadata: Metadata = {
  title: "Forge",
  description: "AI interaction platform",
  applicationName: "Forge",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Forge",
  },
};
```

**Risk:** LOW. Additive metadata changes only.

### 3. tsconfig.json -- Type Additions

**Current state:** `lib: ["dom", "dom.iterable", "esnext"]`, `types: ["vitest/globals"]`.

**Change:** Add `"webworker"` to `lib`, add `"@serwist/next/typings"` to `types`, add `"public/sw.js"` to `exclude`.

**Risk:** LOW. The `webworker` lib adds ServiceWorker types to global scope. No conflicts with existing DOM types.

### 4. Service Worker (sw.ts) -- NEW File

**Location:** `src/app/sw.ts` (compiled to `public/sw.js` by Serwist).

**Caching strategy for Forge:**

| Resource Type | Strategy | Rationale |
|---------------|----------|-----------|
| App shell (HTML, JS, CSS) | Precache + stale-while-revalidate | Instant load, background update |
| Static assets (icons, fonts) | Cache-first, 30-day expiry | Rarely change |
| API calls to FastAPI (`/api/*`) | Network-only | Chat data must be fresh; SSE cannot be cached |
| Login page | Network-only | Auth must hit server |
| Offline fallback | Precached | Shown when network unavailable |

**Critical:** SSE streaming (`/api/v1/chat/stream`) must NOT be intercepted by the service worker. The `defaultCache` from `@serwist/next/worker` handles Next.js assets correctly. Custom rules are needed only to exclude the FastAPI proxy routes.

```typescript
import { defaultCache } from "@serwist/next/worker";
import type { PrecacheEntry, SerwistGlobalConfig } from "serwist";
import { Serwist } from "serwist";

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
    // API routes must never be cached -- SSE streaming, auth, fresh data
    {
      urlPattern: /\/api\/.*/,
      handler: "NetworkOnly",
    },
    ...defaultCache,
  ],
  fallbacks: {
    entries: [{
      url: "/~offline",
      matcher: ({ request }) => request.destination === "document",
    }],
  },
});

serwist.addEventListeners();
```

### 5. Web App Manifest (manifest.ts) -- NEW File

**Location:** `src/app/manifest.ts` (dynamic, TypeScript).

Use dynamic manifest (not static JSON) because Forge supports light/dark themes and the manifest can adapt `theme_color` based on deployment context. Next.js has built-in support for `app/manifest.ts` -- it auto-generates the `<link rel="manifest">` tag.

```typescript
import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Forge",
    short_name: "Forge",
    description: "Local-first AI assistant",
    start_url: "/chat",
    display: "standalone",
    background_color: "#0a0a0a",
    theme_color: "#0a0a0a",
    icons: [
      { src: "/icon-192x192.png", sizes: "192x192", type: "image/png" },
      { src: "/icon-512x512.png", sizes: "512x512", type: "image/png" },
      { src: "/icon-512x512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
```

**Note:** `start_url: "/chat"` because the root `/` just redirects to `/chat` anyway.

### 6. Offline Fallback Page -- NEW File

**Location:** `src/app/~offline/page.tsx`

Simple static page shown when user navigates while offline. Should match Forge's visual style (dark background, centered content). Does NOT need to be a "use client" component -- can be a plain server component for minimal bundle size. The `~offline` path convention is used by Serwist.

### 7. Responsive Layout Modifications -- EXISTING Files

These are the files that need responsive breakpoints added:

#### 7a. Chat Layout (sidebar to drawer)

**File:** `src/app/(protected)/chat/layout.tsx`
**Current:** Fixed `w-64` sidebar always visible. No responsive classes at all.
**Change:** Hide sidebar on mobile, show as overlay/drawer triggered by a menu button.

```
Desktop (md+):  [sidebar w-64] [chat area flex-1]
Mobile (<md):   [chat area full-width] + [drawer overlay triggered by button]
```

**Implementation approach:** Use a `useSidebar` context/hook to manage open/close state. On `md+` breakpoints, sidebar is always visible via CSS (`hidden md:block`). Below `md`, it renders inside a shadcn Sheet component (which uses the Vaul drawer under the hood). The ConversationList component is shared between both views -- just wrapped differently.

#### 7b. App Header (responsive nav)

**File:** `src/components/layout/app-header.tsx`
**Current:** Horizontal nav with icon+label links, always visible. Fixed height `h-12`.
**Change:** On mobile, collapse nav labels behind icons only, or use a hamburger menu. Add the sidebar toggle button (for chat drawer) on mobile.

**Recommendation:** Keep the top header on mobile but simplify: show "Forge" + hamburger (for sidebar) on left, icon-only nav in center, logout icon on right. The hamburger only appears on chat pages (where sidebar exists).

#### 7c. Settings Layout

**File:** `src/app/(protected)/settings/layout.tsx`
**Current:** `max-w-4xl mx-auto px-4 py-8`.
**Change:** Reduce padding on mobile (`px-2 py-4 md:px-4 md:py-8`). Already reasonably responsive since it uses `w-full max-w-4xl`.

#### 7d. Message Bubbles

**File:** `src/components/chat/MessageBubble.tsx`
**Current:** `max-w-[80%]` on messages.
**Change:** Increase to `max-w-[95%] md:max-w-[80%]` on mobile for better space usage.

### 8. Install Prompt UX -- NEW Component

**Location:** `src/components/pwa/InstallPrompt.tsx`

A "use client" component that:
1. Listens for `beforeinstallprompt` event (Chrome/Edge)
2. Detects iOS and shows manual install instructions
3. Detects standalone mode (`display-mode: standalone` media query) and hides prompt if already installed
4. Renders as a dismissible banner in the app header or as a toast notification

### 9. Service Worker Registration -- NEW Component

**Location:** `src/components/pwa/ServiceWorkerRegistration.tsx`

A "use client" component mounted in `providers.tsx` that:
1. Registers `/sw.js` on mount (checks `"serviceWorker" in navigator` first)
2. Handles update notifications (new version available)
3. No visual UI normally -- only shows a toast/banner when an update is available

### 10. Docker Build -- EXISTING File

**File:** `frontend/Dockerfile`
**Current:** Copies `public/` directory in the runner stage.
**Change:** The generated `public/sw.js` is created during `npm run build` (Stage 2), so it is already included in `COPY --from=build /app/public ./public`. No Dockerfile changes needed.

## Component Responsibilities

| Component | Type | Responsibility |
|-----------|------|----------------|
| `manifest.ts` | New file | PWA metadata, icons, display mode |
| `sw.ts` | New file | Service worker source with caching strategies |
| `~offline/page.tsx` | New page | Offline fallback page |
| `InstallPrompt.tsx` | New component | Install UX for desktop/mobile |
| `ServiceWorkerRegistration.tsx` | New component | SW registration + update notifications |
| `useSidebar` hook | New hook | Sidebar open/close state management |
| `chat/layout.tsx` | Modified | Responsive sidebar/drawer |
| `app-header.tsx` | Modified | Responsive nav (hamburger + sidebar toggle) |
| `settings/layout.tsx` | Modified | Mobile padding adjustments |
| `MessageBubble.tsx` | Modified | Mobile-friendly max-width |
| `layout.tsx` (root) | Modified | Viewport + manifest metadata |
| `next.config.ts` | Modified | Serwist wrapper |
| `tsconfig.json` | Modified | WebWorker types |
| `.gitignore` | Modified | Exclude generated SW files |
| `package.json` | Modified | Add dev:pwa script |

## Data Flow

### Service Worker Lifecycle

```
Build time:
  Serwist plugin --> reads sw.ts --> generates public/sw.js with precache manifest

Runtime (browser):
  Page load --> ServiceWorkerRegistration component --> navigator.serviceWorker.register("/sw.js")
       |
       v
  SW activates --> precaches app shell (HTML, JS, CSS bundles)
       |
       v
  Navigation request --> SW intercepts
       |
       +-- /api/* request? --> NetworkOnly (pass through, never cache)
       +-- Cached asset? --> serve from cache (stale-while-revalidate)
       +-- Offline + document? --> serve /~offline fallback
       +-- Offline + non-document? --> network error (standard behavior)
```

### Install Prompt Flow

```
Browser detects valid manifest + registered service worker
       |
       v
  Chrome/Edge: fires "beforeinstallprompt" event
       |                           |
       v                           v
  InstallPrompt component    iOS: detect via userAgent
  captures event, shows         show manual instructions
  "Install Forge" button          (Share > Add to Home Screen)
       |
       v
  User clicks --> event.prompt() --> browser install dialog
       |
       v
  On install: "appinstalled" event --> hide install prompt
```

### Responsive Layout State

```
Window resize / initial load
       |
       v
  CSS breakpoint (md: 768px)
       |
       +-- >= 768px: sidebar always visible (CSS only, no JS state)
       +-- < 768px: sidebar hidden by CSS
                     hamburger button in AppHeader toggles useSidebar state
                     Sheet/Drawer overlay renders ConversationList
                     backdrop click or navigation closes drawer
```

## Architectural Patterns

### Pattern 1: Serwist Build-Time Integration

**What:** Serwist processes `sw.ts` at build time, injecting a precache manifest of all Next.js build artifacts. The service worker file lives in `src/app/sw.ts` but compiles to `public/sw.js`.

**When to use:** Always -- this is the standard approach for Next.js PWA with Serwist.

**Trade-offs:**
- Pro: Automatic precache manifest generation, type-safe service worker
- Pro: Works with Next.js standalone output mode
- Con: Requires `--webpack` flag for local dev testing (`next dev --webpack`)
- Con: Generated `sw.js` must be gitignored

### Pattern 2: Network-Only for API Routes

**What:** Explicitly exclude all `/api/*` routes from service worker caching. Forge proxies requests to FastAPI backend -- these must always hit the network.

**When to use:** Any PWA with a separate API backend or SSE streaming.

**Trade-offs:**
- Pro: Prevents stale API responses, SSE streaming works correctly
- Pro: Auth tokens always validated server-side
- Con: API calls fail immediately when offline (desired behavior -- show offline UI instead)

### Pattern 3: CSS-First Responsive with JS Drawer Fallback

**What:** Use Tailwind breakpoints (`hidden md:block`, `md:hidden`) for layout shifts. Only use JavaScript state (`useSidebar` hook) for the mobile drawer open/close toggle.

**When to use:** When the responsive change is primarily layout (show/hide sidebar) with a small interactive component (drawer toggle).

**Trade-offs:**
- Pro: No layout shift on desktop, no unnecessary JS hydration
- Pro: SSR renders correctly for any viewport -- no hydration mismatch
- Con: Mobile drawer needs client-side state management (but this is minimal)

### Pattern 4: Dynamic Manifest over Static JSON

**What:** Use `app/manifest.ts` (TypeScript function) instead of `public/manifest.json`. Next.js auto-generates `<link rel="manifest">` and serves at `/manifest.webmanifest`.

**When to use:** Always in Next.js App Router projects. Especially when you need type safety or environment-variable-driven values.

**Trade-offs:**
- Pro: TypeScript types prevent manifest errors
- Pro: Can access env vars for per-environment customization
- Pro: Next.js handles linking automatically
- Con: None -- strictly superior to static JSON in App Router

## Anti-Patterns

### Anti-Pattern 1: Caching SSE/Streaming Responses

**What people do:** Use a broad `CacheFirst` or `StaleWhileRevalidate` strategy that accidentally matches `/api/v1/chat/stream`.
**Why it's wrong:** SSE responses are long-lived streams. Caching them breaks streaming entirely -- the service worker tries to serve a partial/stale response. This is especially dangerous because Forge's core value is streaming chat.
**Do this instead:** Put a `NetworkOnly` rule for `/api/*` BEFORE the default cache rules so it matches first. Order matters in Serwist's `runtimeCaching` array.

### Anti-Pattern 2: Using next-pwa Instead of Serwist

**What people do:** Install `next-pwa` because it appears in older tutorials.
**Why it's wrong:** `next-pwa` is abandoned (last release 2022), requires webpack, does not work with Turbopack (Next.js 16 default). It has known security vulnerabilities.
**Do this instead:** Use `@serwist/next` + `serwist`. It is the maintained successor with Turbopack awareness.

### Anti-Pattern 3: Putting manifest.json in public/

**What people do:** Create a static `public/manifest.json` file.
**Why it's wrong:** Misses Next.js's built-in manifest support. A static file cannot use TypeScript types. Next.js does not automatically add `<link rel="manifest">` for files in public/.
**Do this instead:** Create `app/manifest.ts` exporting a function. Next.js handles everything automatically.

### Anti-Pattern 4: JavaScript-Driven Responsive Layout

**What people do:** Use `window.innerWidth` checks and state to conditionally render sidebar vs drawer.
**Why it's wrong:** Causes hydration mismatches (server renders one layout, client renders another). Layout shift on initial load. React strict mode will flag it.
**Do this instead:** Use CSS breakpoints for show/hide. Only use JS for interactive state (drawer open/close toggle). Both the desktop sidebar and mobile drawer can render in the DOM simultaneously -- CSS controls visibility.

### Anti-Pattern 5: Registering Service Worker in Root Layout

**What people do:** Add `navigator.serviceWorker.register()` directly in root `layout.tsx` or in a `<script>` tag.
**Why it's wrong:** Root layout is a server component. Client-side APIs are not available. Even if wrapped in "use client", mixing SW registration with layout logic couples concerns.
**Do this instead:** Create a dedicated `ServiceWorkerRegistration` component, mount it inside `providers.tsx`. Keeps SW lifecycle management isolated and testable.

## Turbopack Compatibility

**Critical detail for development workflow:**

Serwist does NOT generate the service worker during `next dev` with Turbopack (the Next.js 16 default). This means:

- Normal `next dev` works fine for all non-PWA development -- no service worker, standard dev experience
- To test PWA features locally: `next dev --webpack --experimental-https`
- Production builds (`next build`) always work correctly regardless of dev bundler
- Add `SERWIST_SUPPRESS_TURBOPACK_WARNING=1` to `.env` to silence the dev warning

**Recommendation:** Add two npm scripts:
```json
{
  "dev": "next dev --hostname 0.0.0.0",
  "dev:pwa": "next dev --hostname 0.0.0.0 --webpack --experimental-https"
}
```

Most development uses the fast Turbopack dev server. Switch to `dev:pwa` only when actively testing service worker or install prompt behavior.

## Suggested Build Order

Based on dependency analysis between new/modified components:

```
Phase 1: PWA Foundation (no visual changes, no user-facing behavior change)
  1. Install @serwist/next + serwist
  2. Modify next.config.ts (Serwist wrapper)
  3. Modify tsconfig.json (webworker types)
  4. Update .gitignore (public/sw*)
  5. Create sw.ts with caching strategies (NetworkOnly for /api/*)
  6. Create manifest.ts (dynamic, TypeScript)
  7. Update root layout.tsx metadata/viewport exports
  8. Generate and add PWA icons to public/ (192x192, 512x512)
  9. Create /~offline page (simple, matches Forge visual style)
  10. Add dev:pwa script to package.json
      --> TEST: production build succeeds, manifest served at /manifest.webmanifest,
               SW registers in browser, Lighthouse PWA audit passes

Phase 2: Install UX (small new components)
  11. Create ServiceWorkerRegistration component
  12. Mount in providers.tsx
  13. Create InstallPrompt component (beforeinstallprompt + iOS detection)
  14. Integrate install prompt into app (banner or toast)
      --> TEST: install prompt appears in Chrome, SW registers, offline
               fallback works, SSE streaming still works with SW active

Phase 3: Responsive Layout (modify existing components)
  15. Create useSidebar hook/context
  16. Modify chat/layout.tsx (sidebar hidden on mobile, Sheet drawer)
  17. Modify app-header.tsx (hamburger toggle on mobile, responsive nav)
  18. Adjust settings/layout.tsx for mobile padding
  19. Adjust MessageBubble.tsx max-width for mobile
  20. Touch interactions: swipe-to-close on drawer, tap targets >= 44px
      --> TEST: all pages usable at 375px width, sidebar drawer toggles,
               no horizontal scroll, touch targets accessible
```

**Rationale for this order:**
- Phase 1 has zero visual impact on existing users -- safe to ship incrementally
- Phase 2 depends on Phase 1 (SW must exist before registration component works)
- Phase 3 is independent of Phases 1-2 (responsive layout does not require SW) but benefits from testing on an installed PWA to verify standalone display mode
- Each phase is independently testable and deployable
- Phase 1 is the riskiest (config changes to next.config.ts, build pipeline) -- do it first to surface issues early

## New File Structure Summary

```
frontend/
  src/
    app/
      manifest.ts                          # NEW - PWA manifest
      sw.ts                                # NEW - service worker source
      ~offline/
        page.tsx                           # NEW - offline fallback
    components/
      pwa/
        InstallPrompt.tsx                  # NEW - install prompt UX
        ServiceWorkerRegistration.tsx       # NEW - SW lifecycle
    hooks/
      useSidebar.ts                        # NEW - sidebar state
  public/
    icon-192x192.png                       # NEW - PWA icon
    icon-512x512.png                       # NEW - PWA icon
    apple-touch-icon.png                   # NEW - iOS icon
```

## Sources

- [Next.js PWA Guide (official, v16.2.1)](https://nextjs.org/docs/app/guides/progressive-web-apps) -- PRIMARY, HIGH confidence
- [Serwist Getting Started (@serwist/next)](https://serwist.pages.dev/docs/next/getting-started) -- PRIMARY, HIGH confidence
- [Serwist Turbopack support discussion](https://github.com/serwist/serwist/issues/54) -- Turbopack compatibility details
- [Next.js 16 + Serwist (Aurora Scharff)](https://aurorascharff.no/posts/dynamically-generating-pwa-app-icons-nextjs-16-serwist/) -- Next.js 16 specific integration, MEDIUM confidence
- [@serwist/turbopack npm package](https://www.npmjs.com/package/@serwist/turbopack) -- Alternative Turbopack integration path
- [shadcn/ui Drawer (Vaul)](https://www.shadcn.io/ui/drawer) -- Mobile drawer component reference

---
*Architecture research for: PWA integration with Forge (Next.js 16 App Router)*
*Researched: 2026-03-22*
