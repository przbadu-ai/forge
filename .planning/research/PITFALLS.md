# Pitfalls Research

**Domain:** PWA integration for existing Next.js AI chat app (SSE streaming + JWT auth + dynamic content)
**Researched:** 2026-03-22
**Confidence:** HIGH (verified against Next.js official docs, W3C service worker spec discussions, and Forge codebase analysis)

## Critical Pitfalls

### Pitfall 1: Service Worker Intercepts SSE Streaming Requests — Kills Token-by-Token Delivery

**What goes wrong:**
The service worker's `fetch` event handler intercepts the POST request to `/api/v1/chat/{id}/stream`. Since the response is a long-lived SSE stream using `ReadableStream`, the service worker either: (a) tries to cache the response and waits for the stream to complete (buffering all tokens), (b) holds the worker alive for the entire duration of the stream (violating the SW lifecycle), or (c) corrupts the stream by cloning it for cache storage. The user sees tokens arrive all at once after the LLM finishes, or streaming breaks entirely.

**Why it happens:**
Default service worker fetch handlers (including Workbox/Serwist runtime caching) match all requests. Forge uses `fetch()` + `ReadableStream` for SSE (not `EventSource`), so the Accept header is not `text/event-stream` — the standard SSE bypass check does not work. The request looks like a normal POST to the service worker.

**How to avoid:**
- In the service worker fetch handler, explicitly bypass all requests to the backend API base URL (port 8000 or `NEXT_PUBLIC_API_URL`). The service worker should `return` without calling `respondWith()` for these requests, letting the browser handle them natively.
- Additionally, bypass any request where the URL path contains `/stream` or `/chat/` as a defense-in-depth measure.
- Never use a catch-all `NetworkFirst` or `StaleWhileRevalidate` strategy without URL filtering.
- Test streaming after adding the service worker — this is the single most likely regression.

```javascript
// sw.js fetch handler pattern
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  // Never intercept backend API calls — especially SSE streams
  if (url.port === '8000' || url.pathname.includes('/stream')) {
    return; // Let browser handle natively
  }
  // Only handle same-origin navigation and static asset requests
  // ...
});
```

**Warning signs:**
- Streaming worked before adding the service worker, stops working after
- Tokens arrive in a single batch instead of incrementally
- `AbortController` stop button no longer terminates the stream
- DevTools Application > Service Workers shows the fetch handler intercepting `/stream` requests

**Phase to address:** Phase 1 (Service Worker foundation) — this must be the FIRST thing validated after SW registration

---

### Pitfall 2: Service Worker Caches Authenticated Responses — Serves Stale or Wrong-User Data

**What goes wrong:**
The service worker caches API responses that include JWT-authenticated data (conversation list, messages, settings). On the next request, it returns the cached response without checking if the JWT is still valid or if the user has logged out. In Forge's specific case: (a) after logout and re-login, the SW serves cached conversation data from the previous session, (b) after token refresh, the SW serves a response that was fetched with the old token, or (c) the SW caches a 401 response and serves it even after re-authentication.

**Why it happens:**
Forge stores the JWT in memory (`useAuth` context) and passes it via the `Authorization` header. The service worker sees the response as a normal fetch response and caches it based on URL alone. The Authorization header is not part of the cache key by default. Developers add runtime caching for "API responses" without realizing every response is user-specific and session-specific.

**How to avoid:**
- Never cache any request that goes to the backend API. The service worker should only cache: the app shell (HTML), static assets (JS, CSS, images, fonts), and the manifest.
- If API caching is ever considered (for offline mode), cache keys MUST include a session identifier, and the entire cache must be cleared on logout.
- Add a `message` listener in the SW that clears all caches when the main thread sends a `LOGOUT` message.
- Never cache responses with `Authorization` headers — add an explicit check.

**Warning signs:**
- Conversations appear from a previous session after logout/login
- Settings changes don't reflect until hard refresh (Ctrl+Shift+R)
- 401 errors persist even after successful re-authentication
- Different conversations show identical message content

**Phase to address:** Phase 1 (Service Worker foundation) — must be architecturally decided before any caching strategy is implemented

---

### Pitfall 3: Service Worker Scope and `output: "standalone"` — SW File Not Served in Docker

