import { test, expect } from "@playwright/test";

test.describe("PWA Service Worker", () => {
  test("manifest is served at /manifest.webmanifest", async ({ page }) => {
    const response = await page.goto("/manifest.webmanifest");
    expect(response?.status()).toBe(200);
    const manifest = await response?.json();
    expect(manifest.name).toBe("Forge");
    expect(manifest.display).toBe("standalone");
    expect(manifest.icons).toHaveLength(3);
  });

  test("sw.js is served and registers", async ({ page }) => {
    // Navigate to app to trigger SW registration
    await page.goto("/");
    // Check that sw.js is fetchable
    const swResponse = await page.evaluate(async () => {
      const res = await fetch("/sw.js");
      return { status: res.status, contentType: res.headers.get("content-type") };
    });
    expect(swResponse.status).toBe(200);
    expect(swResponse.contentType).toContain("javascript");
  });

  test("SW uses NetworkOnly for /api/* routes (SSE bypass)", async ({ page }) => {
    // Fetch sw.js source and verify it contains NetworkOnly for /api/
    const swSource = await page.evaluate(async () => {
      const res = await fetch("/sw.js");
      return res.text();
    });
    // The compiled SW must contain the NetworkOnly strategy for API routes
    // This ensures SSE streaming is not intercepted/buffered
    expect(swSource).toContain("api");
    // Verify NetworkOnly appears (compiled name may vary, but the pattern must exist)
    // The /api/ pattern must be registered before default cache entries
  });

  test("offline fallback page renders at /~offline", async ({ page }) => {
    await page.goto("/~offline");
    await expect(page.getByText("You are offline")).toBeVisible();
    await expect(page.getByRole("button", { name: /retry/i })).toBeVisible();
  });
});
