import { test, expect } from "@playwright/test";

test.describe("Settings page", () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.context().clearCookies();
    await page.goto("/login");
    await page.getByLabel(/username/i).fill("admin");
    await page.getByLabel(/password/i).fill("changeme");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page).toHaveURL("/");
  });

  test("settings page loads with tabs", async ({ page }) => {
    await page.goto("/settings");

    // Verify key tabs are present
    await expect(page.getByRole("tab", { name: /llm providers/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /embeddings/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /web search/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /mcp servers/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /skills/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /general/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /diagnostics/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /appearance/i })).toBeVisible();
  });

  test("web search tab shows form fields", async ({ page }) => {
    await page.goto("/settings");
    await page.getByRole("tab", { name: /web search/i }).click();

    await expect(page.getByLabel(/searxng base url/i)).toBeVisible();
    await expect(page.getByLabel(/exa api key/i)).toBeVisible();
  });

  test("diagnostics tab shows check now button", async ({ page }) => {
    await page.goto("/settings");
    await page.getByRole("tab", { name: /diagnostics/i }).click();

    await expect(
      page.getByRole("button", { name: /check now/i }),
    ).toBeVisible();
  });
});
