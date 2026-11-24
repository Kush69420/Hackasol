import { expect, test } from "@playwright/test";

const diff = "--- a/server.ts\n+++ b/server.ts\n@@ -1 +1 @@\n-old\n+new\n";
const verified = JSON.stringify({ remaining: [], new: [], target_tests: [] });

test("Open PR requires authorization, fork destination, and shows review context", async ({ page }) => {
  const publishCalls: string[] = [];
  await page.route("**/api/scans/*/report/json", async (route) => {
    const response = await route.fetch();
    const report = await response.json();
    // Review state is injected here; no patch is generated or verified by the scan itself.
    const [first, second] = report.findings;
    first.fix_patch = { status: "accepted", diff, reason: verified, provenance: "authored" };
    second.fix_patch = { status: "generated", diff, reason: "not verified", provenance: "generated" };
    await route.fulfill({ response, json: report });
  });
  // Fake publisher: no GitHub write is ever reachable from this test.
  await page.route("**/api/scans/*/fix-patches/publish", async (route) => {
    publishCalls.push(route.request().postData() ?? "");
    await route.fulfill({ json: { url: "https://example.invalid/pr/1" } });
  });

  const res = await page.request.post("/api/scans", { data: { target: "targets/juice-shop" } });
  expect(res.status()).toBe(202);
  const { run_id } = (await res.json()) as { run_id: string };
  await page.goto(`/dashboard?run=${run_id}`);
  await expect(page.getByTestId("run-status")).toHaveAttribute("data-status", "completed", { timeout: 120_000 });
  expect(publishCalls).toHaveLength(0); // a scan alone opens no branch or PR

  const review = page.getByRole("region", { name: "Fix Patch review" });
  await expect(review).toContainText("Destination: TanKaizokuO/juice-shop; branch: dpdp-fix-review");
  await expect(review.getByRole("region", { name: /^Issue Type / }).first().getByRole("heading")).toBeVisible();
  await expect(review).toContainText("Re-scan: 0 selected Finding(s) remaining, 0 new");
  await expect(review).toContainText("Re-scan: not yet verified");

  const open = review.getByRole("button", { name: "Open PR" });
  await expect(open).toBeDisabled();
  await review.locator('input[type=checkbox]:not([disabled])').first().check();
  await expect(open).toBeDisabled(); // still unauthorized
  await review.getByLabel(/I authorize opening a PR/).check();

  await review.getByLabel("Destination fork").fill("juice-shop/juice-shop");
  await expect(review.getByRole("alert")).toContainText("not upstream");
  await expect(open).toBeDisabled();
  expect(publishCalls).toHaveLength(0);

  await review.getByLabel("Destination fork").fill("TanKaizokuO/juice-shop");
  await open.click();
  await expect(review.getByRole("status")).toContainText("https://example.invalid/pr/1");
  expect(publishCalls).toHaveLength(1);
  expect(JSON.parse(publishCalls[0])).toMatchObject({ destination: "TanKaizokuO/juice-shop", authorized: true });
});
