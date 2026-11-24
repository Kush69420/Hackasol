import { expect, test } from "@playwright/test";

const TOGGLE_TO_LIGHT = "Switch to light theme";
const TOGGLE_TO_DARK = "Switch to dark theme";

async function bodyBackground(page: import("@playwright/test").Page) {
  return page.locator("body").evaluate((el) => getComputedStyle(el).backgroundColor);
}

test("defaults to dark on a fresh browser", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.getByRole("button", { name: TOGGLE_TO_LIGHT })).toBeVisible();
});

test("ignores the OS light preference", async ({ browser }) => {
  const context = await browser.newContext({ colorScheme: "light" });
  const page = await context.newPage();
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await context.close();
});

test("toggle on Home persists across reload and carries to /dashboard", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: TOGGLE_TO_LIGHT }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.getByRole("button", { name: TOGGLE_TO_DARK })).toBeVisible();

  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

  await page.goto("/dashboard");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});

test("toggle on /dashboard works and persists back on Home", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: TOGGLE_TO_LIGHT }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

  await page.getByRole("button", { name: TOGGLE_TO_DARK }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
});

test("page background differs between dark and light", async ({ page }) => {
  await page.goto("/");
  const darkBackground = await bodyBackground(page);
  await expect(page.locator("body")).toHaveCSS("background-color", darkBackground);

  await page.getByRole("button", { name: TOGGLE_TO_LIGHT }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.locator("body")).not.toHaveCSS("background-color", darkBackground);
});
