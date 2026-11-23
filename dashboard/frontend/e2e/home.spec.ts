import { expect, Page, test } from "@playwright/test";

const SNIPPET = [
  "import sqlite3",
  "",
  'USER_EMAIL = "priya.sharma@example.com"',
  'USER_PHONE = "+91 98765 43210"',
  "",
  "def save_user(conn):",
  '    conn.execute("INSERT INTO users (email, phone) VALUES (?, ?)", (USER_EMAIL, USER_PHONE))',
  "",
].join("\n");

const FILE_SOURCE = [
  "import sqlite3",
  "",
  'PAN = "ABCDE1234F"',
  "",
  "def save(conn, email):",
  '    conn.execute("INSERT INTO users (email, pan) VALUES (?, ?)", (email, PAN))',
  "",
].join("\n");

/** Waits until the dashboard has attached to the run and shows its progress, then its Findings. */
async function expectRunRendered(page: Page) {
  await expect(page).toHaveURL(/\/dashboard\?run=[0-9a-f]+/, { timeout: 30_000 });
  await expect(page.getByRole("region", { name: "Run progress" })).toBeVisible();
  await expect(page.getByTestId("stages")).toBeVisible();
  await expect(page.getByTestId("run-status")).toHaveAttribute("data-status", "completed", {
    timeout: 120_000,
  });
  await expect(page.getByTestId("severity-critical")).toBeVisible();
}

test("home shows the three input tabs and keeps Audit disabled until the input is valid", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("tab", { name: "Git URL" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "File" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Code snippet" })).toBeVisible();

  const audit = page.getByRole("button", { name: "Audit", exact: true });
  await expect(audit).toBeDisabled();

  await page.getByRole("textbox", { name: "Git URL" }).fill("https://github.com/owner/repo");
  await expect(audit).toBeEnabled();
});

test("Git URL tab rejects a non-https address inline", async ({ page }) => {
  await page.goto("/");
  const url = page.getByRole("textbox", { name: "Git URL" });
  await url.fill("http://github.com/owner/repo");
  await expect(page.getByText("Use an https:// address")).toBeVisible();
  await expect(url).toHaveAttribute("aria-invalid", "true");
  await expect(page.getByRole("button", { name: "Audit", exact: true })).toBeDisabled();
});

test("Git URL submit posts the target and navigates to the dashboard run", async ({ page }) => {
  // No clone: the scan start is answered by a stub, and the dashboard's event stream is not mocked.
  await page.route("**/api/scans", (route) =>
    route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({ run_id: "mockgit0001", mode: "live" }),
    }),
  );
  await page.goto("/");
  await page.getByRole("textbox", { name: "Git URL" }).fill("https://github.com/owner/repo");
  const posted = page.waitForRequest((r) => r.method() === "POST" && r.url().endsWith("/api/scans"));
  await page.getByRole("button", { name: "Audit", exact: true }).click();
  expect((await posted).postDataJSON()).toEqual({ target: "https://github.com/owner/repo" });
  await expect(page).toHaveURL(/\/dashboard\?run=mockgit0001/);
});

test("code snippet audit navigates to the dashboard and renders progress and Findings", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("tab", { name: "Code snippet" }).click();
  await page.getByLabel("Language", { exact: true }).selectOption("python");
  await page.getByLabel("Code", { exact: true }).fill(SNIPPET);
  await page.getByRole("button", { name: "Audit", exact: true }).click();
  await expectRunRendered(page);
});

test("file upload audit navigates to the dashboard and renders progress and Findings", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("tab", { name: "File" }).click();
  await page.locator("#home-file").setInputFiles({
    name: "users.py",
    mimeType: "text/x-python",
    buffer: Buffer.from(FILE_SOURCE),
  });
  await expect(page.getByRole("group", { name: "Selected file" })).toContainText("users.py");
  await page.getByRole("button", { name: "Audit", exact: true }).click();
  await expectRunRendered(page);
});

test("reloading /dashboard?run=<id> re-attaches to the run", async ({ page }) => {
  const res = await page.request.post("/api/scans/snippet", {
    data: { code: SNIPPET, language: "python" },
  });
  expect(res.status()).toBe(202);
  const { run_id } = (await res.json()) as { run_id: string };

  await page.goto(`/dashboard?run=${run_id}`);
  await expect(page.getByTestId("run-status")).toHaveAttribute("data-status", "completed", {
    timeout: 120_000,
  });
  await page.reload();
  await expect(page.getByTestId("run-status")).toHaveAttribute("data-status", "completed", {
    timeout: 120_000,
  });
  await expect(page.getByTestId("severity-critical")).toBeVisible();
});
