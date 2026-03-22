# Feature Research

**Domain:** PWA capabilities for AI chat application (Forge)
**Researched:** 2026-03-22
**Confidence:** HIGH

## Context

This research covers NEW PWA features for the v2.1 milestone. Forge already has a complete v1.0 with streaming chat, execution traces, MCP, settings, file upload, themes, and JWT auth. The existing UI is desktop-focused with a fixed-width sidebar and no mobile responsiveness. This document focuses exclusively on what needs to be added to make Forge a proper PWA.

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist once an app calls itself a PWA. Missing any of these = not actually a PWA.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Web App Manifest | Required for installability. Chrome, Edge, Safari all need a valid manifest with name, icons (192x192 + 512x512), display mode, theme_color, start_url | LOW | Next.js has built-in `app/manifest.ts` support -- export a function returning `MetadataRoute.Manifest`. Zero library dependencies. |
| Service Worker Registration | A registered service worker is a hard requirement for the browser install prompt. Without one, the app simply cannot be installed | LOW | Create `public/sw.js` and register via a client component on mount. Official Next.js guide shows this exact pattern. |
| App Shell Caching | Users expect the PWA to load its UI skeleton instantly, even on slow networks. Cache the HTML shell, CSS, JS bundles, and static assets | MEDIUM | Cache-first for static assets (JS/CSS bundles, icons). The service worker precaches the app shell so navigation feels instant. Manual approach (explicit cache list in sw.js) is simpler than Serwist for Forge's scope. |
| Install Prompt UX | Users need a clear way to install the app. On Chrome/Edge, `beforeinstallprompt` fires automatically when criteria are met. iOS requires manual "Add to Home Screen" instructions | LOW | Two code paths: (1) intercept `beforeinstallprompt` event for Chrome/Edge install button, (2) detect iOS and show manual instructions. Hide entirely when `display-mode: standalone` is already active. |
| HTTPS Enforcement | Service workers only work over HTTPS (or localhost for dev). Non-negotiable browser requirement | LOW | Already handled -- Forge runs behind Docker/reverse proxy in production. For local dev, `next dev --experimental-https` is available. |
| Responsive Chat Layout | Mobile users expect the chat to be usable. Current sidebar is fixed at `w-64 shrink-0` with no collapse behavior -- completely broken on screens under ~768px | HIGH | Requires the most significant refactoring in the milestone: collapsible sidebar (hidden by default on mobile, overlay/drawer pattern), full-width chat area on small screens, touch-friendly message input area. Existing `ConversationList` component stays, but its parent layout changes substantially. |
| Responsive Header/Navigation | App header must adapt to mobile. Navigation needs a mobile menu pattern (hamburger or sheet drawer) | MEDIUM | Current `AppHeader` is desktop-oriented. Needs a hamburger button that opens a Sheet/Drawer with nav links on mobile. shadcn/ui Sheet component is available for this. |
| Responsive Settings Page | Settings must be usable on mobile. Current `max-w-4xl px-4 py-8` layout is mostly fine, but form inputs may need stacking and touch-target adjustments | LOW | Minor work. Test at 375px width and fix any overflow or tap-target issues. |
| Theme Color Meta Tags | `theme-color` in manifest and HTML meta tags ensures browser chrome (address bar, task switcher) matches the app theme | LOW | Add to manifest.ts and as `<meta name="theme-color">` in root layout. Should ideally respect light/dark theme via media query. |
| App Icons at Required Sizes | 192x192 and 512x512 PNG icons are minimum for installability. Maskable icon variant needed for Android adaptive icons | LOW | Generate icon set from Forge logo/branding. Place in `public/`. Add `purpose: "maskable"` variant. |
| Security Headers for Service Worker | Service worker file needs specific headers to prevent cache poisoning and ensure correct MIME type | LOW | Configure in `next.config.ts` headers: `Cache-Control: no-cache`, correct `Content-Type`, and `Content-Security-Policy` for sw.js route. |

### Differentiators (Competitive Advantage)