**What goes wrong:**
Forge uses `output: "standalone"` in `next.config.ts` for Docker deployment. In standalone mode, Next.js copies only the files needed to run the server into `.next/standalone/`. Files in `public/` are NOT automatically included — they must be copied manually in the Dockerfile. If `sw.js` is placed in `public/` (the standard location), it will exist in development but be missing in the Docker production image. The browser silently fails to register the service worker, and the PWA appears to work (manifest loads, install prompt shows) but has no offline capability.

**Why it happens:**
The Next.js standalone output docs explicitly state that `public/` and `.next/static/` must be copied manually. Developers test PWA features in `next dev` where `public/` is served directly, assume it works, and discover the SW is missing only after Docker deployment.

**How to avoid:**
- In the Dockerfile, explicitly copy `public/` to the standalone output:
  ```dockerfile
  COPY --from=builder /app/public ./public
  COPY --from=builder /app/.next/static ./.next/static
  ```
- Verify SW registration succeeds in the Docker container by checking `navigator.serviceWorker.controller` in the browser console after deployment.
- Add a health check or E2E test that verifies `/sw.js` returns 200 with `Content-Type: application/javascript` in the production build.
- Set `Cache-Control: no-cache, no-store, must-revalidate` on `sw.js` per the Next.js official PWA guide, so browsers always fetch the latest version.

**Warning signs:**
- PWA installs on desktop/mobile but has no offline capability
- DevTools > Application > Service Workers shows "No service worker registered"
- `/sw.js` returns 404 in production but works in development
- `navigator.serviceWorker` is undefined or registration promise rejects

**Phase to address:** Phase 1 (Service Worker foundation) + Phase 3 (Docker integration testing)

---

### Pitfall 4: Manifest `start_url` and Auth — PWA Opens to Login Screen Every Time

**What goes wrong:**
The `manifest.json` sets `start_url: "/"` which maps to the app root. When the PWA is launched from the home screen, the browser opens a fresh context without the auth session. Forge uses in-memory JWT tokens with cookie-based refresh. If the refresh token cookie has `SameSite=Strict` or the cookie domain doesn't match the standalone PWA origin, the refresh call fails silently and the user is redirected to `/login` every time they open the installed app.

**Why it happens:**
In PWA standalone mode (`display: "standalone"`), the app runs in its own window without a browser URL bar. Cookie behavior can differ from the regular browser context. The `start_url` is loaded fresh on each launch. If session restoration depends on cookies that are not available in the standalone context, auth breaks.

**How to avoid:**
- Set the refresh token cookie with `SameSite=Lax` (not `Strict`) — standalone PWA launches are treated as top-level navigations, which `Lax` allows.
- Ensure the cookie `Path=/` and `Domain` matches the origin the PWA is served from.
- Test the PWA install flow end-to-end: install, close, reopen from home screen, verify auth persists without re-login.
- Consider a `start_url: "/?source=pwa"` to track PWA launches and debug auth issues.
- The protected layout's `useEffect` redirect to `/login` must handle the brief `isLoading: true` state gracefully — show a splash screen, not a flash of the login page.

**Warning signs:**
- PWA always shows login screen on launch from home screen
- Auth works in browser tab but not in installed PWA
- Refresh token cookie is present in browser DevTools but absent in standalone PWA DevTools
- Brief flash of login page before auth restores

**Phase to address:** Phase 2 (Manifest and install flow) — requires auth integration testing

---

### Pitfall 5: Cache Invalidation After Deployment — Users Stuck on Old App Version

**What goes wrong:**
After deploying a new version, the service worker serves the old cached app shell. The user sees the old UI, old JavaScript bundles, and potentially old API client code that is incompatible with the new backend. The service worker update cycle requires: (1) browser detects new SW, (2) new SW installs in background, (3) old SW still controls the page, (4) user closes ALL tabs, (5) new SW activates. Most users never close all tabs — they are stuck on the old version indefinitely.

**Why it happens:**
Service worker lifecycle is intentionally conservative — it never disrupts the current page. Developers assume "deploy = update" but the SW lifecycle means the old version can persist for days or weeks. This is catastrophic for Forge because a backend API change (new endpoint, changed schema) will break the cached frontend.

