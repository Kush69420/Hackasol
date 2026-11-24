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

const BANDS = ["critical", "high", "medium", "low"] as const;
const TARGET_LABELS = ["Juice Shop", "TrackMyRupee", "ai-kyc-platform", "singharya E-KYC"];

type TargetSummary = {
  name: string;
  label: string;
  replay_available: boolean;
  live_available: boolean;
  scan_date: string | null;
  counts: Record<(typeof BANDS)[number], number> & { total: number };
};

/** Mirrors ui.ts formatDate so the card text can be compared exactly. */
function formatScanDate(iso: string | null): string {
  if (!iso) return "not stated";
  const d = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(d.getTime())) return iso;
  return d
    .toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" })
    .replace(/ /g, " ");
}

function targetCard(page: Page, label: string) {
  return page.getByRole("article", { name: label, exact: true });
}

test("home renders a card per Target Application with the counts and scan date from /api/targets", async ({ page }) => {
  const res = await page.request.get("/api/targets");
  expect(res.status()).toBe(200);
  const targets = (await res.json()) as TargetSummary[];
  expect(targets.map((t) => t.label).sort()).toEqual([...TARGET_LABELS].sort());

  await page.goto("/");
  await expect(page.locator("article.target-card")).toHaveCount(TARGET_LABELS.length);
  for (const t of targets) {
    const card = targetCard(page, t.label);
    await expect(card).toBeVisible();
    expect(t.counts, `counts for ${t.label}`).not.toBeNull();
    const chips = await card.locator(".home-counts li").allTextContents();
    expect(chips).toEqual([
      ...BANDS.map((band) => `${t.counts[band]} ${band}`),
      `${t.counts.total} total`,
    ]);
    expect(await card.locator("dl.target-meta dd").nth(0).textContent()).toBe(formatScanDate(t.scan_date));
  }
});

test("Replay on the Juice Shop card opens its run on the dashboard and renders the Findings", async ({ page }) => {
  const res = await page.request.get("/api/targets");
  const targets = (await res.json()) as TargetSummary[];
  const juice = targets.find((t) => t.name === "juice-shop");
  expect(juice?.replay_available, "Juice Shop has a recording").toBe(true);

  await page.goto("/");
  const replay = targetCard(page, "Juice Shop").getByRole("button", { name: "Replay recorded scan: Juice Shop" });
  await expect(replay).toBeEnabled();
  const posted = page.waitForResponse(
    (r) => r.request().method() === "POST" && new URL(r.url()).pathname === "/api/replays/juice-shop",
  );
  await replay.click();
  const started = await posted;
  expect(started.status()).toBe(202);
  const { run_id } = (await started.json()) as { run_id: string };

  await expect(page).toHaveURL(`/dashboard?run=${run_id}`);
  await expectRunRendered(page);
  // Reported, not asserted: whether the dashboard shows the Replay pill for a run started from Home.
  const pills = await page.getByTestId("provenance").allTextContents();
  console.log(`PROVENANCE_PILLS_AFTER_HOME_REPLAY=${JSON.stringify(pills)}`);
});

test("Scan live is disabled with the clone-missing text when a clone is absent, and starts a run when present", async ({ page }) => {
  // Every clone exists in this checkout, so the missing state is simulated on the list response only.
  await page.route("**/api/targets", async (route) => {
    const response = await route.fetch();
    const body = (await response.json()) as TargetSummary[];
    const missing = body.map((t) => (t.name === "ai-kyc-platform" ? { ...t, live_available: false } : t));
    await route.fulfill({ response, json: missing });
  });
  await page.goto("/");

  const absent = targetCard(page, "ai-kyc-platform").getByRole("button", { name: "Scan live: ai-kyc-platform" });
  await expect(absent).toBeDisabled();
  await expect(absent).toHaveAccessibleDescription("Clone missing: see README Set-up");
  await expect(absent).toHaveAttribute("title", "Clone missing: see README Set-up");

  // The stub answers the POST so no real live scan starts.
  const stubbedRunId = "0123456789abcdef0123456789abcdef";
  await page.route("**/api/targets/juice-shop/scan", (route) =>
    route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({ run_id: stubbedRunId, mode: "live" }),
    }),
  );
  const present = targetCard(page, "Juice Shop").getByRole("button", { name: "Scan live: Juice Shop" });
  await expect(present).toBeEnabled();
  const posted = page.waitForRequest((r) => r.method() === "POST" && new URL(r.url()).pathname === "/api/targets/juice-shop/scan");
  await present.click();
  await posted;
  await expect(page).toHaveURL(`/dashboard?run=${stubbedRunId}`);
});

test("the pipeline strip shows the four audit stages in order", async ({ page }) => {
  await page.goto("/");
  const section = page.getByRole("region", { name: "How an audit works" });
  await expect(section).toBeVisible();
  await expect(section.locator(".pipeline-step .pipeline-name")).toHaveText([
    "Inventory",
    "Personal Data Elements",
    "Data Flows",
    "Findings",
  ]);
});

test("a replay started from Home is listed under Recent runs with a link to its dashboard run", async ({ page }) => {
  const res = await page.request.post("/api/replays/juice-shop");
  expect(res.status()).toBe(202);
  const { run_id } = (await res.json()) as { run_id: string };

  await page.goto("/");
  await page.reload();
  const recent = page.getByRole("region", { name: "Recent runs" });
  const link = recent.locator(`a.run-link[href="/dashboard?run=${run_id}"]`);
  await expect(link).toBeVisible();
  await expect(link).toContainText("Juice Shop");
});

test("with the Target Applications list failing, the unavailable note shows and the form still works", async ({ page }) => {
  await page.route("**/api/targets", (route) =>
    route.fulfill({ status: 500, contentType: "text/plain", body: "internal error" }),
  );
  await page.route("**/api/scans", (route) =>
    route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({ run_id: "fedcba9876543210fedcba9876543210", mode: "live" }),
    }),
  );
  await page.goto("/");
  await expect(
    page.getByText("Target Applications are unavailable right now. The form above still works."),
  ).toBeVisible();
  await expect(page.locator("article.target-card")).toHaveCount(0);

  await page.getByRole("textbox", { name: "Git URL" }).fill("https://github.com/owner/repo");
  const audit = page.getByRole("button", { name: "Audit", exact: true });
  await expect(audit).toBeEnabled();
  await audit.click();
  await expect(page).toHaveURL(/\/dashboard\?run=fedcba9876543210fedcba9876543210/);
});