Features that make Forge's PWA experience stand out. Most AI chat apps (ChatGPT, Claude.ai, Gemini) are standard web apps, not PWAs. Being installable is itself a differentiator.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Offline Conversation History (read-only) | View past conversations when the backend is unreachable. Cache conversation list and recent message content via the service worker | MEDIUM | Network-first for API calls with cache fallback. When offline, show cached conversations as read-only with a clear "offline" indicator. Users get value (reviewing past work) even without connectivity. Depends on: service worker caching strategy. |
| Offline Shell with Graceful Degradation | Instead of a blank page when offline, show the full UI shell with a clear "You're offline -- reconnect to chat" message. Preserves the app feel even without the backend | LOW | Cache app shell assets in the service worker. Intercept failed API calls and return a custom offline response. Show an offline banner in the UI. Much better than the default browser "no internet" page. |
| Smart Reconnection UX | When coming back online, automatically retry the last failed request, show a "Back online" toast, and restore normal state. Seamless online/offline transitions | LOW | Listen for `online`/`offline` events. Show toast notifications via existing UI patterns. Retry queued navigation. Good UX polish that most PWAs skip. |
| Standalone Window Experience | When running as installed PWA, `display: standalone` removes browser chrome. The app gets its own window, own icon in dock/taskbar, feels native | LOW | Already handled by manifest `display: standalone`. Need to verify the app header provides sufficient navigation context when browser back/forward buttons are absent. May need a back button in chat detail views. |
| Swipe Gestures for Sidebar | Swipe right from left edge to open conversation list, swipe left to close. Natural mobile interaction pattern | MEDIUM | Touch event listeners on the main content area. Only active on touch devices. Significantly improves the collapsible sidebar experience. Depends on: responsive sidebar existing first. |
| Splash Screen | Branded loading screen on app launch (before React hydrates). Native app feel on mobile | LOW | Configured automatically via manifest `background_color` + icons. Browsers generate the splash from manifest data. No custom code needed beyond good manifest values. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem like good PWA additions but create problems for Forge specifically.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full Offline Chat (send messages offline) | "I want to chat even without internet" | Forge connects to external LLM APIs (Ollama, OpenAI, etc.). Chat requires backend + LLM endpoint. Queuing messages offline creates false expectations -- the message sits unsent. Background sync adds complexity with no value since the LLM call fails anyway | Show "offline" state clearly. Let users read cached history. Do not pretend chat works offline. |
| Push Notifications | "Notify me when generation completes" | Forge is single-user, self-hosted. The user is already looking at the screen when chatting. Push requires VAPID keys, notification server (web-push npm package), and significant backend complexity for minimal value in a synchronous chat tool | Skip entirely for v2.1. Revisit only if async/background task features are added later. |
| Background Sync for Message Queue | "Queue messages when offline, send when reconnected" | Same fundamental problem as offline chat -- the LLM endpoint is unreachable, so queued messages cannot be processed. The Background Sync API also has limited browser support (Chrome-only) | Show clear offline state instead of false queuing UX |
| Periodic Background Sync | "Check for new messages periodically" | Forge is not a multi-user messaging app. There are no "incoming messages" from other users. User initiates all conversations. Chrome-only API | Not applicable to single-user AI chat |
| Full Offline-First with IndexedDB | "Mirror the entire database client-side" | Forge uses SQLite backend with complex relations (conversations, messages, traces, files, embeddings). Duplicating this in IndexedDB creates sync nightmares and doubles the data model surface | Cache API responses in the service worker for read-only offline access. Do not build a client-side database mirror. |
| Serwist / next-pwa Library | "Use Serwist for automatic precaching" | Serwist requires webpack configuration, which conflicts with Turbopack (Next.js default bundler in dev). Adds a dependency and build complexity for functionality achievable with a simple manual service worker given Forge's modest caching needs | Write a manual `public/sw.js` with explicit cache lists. Simpler, no build-tool conflicts, full control. |
| Bottom Navigation Bar | "Mobile apps use bottom nav" | Introduces a navigation paradigm conflict -- Forge already has a top header and sidebar. Adding bottom nav creates three navigation surfaces. Design decision complexity outweighs the benefit for v2.1 | Use hamburger menu in header for mobile. Evaluate bottom nav as a future refinement if user feedback demands it. |
| Camera/Microphone for Voice Chat | "Talk to the AI" | Significant scope expansion beyond PWA. Speech-to-text adds dependencies, new UI patterns, backend processing. This is a product feature, not a PWA infrastructure feature | Defer to a dedicated voice milestone if desired. Not a PWA concern. |

## Feature Dependencies