**How to avoid:**
- Implement a `skipWaiting()` + `clients.claim()` pattern so the new SW activates immediately.
- Show an "Update available" toast/banner when a new SW is detected (`registration.onupdatefound`). On user click, call `registration.waiting.postMessage({ type: 'SKIP_WAITING' })` and reload.
- In the SW install handler, call `self.skipWaiting()` to bypass waiting.
- In the SW activate handler, call `self.clients.claim()` to take control of all open tabs.
- Register the SW with `updateViaCache: 'none'` (already recommended in Next.js official PWA guide) so the browser always checks for a new SW file.
- Version the SW file name or include a version constant that changes with each build.

**Warning signs:**
- Users report seeing old UI after deployment
- API errors appear because cached frontend calls endpoints that changed
- DevTools > Application > Service Workers shows "waiting to activate"
- Hard refresh (Ctrl+Shift+R) fixes the issue (bypasses SW)

**Phase to address:** Phase 2 (SW update strategy) — MUST be implemented before first production deployment

---

### Pitfall 6: Offline Shell Shows UI But All Actions Fail Silently

**What goes wrong:**
The app shell (layout, sidebar, header) loads from cache when offline, giving the impression the app works. But every action — sending a message, loading conversations, changing settings — fails because the backend API is unreachable. Without explicit offline detection and user feedback, the app appears frozen or broken. Users type a message, hit send, and nothing happens.

**Why it happens:**
The app shell pattern caches the HTML/JS/CSS but not the data. Forge is entirely API-dependent — every screen requires a successful API call. Developers implement the offline shell as a "PWA checkbox" without considering the user experience when the shell loads but data doesn't.

**How to avoid:**
- Add an online/offline status indicator in the AppHeader component using `navigator.onLine` and the `online`/`offline` window events.
- When offline, disable the chat input and show "You are offline — messages will be sent when connection is restored" instead of silently failing.
- Wrap `apiFetch` with offline detection — if `!navigator.onLine`, reject immediately with a user-friendly error rather than letting the request timeout.
- Do NOT attempt to queue messages for later sending in v2.1 — this adds massive complexity (conflict resolution, ordering). Simply show a clear offline state.
- Cache the conversation list for read-only browsing when offline (optional, low priority).

**Warning signs:**
- App shell loads offline but every interaction shows a spinner that never resolves
- Error messages say "Failed to fetch" instead of "You are offline"
- Send button appears active when offline
- No visual distinction between online and offline states

**Phase to address:** Phase 2 (Offline UX) — after app shell caching is working

---

### Pitfall 7: `next-pwa` Is Abandoned — Using It Causes Build Failures with Turbopack

**What goes wrong:**
Developers find `next-pwa` as the top search result for "Next.js PWA" and install it. The package has not been maintained since 2023, does not support Next.js 15+, and requires webpack. Since Next.js 16 defaults to Turbopack, `next-pwa` causes build failures or requires falling back to webpack (losing Turbopack performance benefits). Even if it builds, it generates a service worker with aggressive caching defaults that will trigger Pitfalls 1, 2, and 5.

**Why it happens:**
`next-pwa` has 3.5k+ GitHub stars and dominates SEO for "Next.js PWA" searches. Many tutorials and blog posts still recommend it. The package README does not clearly state it is unmaintained.

**How to avoid:**
- Use either Serwist (`@serwist/next`) or a hand-written service worker. For Forge's needs (simple app shell caching + bypass for API calls), a hand-written `public/sw.js` following the Next.js official PWA guide is simpler and more controllable.
- If using Serwist: it works with Turbopack for production builds but requires `--webpack` flag for local development PWA testing. This is acceptable.
- Avoid any package that wraps Workbox with aggressive defaults — Forge needs precise control over what gets cached and what doesn't.

**Warning signs:**
- `npm install next-pwa` followed by build errors mentioning webpack plugins
- Service worker precaches every page and API route
- `next build` takes significantly longer after adding the PWA plugin
- Unexplained caching behavior that didn't exist before

**Phase to address:** Phase 0 (Technology selection) — decide before writing any code

---

### Pitfall 8: Cross-Origin API Requests Bypass Service Worker Entirely

