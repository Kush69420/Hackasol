import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

const criterion = {
  criterion: "Consent is enforced", applicability: "applicable", reason: "Processing requires consent",
  assessment: "Not established statically", linked_identifiers: ["F-1"], issue_types: ["CON-01"],
  evidence: [], step_counts: null,
};

async function showReport(page: Page, withProbes: boolean, replay: boolean) {
  await page.route("**/api/replays", (route) => route.fulfill({ json: { recordings: [] } }));
  await page.route("**/api/replays/juice-shop", (route) => route.fulfill({ json: { run_id: "mock" } }));
  await page.route("**/api/scans/mock/events", (route) => route.fulfill({
    contentType: "text/event-stream",
    body: `data: ${JSON.stringify({ run_id: "mock", ordinal: 1, mode: replay ? "recorded" : "live", type: "completed", elapsed_ms: 1, finding_count: 0 })}\n\n`,
  }));
  await page.route("**/api/scans/mock/legal", (route) => route.fulfill({ status: 404 }));
  await page.route("**/api/scans/mock/report/json", (route) => route.fulfill({ json: {
    target: { name: "Example", source: "local", commit: null }, llm: { mode: "live" }, personal_data_map: [], findings: [],
    consent_assessment: {
      criteria: [{ ...criterion, ...(withProbes ? { live_probes: [
        { status: "Confirmed", meaning: "violation observed", assertion: "Declined", reason: "Processing occurred" },
        { status: "Not Confirmed", meaning: "enforcement observed", assertion: "Withdrawal", reason: "Processing stopped" },
        { status: "Inconclusive", meaning: "could not determine", assertion: "Notice", reason: "No observation" },
      ] } : {}) }],
      ...(withProbes ? { live_probe_run: { target: "Example", commit: "1234567890abcdef1234567890abcdef12345678", observed_at: "2026-01-01T12:00:00Z" } } : {}),
    },
  } }));
  // Live uses the mocked "mock" run: page.request bypasses page.route, so a POST would reach the real backend.
  await page.goto(replay ? "/dashboard" : "/dashboard?run=mock");
  if (replay) await page.getByRole("button", { name: /Replay Mode \(recorded Juice Shop scan\)/ }).click();
  await expect(page.getByTestId("consent-assessment")).toBeVisible();
}

test("Replay Mode shows static criteria and past Live Probe outcomes", async ({ page }) => {
  await showReport(page, true, true);
  const criterionView = page.getByTestId("consent-criterion");
  await expect(criterionView).toContainText("Consent is enforced");
  await expect(criterionView).toContainText("Applicability: applicable — Processing requires consent");
  await expect(criterionView).toContainText("Assessment: Not established statically");
  await expect(criterionView).toContainText("Linked identifiers: F-1");
  await expect(criterionView).toContainText("Issue Types: CON-01");
  await expect(criterionView).toContainText("Past Live Probe results");
  const probes = page.getByTestId("consent-live-probe");
  await expect(probes).toHaveCount(3);
  await expect(probes.nth(0)).toContainText("Live Probe (Example @ 1234567890ab, 2026-01-01T12:00:00Z): Confirmed (violation observed)");
  await expect(probes.nth(1)).toContainText("Not Confirmed (enforcement observed)");
  await expect(probes.nth(2)).toContainText("Inconclusive (could not determine)");
});

test("live Report without probes has no consent Live Probe entries", async ({ page }) => {
  await showReport(page, false, false);
  await expect(page.getByTestId("consent-criterion")).toContainText("Assessment: Not established statically");
  await expect(page.getByTestId("consent-live-probes")).toHaveCount(0);
});