```
[Web App Manifest]
    |
    +-- [App Icons] (manifest references icon file paths in /public)
    |
    +-- [Theme Color Meta Tags] (manifest theme_color + HTML meta must agree)
    |
    +-- [Splash Screen] (generated automatically from manifest data)

[Service Worker Registration]
    |
    +-- [App Shell Caching] (SW handles all cache logic)
    |       |
    |       +-- [Offline Shell with Graceful Degradation] (requires cached shell assets)
    |       |
    |       +-- [Offline Conversation History] (extends caching to API responses)
    |
    +-- [Install Prompt UX] (SW registration is a prerequisite for browser install prompt)
    |
    +-- [Smart Reconnection UX] (online/offline events pair with SW state)

[Responsive Chat Layout] (independent of service worker -- can be built in parallel)
    |
    +-- [Swipe Gestures for Sidebar] (requires collapsible sidebar to exist first)

[Responsive Header/Navigation] (independent, parallel workstream)

[Security Headers] ──applied to──> [Service Worker file serving]

[HTTPS] ──prerequisite for──> [Service Worker Registration]
```

### Dependency Notes

- **Install Prompt requires both Manifest AND Service Worker:** Browsers will not fire `beforeinstallprompt` without a registered service worker. Manifest alone is insufficient.
- **Offline features require App Shell Caching:** Cannot show offline UI if shell assets are not cached in the service worker.
- **Responsive layout is fully independent of SW work:** Can be built in parallel with service worker features. No technical dependency between them, but both are required for the milestone to be complete.
- **Swipe Gestures depend on Responsive Chat Layout:** The sidebar must be collapsible before swipe gestures make sense.
- **Offline Conversation History depends on both SW and API caching strategy:** Must decide which API routes to cache and for how long.
- **Existing features are unaffected:** All v1.0 features (chat, traces, MCP, settings) continue to work. PWA wraps around them without modifying core functionality.

## MVP Definition

### Launch With (v2.1 Core)

Minimum to call Forge a genuine PWA that users can install and use on mobile.

- [ ] Web App Manifest (`app/manifest.ts`) with correct metadata -- installability gate
- [ ] App icons (192x192, 512x512, maskable) in `/public` -- installability gate
- [ ] Service worker (`public/sw.js`) with app shell caching -- installability gate + instant loads
- [ ] Service worker registration component -- wires up SW on client mount
- [ ] Install prompt UX (beforeinstallprompt + iOS fallback) -- users need to discover installation
- [ ] Responsive chat layout with collapsible sidebar -- mobile is unusable without this
- [ ] Responsive header with mobile navigation (hamburger + Sheet) -- users must navigate on mobile
- [ ] Offline shell with "you're offline" messaging -- graceful degradation
- [ ] Theme color meta tags (light + dark aware) -- polished browser chrome
- [ ] Security headers for service worker -- prevent cache poisoning
- [ ] Viewport meta tag verification -- correct mobile scaling

### Add After Core (v2.1 Polish)

Features to add once the core PWA passes Lighthouse audit and manual mobile testing.

- [ ] Offline conversation history (read-only cached API responses) -- adds value but needs cache invalidation strategy
- [ ] Smart reconnection UX (auto-retry + "back online" toast) -- polish
- [ ] Swipe gestures for sidebar toggle on touch devices -- mobile UX enhancement
- [ ] Settings page responsive adjustments -- minor touch-target and stacking fixes
- [ ] Standalone mode navigation verification -- ensure back navigation works without browser chrome

### Future Consideration (v3+)

Features to defer beyond the PWA milestone entirely.

- [ ] Bottom navigation bar -- requires design paradigm decision
- [ ] Push notifications -- only relevant if async/background tasks are added
- [ ] Background sync -- only relevant for multi-step async workflows
- [ ] Voice/audio input -- product feature, not PWA infrastructure
- [ ] IndexedDB local data store -- only if true offline-first is validated as needed

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Web App Manifest + Icons | HIGH | LOW | P1 |
| Service Worker + Registration | HIGH | LOW | P1 |
| App Shell Caching | HIGH | MEDIUM | P1 |
| Install Prompt UX | HIGH | LOW | P1 |
| Responsive Chat Layout (collapsible sidebar) | HIGH | HIGH | P1 |
| Responsive Header / Mobile Nav | HIGH | MEDIUM | P1 |
| Offline Shell + Graceful Degradation | MEDIUM | LOW | P1 |
| Theme Color Meta Tags | MEDIUM | LOW | P1 |
| Security Headers for SW | MEDIUM | LOW | P1 |
| Viewport Meta Verification | MEDIUM | LOW | P1 |
| Offline Conversation History | MEDIUM | MEDIUM | P2 |
| Smart Reconnection UX | MEDIUM | LOW | P2 |
| Swipe Gestures | LOW | MEDIUM | P2 |
| Settings Responsive Fixes | LOW | LOW | P2 |
| Standalone Navigation Check | LOW | LOW | P2 |
| Bottom Navigation Bar | MEDIUM | MEDIUM | P3 |
| Push Notifications | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for v2.1 launch (installable + mobile-usable)
- P2: Should have, add during v2.1 polish phase
- P3: Nice to have, defer to future milestone