**What goes wrong:**
Forge's frontend (port 3000) makes API calls to the backend (port 8000). These are cross-origin requests. Service workers can only intercept requests within their scope (same origin by default). The SW registered at `localhost:3000/sw.js` with `scope: '/'` does not intercept requests to `localhost:8000`. This is actually CORRECT behavior for Forge (we don't want the SW intercepting API calls — see Pitfall 1). But developers who try to add offline API response caching via the SW will find it silently doesn't work for cross-origin requests.

**Why it happens:**
Forge deliberately uses direct browser-to-backend API calls (not proxied through Next.js) for SSE streaming performance. The `API_BASE` is constructed from `window.location.hostname:8000`. This cross-origin architecture is good for streaming but means the SW cannot intercept, cache, or modify API requests even if you wanted it to.

**How to avoid:**
- Accept this as a feature, not a bug. Document that the SW handles ONLY the app shell (HTML/JS/CSS/images) and the backend API is always network-only.
- If offline API response caching is ever needed (future milestone), it must be done in the application layer (IndexedDB via the React app), not in the service worker.
- Do not attempt to proxy API calls through Next.js route handlers just to make them same-origin for SW caching — this reintroduces the SSE buffering problem from the v1.0 pitfalls.

**Warning signs:**
- Developer adds Workbox runtime caching for `/api/*` routes but it never caches anything
- Network tab shows API requests not going through the SW
- Offline mode caches the shell but has zero API data available

**Phase to address:** Phase 1 (Architecture decisions) — understand this constraint before designing the caching strategy

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip SW update UX (auto skipWaiting) | No toast/banner to build | Users may see jarring mid-session reload; no control over when update happens | MVP only; add user-controlled update prompt before production |
| Cache all static assets with no size limit | Everything loads offline | Cache storage grows unbounded; mobile devices with limited storage may evict the SW cache | Never; set a max cache size (50MB) and use LRU eviction |
| Use `next-pwa` for "quick setup" | Faster initial implementation | Abandoned package; webpack dependency; aggressive caching defaults | Never; use hand-written SW or Serwist |
| Skip offline detection in UI | Less code to write | Users confused when actions fail silently offline | Never; even a simple `navigator.onLine` check is sufficient |
| Hardcode manifest icons as static files | No build pipeline needed | Cannot adapt icons for different themes (light/dark) or platform requirements | MVP acceptable; dynamic manifest can come later |
| Register SW in development mode | Easier to test PWA features | SW caches dev bundles; HMR breaks; confusing stale code during development | Never; only register in production builds |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| SW + SSE streaming (fetch+ReadableStream) | SW fetch handler intercepts the stream request, buffering or corrupting it | Bypass all backend API URLs in the SW fetch handler; never call `respondWith()` for streaming requests |
| SW + JWT auth (Bearer token in header) | Caching responses keyed by URL only; serving wrong-session data | Never cache authenticated API responses in the SW; cache only static app shell assets |
| SW + `output: "standalone"` Docker | `public/sw.js` not copied to standalone output | Add explicit `COPY public/ ./public` in Dockerfile after standalone build |
| Manifest + cookie-based auth refresh | `SameSite=Strict` cookie not sent on PWA standalone launch | Use `SameSite=Lax` for refresh token cookie; test in installed PWA context |
| SW + Next.js `compress: false` | SW caches uncompressed responses; no gzip benefit | Add compression at the reverse proxy level (nginx) rather than Next.js; SW caches compressed responses transparently |
| SW + HMR in development | Service worker caches dev bundles; hot reload stops working | Conditionally register SW only in production: `if (process.env.NODE_ENV === 'production')` |
| Manifest + dynamic `API_BASE` | Manifest `start_url` hardcoded but API base is dynamic (hostname-based) | Set `start_url: "/"` and let the app resolve API_BASE at runtime from `window.location` |
| SW update + backend deployment | Frontend SW update and backend deploy happen at different times; version mismatch | Version the API; or deploy frontend and backend atomically via docker-compose |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Precaching all Next.js pages and chunks | Initial SW install downloads 10MB+ of JS bundles; slow on mobile | Only precache the app shell (layout, critical CSS); let other routes load on-demand with runtime caching | Immediately on mobile with slow connections |
| No cache size limit on runtime cache | Cache Storage grows unbounded as user navigates | Set `maxEntries` (e.g., 50) and `maxAgeSeconds` (e.g., 7 days) on runtime cache strategies | After weeks of use; mobile storage pressure |
| SW fetch handler runs on every request | Even for requests the SW should not handle, the fetch event fires and adds overhead | Use `return` (no `respondWith()`) for requests outside SW scope; Chrome optimizes this as a "no-op fetch handler" | Noticeable on pages with 50+ resource requests |
| Caching Next.js `_next/static/` chunks with wrong strategy | Immutable hashed chunks cached as `NetworkFirst` (unnecessary network check) | Use `CacheFirst` for `_next/static/` (immutable, hash-versioned); `NetworkFirst` only for HTML navigation | Every page load wastes a network round-trip |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| SW serves cached login page when session is valid | User sees login flash; may re-enter credentials unnecessarily | Never cache `/login` route; always fetch from network |
| SW caches responses containing JWT tokens | Token persists in Cache Storage even after logout | Never cache API responses; clear all caches on logout via `postMessage` |
| `sw.js` served without proper headers | Browser caches old SW indefinitely; security patches don't reach users | Set `Cache-Control: no-cache, no-store, must-revalidate` on `/sw.js` response |
| Manifest `scope` too broad | SW controls paths it shouldn't (e.g., admin panels, different apps on same domain) | Set `scope: "/"` only if the PWA is the sole app on the origin |
| SW fetch handler leaks auth headers to third-party domains | If SW intercepts cross-origin requests and adds Authorization header | Only add auth headers for same-origin requests; bypass cross-origin entirely |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Install prompt shown immediately on first visit | Annoying; user hasn't experienced the app yet | Show install prompt after 3+ sessions or after user demonstrates engagement (e.g., sends first message) |
| No visual feedback during SW update | User doesn't know an update is available; stuck on old version | Show a dismissible banner: "New version available — tap to update" |
| PWA installed but no offline indicator | User opens PWA offline, app shell loads, then confusion when nothing works | Show offline banner in AppHeader; disable send button; show last-cached conversation list if available |
| Splash screen missing or wrong colors | App feels unfinished on iOS/Android launch | Set `background_color` and `theme_color` in manifest to match Forge's theme; provide proper splash icons |
| iOS "Add to Home Screen" instructions not shown | iOS users don't know how to install (no automatic install prompt on Safari) | Detect iOS Safari + not-standalone; show manual installation instructions |
| PWA opens in both browser tab and standalone | Confusing; notifications go to wrong instance | Use `getInstalledRelatedApps()` API to detect installation; suggest opening in installed app |

