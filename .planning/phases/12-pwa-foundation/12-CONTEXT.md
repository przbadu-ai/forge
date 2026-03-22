# Phase 12: PWA Foundation - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase makes Forge a valid, installable Progressive Web App. Delivers: web app manifest, service worker with app shell caching, PWA icons, offline fallback page, and Docker build support for SW assets. No visual layout changes — purely PWA infrastructure + offline page.

</domain>

<decisions>
## Implementation Decisions

### Service Worker Strategy
- Use Serwist (`@serwist/next`) for service worker generation — maintained successor to next-pwa, handles precaching and runtime caching
- StaleWhileRevalidate caching for JS/CSS/fonts — instant load from cache, background update
- NetworkOnly for all `/api/*` routes — preserves SSE streaming, no API caching
- Add `dev:pwa` npm script using `--webpack` for PWA testing; keep default `dev` on Turbopack

### Manifest & Icons
- Use Next.js `app/manifest.ts` for type-safe dynamic manifest generation
- Theme color matches Forge brand dark theme primary color from Tailwind config
- Generate icons from a single SVG source: 192x192, 512x512, Apple touch icon, favicon
- Display mode: `standalone` — removes browser chrome for native app feel

### Offline Fallback Page
- Branded static page with Forge logo, "You're offline" message, and retry button
- Inline CSS for self-contained rendering (no dependency on cached stylesheets)
- Place at `app/offline/page.tsx` and precache in service worker
- Auto-retry on browser `online` event plus manual retry button

### Claude's Discretion
- Exact Serwist configuration options and precache manifest entries
- Specific icon dimensions beyond the required 192/512/Apple touch
- SW registration timing and lifecycle management details

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `next.config.ts` — already has `output: "standalone"` and `compress: false` (SSE-friendly)
- `src/components/providers.tsx` — ThemeProvider + QueryClient + AuthProvider wrapper (SW registration component goes here)
- `src/app/layout.tsx` — root layout with metadata (manifest link goes in metadata)
- Tailwind CSS v4 config — brand colors available for manifest theme_color

### Established Patterns
- Client components use `"use client"` directive
- Provider pattern wraps app in `providers.tsx`
- Protected routes via `(protected)/layout.tsx` with auth guard
- Metadata defined in layout.tsx

### Integration Points
- `next.config.ts` — Serwist plugin wraps the config
- `src/app/layout.tsx` — manifest metadata link
- `src/components/providers.tsx` — SW registration client component
- `frontend/Dockerfile` — verify `public/` assets in standalone output
- `public/` directory — icons and generated SW output

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. Research recommends Serwist as the canonical solution for Next.js 16 PWA.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
