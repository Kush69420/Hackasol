import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

async function replay(page: Page, top: boolean) {
  await page.route("**/api/replays", (route) => route.fulfill({ json: { recordings: [] } }));
  await page.route("**/api/replays/juice-shop", (route) => route.fulfill({ json: { run_id: "mock" } }));
  await page.route("**/api/scans/mock/events", (route) => route.fulfill({
    contentType: "text/event-stream",
    body: `data: ${JSON.stringify({ run_id: "mock", ordinal: 1, mode: "recorded", type: "completed", elapsed_ms: 1, finding_count: 0 })}\n\n`,
  }));
  await page.route("**/api/scans/mock/report/json", (route) => route.fulfill({ json: {
    target: { name: "Example", source: "local" }, llm: { mode: "recorded" },
    personal_data_map: [], findings: [], consent_assessment: null,
  } }));
  await page.route("**/api/scans/mock/legal", (route) => route.fulfill({ json: {
    as_of: "2026-06-01",
    note: "Statutory maximum per Schedule; not a predicted or estimated fine. The actual penalty is determined by the Data Protection Board under section 33(2) factors.",
    ceilings: [{ provision: "DPDP-Act-8(5)", citation: "Section 8(5)", schedule_entry: "Schedule, item 1",
      statutory_maximum_inr_crore: 250, statutory_maximum_text: null, finding_ids: ["A", "B", "C", "D"],
      finding_ids_by_applicability: { applicable_primary: top ? ["A"] : [], related: ["B"], conditional: ["C"], needs_legal_review: ["D"] },
      severity_mix: { critical: 1, high: 0, medium: 0, low: 1 } }],
    highest_applicable_ceiling: top ? { amount_inr_crore: 250, provisions: ["DPDP-Act-8(5)"], finding_ids: ["A"] } : null,
    timeline: [
      { enforceable_from: "2025-11-13", finding_ids: ["A"], basis: null, days_until: -199, already_enforceable: true },
      { enforceable_from: "2027-05-13", finding_ids: ["B"], basis: null, days_until: 347, already_enforceable: false },
    ],
  } }));
  await page.goto("/");
  await page.getByRole("button", { name: /Replay Mode \(recorded Juice Shop scan\)/ }).click();
  await expect(page.getByTestId("legal-view")).toBeVisible();
}

test("Replay Mode shows applicability per Finding and the applicable ceiling", async ({ page }) => {
  await replay(page, true);
  const view = page.getByTestId("legal-view");
  await expect(view.getByRole("heading", { name: "Statutory Penalty Ceilings and Enforcement Timeline" })).toBeVisible();
  await expect(page.getByTestId("ceiling-note")).toContainText("not a predicted or estimated fine");
  await expect(page.getByTestId("ceiling-note")).toContainText("section 33(2)");
  await expect(page.getByTestId("highest-ceiling")).toContainText("₹250 crore (DPDP-Act-8(5))");
  const row = page.getByTestId("ceiling-row");
  await expect(row).toContainText("Schedule, item 1");
  await expect(row).toContainText("₹250 crore");
  await expect(row).toContainText("Applicable Primary Provision: A");
  await expect(row).toContainText("Related Provision: B");
  await expect(row).toContainText("Conditional Provision: C");
  await expect(row).toContainText("Needs Legal Review (breach not established): D");
  await expect(row).toContainText("critical: 1, low: 1");
  await expect(view).not.toContainText(/total exposure/i);
  const phases = page.getByTestId("phase");
  await expect(phases.nth(0)).toContainText("2025-11-13: already enforceable");
  await expect(phases.nth(1)).toContainText("enforceable in 347 days");
});

test("related and conditional Provisions do not create an applicable ceiling", async ({ page }) => {
  await replay(page, false);
  await expect(page.getByTestId("highest-ceiling")).toContainText("Highest applicable ceiling: none");
  await expect(page.getByTestId("ceiling-row")).not.toContainText("Applicable Primary Provision");
  await expect(page.getByTestId("ceiling-row")).toContainText("Conditional Provision: C");
});