---

## "Looks Done But Isn't" Checklist

- [ ] **SSE Streaming:** Verify token-by-token streaming still works after SW registration — test in both browser tab and installed PWA
- [ ] **Auth Persistence:** Install PWA, close it completely, reopen from home screen — verify user is still logged in without re-entering credentials
- [ ] **SW in Docker:** Build Docker image, run container, verify `/sw.js` returns 200 and SW registers successfully
- [ ] **Cache Isolation:** Log in, browse conversations, log out, log back in — verify no stale data from previous session
- [ ] **SW Update:** Deploy a new version, open existing PWA — verify update notification appears and app updates on action
- [ ] **Offline State:** Disconnect network, open PWA — verify clear offline indicator and no silent failures
- [ ] **iOS Install:** Test on iOS Safari — verify install instructions appear and installed PWA works correctly
- [ ] **Theme Consistency:** Verify manifest `theme_color` and `background_color` match both light and dark theme modes
- [ ] **No Dev SW:** Verify service worker is NOT registered during `next dev` — only in production builds
- [ ] **AbortController:** Verify stop-generation button works in PWA standalone mode (not just browser tab)

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| SW intercepts SSE streams | LOW | Add URL bypass in SW fetch handler; redeploy SW; users get fix on next visit |
| Cached auth data served cross-session | MEDIUM | Clear all caches in SW activate handler; send LOGOUT message to SW on auth state change; force SW update |
| SW missing in Docker | LOW | Fix Dockerfile COPY command; rebuild and redeploy image |
| Users stuck on old version | MEDIUM | Deploy SW with `skipWaiting()` + `clients.claim()`; or instruct users to clear site data in browser settings |
| PWA always shows login screen | LOW | Change cookie `SameSite` to `Lax`; verify cookie domain; redeploy backend |
| Offline UI shows broken state | LOW | Add `navigator.onLine` check and offline banner; purely frontend change |
| `next-pwa` causing build failures | MEDIUM | Remove package; replace with hand-written SW or Serwist; rewrite SW configuration |
| Unbounded cache growth | LOW | Add `maxEntries` and `maxAgeSeconds` to cache strategies; SW update clears old caches |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| SW intercepts SSE (Pitfall 1) | Phase 1: SW foundation | E2E test: send chat message with SW active; verify tokens arrive incrementally |
| Cached auth data (Pitfall 2) | Phase 1: SW caching architecture | Test: login, browse, logout, login as same user; verify no stale data |
| SW missing in Docker (Pitfall 3) | Phase 1: SW foundation + Dockerfile | CI test: build Docker image; curl `/sw.js`; verify 200 response |
| Manifest + auth (Pitfall 4) | Phase 2: Manifest and install UX | Manual test: install PWA, close, reopen; verify no login prompt |
| Cache invalidation (Pitfall 5) | Phase 2: SW update strategy | Test: deploy new version; verify update banner appears in existing PWA |
| Offline UX (Pitfall 6) | Phase 2: Offline experience | Test: disconnect network; verify offline banner and disabled input |
| next-pwa abandoned (Pitfall 7) | Phase 0: Technology decision | N/A — decision point, not code verification |
| Cross-origin SW scope (Pitfall 8) | Phase 1: Architecture documentation | Code review: verify SW fetch handler does not attempt to cache cross-origin requests |

