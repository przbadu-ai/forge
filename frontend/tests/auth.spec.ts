import { test, expect } from "@playwright/test";

test.describe("Authentication flow", () => {
  test("redirects to /login when unauthenticated", async ({ page }) => {
    // Clear all cookies first
    await page.context().clearCookies();
    await page.goto("/");
    await expect(page).toHaveURL(/\/login/);
  });

  test("shows login form with username and password fields", async ({
    page,
  }) => {
    await page.goto("/login");
    await expect(page.getByLabel(/username/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(
      page.getByRole("button", { name: /sign in/i })
    ).toBeVisible();
  });

  test("shows error for invalid credentials", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/username/i).fill("admin");
    await page.getByLabel(/password/i).fill("wrongpassword");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page.getByRole("alert")).toBeVisible();
  });

  test("successful login redirects to home page", async ({ page }) => {
    await page.context().clearCookies();
    await page.goto("/login");
    await page.getByLabel(/username/i).fill("admin");
    await page.getByLabel(/password/i).fill("changeme");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page).toHaveURL("/");
    await expect(page.getByText(/signed in as admin/i)).toBeVisible();
  });

  test("session persists after page refresh", async ({ page }) => {
    // Login first
    await page.context().clearCookies();
    await page.goto("/login");
    await page.getByLabel(/username/i).fill("admin");
    await page.getByLabel(/password/i).fill("changeme");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page).toHaveURL("/");

    // Refresh -- auth context should restore session via refresh endpoint
    await page.reload();
    await expect(page).toHaveURL("/");
    await expect(page.getByText(/signed in as admin/i)).toBeVisible();
  });

  test("logout redirects to login and clears session", async ({ page }) => {
    // Login first
    await page.context().clearCookies();
    await page.goto("/login");
    await page.getByLabel(/username/i).fill("admin");
    await page.getByLabel(/password/i).fill("changeme");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page).toHaveURL("/");

    // Click logout
    await page.getByRole("button", { name: /sign out/i }).click();
    await expect(page).toHaveURL(/\/login/);

    // Navigating to protected route should redirect to login again
    await page.goto("/");
    await expect(page).toHaveURL(/\/login/);
  });
});
