import { expect, Page, test } from "@playwright/test";

async function assertReportContent(page: Page) {
  // Severity groups (from severity.band), including empty ones.
  for (const band of ["critical", "high", "medium", "low"]) {
    await expect(page.getByTestId(`severity-${band}`)).toBeVisible();
  }
  const buttons = page.locator('[data-testid^="severity-"] li button');
  expect(await buttons.count()).toBeGreaterThan(0);

  // Open Findings until one has a Data Flow (some have none).
  const total = await buttons.count();
  let opened = false;
  for (let i = 0; i < total; i++) {
    await buttons.nth(i).click();
    await expect(page.getByTestId("finding-detail")).toBeVisible();
    if ((await page.getByTestId("flow-step").count()) > 0) {
      opened = true;
      break;
    }
  }
  expect(opened, "a Finding with a Data Flow").toBe(true);

  const detail = page.getByTestId("finding-detail");
  await expect(detail.getByTestId("evidence-line").first()).toBeVisible();
  await expect(detail.getByTestId("evidence").first().locator("figcaption")).toContainText(/:\d+/);
  await expect(detail.getByTestId("data-flow")).toBeVisible();
  expect(await detail.getByTestId("flow-step").count()).toBeGreaterThan(0);
  await expect(detail.getByTestId("primary-provision")).toBeVisible();
  await expect(detail.getByTestId("statute-excerpt").first()).not.toBeEmpty();
  await expect(detail.getByTestId("penalty-ceiling")).toContainText("crore");
  await expect(detail.getByTestId("justification")).not.toBeEmpty();
  await expect(detail.getByTestId("recommended-fix")).not.toBeEmpty();
  await expect(detail.getByTestId("llm-triage")).not.toBeEmpty();

  const map = page.getByTestId("personal-data-map");
  await expect(map.getByRole("columnheader", { name: "Element" })).toBeVisible();
  await expect(map.getByRole("columnheader", { name: "Data Category" })).toBeVisible();
  await expect(map.getByRole("columnheader", { name: "Processing Operations" })).toBeVisible();
  expect(await map.getByTestId("map-row").count()).toBeGreaterThan(0);
  await expect(map.getByText("No Finding").first()).toBeVisible();

  const downloads = page.getByTestId("downloads");
  for (const f of ["json", "md", "html", "pdf"]) {
    const link = downloads.locator(`a[href$="/report/${f}"]`);
    await expect(link).toBeVisible();
    const res = await page.request.get((await link.getAttribute("href"))!);
    expect(res.status()).toBe(200);
  }
}

test("live dashboard", async ({ page }) => {
  await page.goto("/dashboard");
  await page.getByLabel("Target Application").fill("targets/juice-shop");
  await page.getByRole("button", { name: "Scan", exact: true }).click();
  await expect(page.getByTestId("provenance")).toHaveText(/Live|Cache-only/, { timeout: 120_000 });
  await expect(page.getByTestId("run-status")).toHaveAttribute("data-status", "completed", {
    timeout: 120_000,
  });
  await assertReportContent(page);
});

test("replay dashboard", async ({ page }) => {
  await page.route("**/*", (route) => {
    const url = new URL(route.request().url());
    return url.hostname === "127.0.0.1" ? route.continue() : route.abort();
  });
  await page.goto("/dashboard");
  await page.getByRole("button", { name: /Replay Mode \(recorded Juice Shop scan\)/ }).click();
  await expect(page.getByTestId("provenance")).toHaveText("Replay Mode");
  await expect(page.getByTestId("run-status")).toHaveAttribute("data-status", "completed", {
    timeout: 120_000,
  });
  await assertReportContent(page);
});