---

## Sources

- [Guides: PWAs - Next.js Official Documentation](https://nextjs.org/docs/app/guides/progressive-web-apps) — verified 2026-03-22, covers manifest, SW registration, security headers, and recommends Serwist for offline
- [Should EventSource bypass service worker interception? - W3C ServiceWorker Issue #885](https://github.com/w3c/ServiceWorker/issues/885) — confirms SSE/SW interaction challenges
- [ServiceWorker lifetime and respondWith() with ReadableStream - W3C Issue #882](https://github.com/w3c/ServiceWorker/issues/882) — confirms stream lifetime issues in SW
- [Service worker cache messing with authentication - OHIF/Viewers Issue #1691](https://github.com/OHIF/Viewers/issues/1691) — real-world example of cached auth data causing issues
- [Authenticated PWA? - W3C ServiceWorker Issue #909](https://github.com/w3c/ServiceWorker/issues/909) — discussion of auth challenges in PWAs
- [When 'Just Refresh' Doesn't Work: Taming PWA Cache Behavior - Infinity Interactive](https://iinteractive.com/resources/blog/taming-pwa-cache-behavior) — SW update lifecycle problems
- [index.html cached in a bad state when service worker updates - Workbox Issue #1528](https://github.com/GoogleChrome/workbox/issues/1528) — cache invalidation failure case
- [Building a PWA in Next.js with Serwist (Next-PWA Successor)](https://javascript.plainenglish.io/building-a-progressive-web-app-pwa-in-next-js-with-serwist-next-pwa-successor-94e05cb418d7) — Serwist as modern replacement for next-pwa
- [Dynamically Generating PWA App Icons in Next.js 16 with Serwist - Aurora Scharff](https://aurorascharff.no/posts/dynamically-generating-pwa-app-icons-nextjs-16-serwist/) — confirms Serwist works with Next.js 16 + Turbopack
- [A guide to Service Workers - pitfalls and best practices - The Codeship](https://www.thecodeship.com/web-development/guide-service-worker-pitfalls-best-practices/) — general SW pitfalls reference
- [Stuff I wish I'd known sooner about service workers - Rich Harris](https://gist.github.com/Rich-Harris/fd6c3c73e6e707e312d7c5d7d0f3b2f9) — practical SW lessons from Svelte creator
- Forge codebase analysis: `frontend/next.config.ts` (standalone output, compress: false), `frontend/src/hooks/useChat.ts` (fetch+ReadableStream SSE), `frontend/src/lib/api.ts` (cross-origin API calls to port 8000), `frontend/src/context/auth-context.tsx` (in-memory JWT + cookie refresh)

---
*Pitfalls research for: PWA integration into Forge AI chat app*
*Researched: 2026-03-22*
