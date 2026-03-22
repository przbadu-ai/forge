---
phase: quick
plan: 260322-cox
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/api/v1/health_diagnostics.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "ChromaDB health check returns 'ok' when EphemeralClient is working"
    - "ChromaDB health check reports latency in milliseconds"
    - "ChromaDB health check returns 'error' with message if client fails"
  artifacts:
    - path: "backend/app/api/v1/health_diagnostics.py"
      provides: "Fixed _check_chromadb using in-process client"
      contains: "get_chroma_client"
  key_links:
    - from: "backend/app/api/v1/health_diagnostics.py"
      to: "backend/app/core/chroma_client.py"
      via: "import get_chroma_client"
      pattern: "from app\\.core\\.chroma_client import get_chroma_client"
---

<objective>
Fix ChromaDB health check to use the in-process EphemeralClient instead of making HTTP requests to a non-existent server.

Purpose: The current `_check_chromadb()` function sends an HTTP GET to `http://localhost:8100/api/v1/heartbeat`, but the app uses `chromadb.EphemeralClient()` (in-process, no server). This always fails. The fix uses the existing `get_chroma_client()` singleton and calls its `.heartbeat()` method.

Output: Working ChromaDB health check that reports accurate status.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@backend/app/api/v1/health_diagnostics.py
@backend/app/core/chroma_client.py

<interfaces>
From backend/app/core/chroma_client.py:
```python
def get_chroma_client() -> Any:
    """Get or create the ChromaDB client singleton. Returns EphemeralClient."""
    # client.heartbeat() returns nanosecond timestamp (int)
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix _check_chromadb to use in-process EphemeralClient</name>
  <files>backend/app/api/v1/health_diagnostics.py</files>
  <action>
Replace the `_check_chromadb()` function (lines 117-142) to use the in-process client instead of HTTP:

1. Add import at top: `from app.core.chroma_client import get_chroma_client`
2. Remove the `import httpx` inside the function (no longer needed for ChromaDB check)
3. Replace the function body:
   - Call `get_chroma_client()` to get the EphemeralClient singleton
   - Call `client.heartbeat()` which returns a nanosecond timestamp (int) confirming the client is alive
   - Measure latency with `time.perf_counter()` around the heartbeat call
   - Return `ServiceStatus(name="ChromaDB", status="ok", latency_ms=latency)` on success
   - Return `ServiceStatus(name="ChromaDB", status="error", error=str(exc)[:200])` on exception

The function should look like:
```python
async def _check_chromadb() -> ServiceStatus:
    """Check ChromaDB connectivity via in-process client."""
    try:
        client = get_chroma_client()
        start = time.perf_counter()
        client.heartbeat()  # Returns nanosecond timestamp; confirms client is alive
        latency = int((time.perf_counter() - start) * 1000)
        return ServiceStatus(
            name="ChromaDB",
            status="ok",
            latency_ms=latency,
        )
    except Exception as exc:
        return ServiceStatus(
            name="ChromaDB",
            status="error",
            error=str(exc)[:200],
        )
```

Note: `heartbeat()` is a sync method on EphemeralClient, which is fine since it is in-process and near-instant. No need for asyncio.wait_for or run_in_executor.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone && python -c "from app.core.chroma_client import get_chroma_client; c = get_chroma_client(); print('heartbeat:', c.heartbeat())" && make -C backend lint</automated>
  </verify>
  <done>ChromaDB health check uses get_chroma_client().heartbeat() instead of HTTP request to localhost:8100. Lint passes. The httpx import is no longer used for ChromaDB (but may remain if used elsewhere in the file like _check_web_search).</done>
</task>

</tasks>

<verification>
- `make -C backend lint` passes (no unused imports, type checks OK)
- Manual: Start the backend, hit GET /api/v1/health/diagnostics with auth, ChromaDB shows status "ok" with latency
</verification>

<success_criteria>
- ChromaDB service status returns "ok" (not "error") in diagnostics endpoint
- No HTTP connection attempt to localhost:8100 for ChromaDB
- Existing health checks for other services remain unchanged
</success_criteria>

<output>
After completion, create `.planning/quick/260322-cox-fix-chromadb-connection-all-connection-a/260322-cox-SUMMARY.md`
</output>