## Competitor PWA Analysis

| PWA Feature | ChatGPT (web) | Claude.ai (web) | Open WebUI | Forge (Current) | Forge (v2.1 Target) |
|-------------|---------------|-----------------|------------|-----------------|---------------------|
| Installable PWA | Yes (manifest + SW) | No | Partial (manifest, no SW) | No | Yes |
| Mobile responsive | Yes (polished) | Yes (polished) | Yes (basic) | No (fixed w-64 sidebar) | Yes |
| Offline access | Shell only | No | No | No | Shell + cached history |
| Service worker | Yes | No | No | No | Yes (manual) |
| Native app feel (standalone) | Yes | No | No | No | Yes |
| Install prompt | Yes | No | No | No | Yes |
| Collapsible sidebar | Yes (hamburger) | Yes (collapsible) | Yes (toggle) | No (fixed) | Yes (drawer on mobile) |
| Touch gestures | Basic | Basic | None | None | Swipe for sidebar |
| Offline indicator | Yes | N/A | No | No | Yes |
| Splash screen | Yes | N/A | No | No | Yes (via manifest) |

**Key insight:** Claude.ai and Open WebUI are NOT PWAs. ChatGPT is the only major AI chat with full PWA support. Making Forge a proper PWA puts it ahead of most self-hosted alternatives and on par with ChatGPT's web experience for installability.

## Existing Forge Features Affected by PWA Work

These v1.0 features need specific attention during PWA implementation:

| Existing Feature | PWA Impact | Action Needed |
|------------------|-----------|---------------|
| Chat sidebar (`ConversationList`) | Currently in fixed `w-64` aside -- breaks on mobile | Wrap in collapsible drawer component, keep component internals unchanged |
| `AppHeader` | Desktop-only navigation | Add hamburger menu trigger, mobile Sheet with nav links |
| SSE streaming | Service worker must not interfere with SSE connections | Exclude `/api/` routes from SW cache; use network-only for streaming endpoints |
| Theme (light/dark/system) | Theme color meta tag should match current theme | Dynamic `<meta name="theme-color">` that updates with theme changes |
| JWT auth | SW fetch interception must forward auth headers | Ensure SW does not strip Authorization headers when proxying cached responses |
| File upload | Must work on mobile (file picker, camera for documents) | Verify `<input type="file">` works on mobile browsers; add `accept` attributes |
| Execution traces (expandable) | Must be usable on narrow screens | Verify trace expansion works at mobile widths; may need horizontal scroll for wide content |
| Settings forms | Must be touch-friendly | Verify tap targets >= 44px, form fields stack on mobile |

## Sources

- [Next.js Official PWA Guide](https://nextjs.org/docs/app/guides/progressive-web-apps) -- Primary implementation reference. Covers manifest.ts, service worker, install prompt, security headers. HIGH confidence.
- [MDN PWA Best Practices](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Best_practices) -- Authoritative PWA standards reference. HIGH confidence.
- [Microsoft PWA Best Practices](https://learn.microsoft.com/en-us/microsoft-edge/progressive-web-apps/how-to/best-practices) -- Additional PWA UX patterns. MEDIUM confidence.
- [Serwist Documentation](https://serwist.pages.dev/docs/next/getting-started) -- Evaluated and rejected due to webpack/Turbopack conflict. MEDIUM confidence.
- [What PWA Can Do Today](https://whatpwacando.today/) -- Web API capability reference. MEDIUM confidence.
- Forge codebase analysis -- Direct inspection of `chat/layout.tsx` (fixed `w-64` sidebar), `settings/layout.tsx`, `(protected)/layout.tsx`, `next.config.ts`, `package.json`. HIGH confidence.

---
*Feature research for: PWA capabilities in Forge AI assistant*
*Researched: 2026-03-22*
