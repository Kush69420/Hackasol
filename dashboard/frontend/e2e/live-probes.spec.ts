import { expect, test } from "@playwright/test";
import { spawn } from "node:child_process";
import { once } from "node:events";
import path from "node:path";
import { createInterface } from "node:readline";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");

test("Live Probe outcomes show masked Evidence", async ({ page }) => {
  const fixture = spawn(path.join(repoRoot, ".venv/bin/python"), ["-u", path.join(repoRoot, "tests/fixtures/probes/server.py")], {
    cwd: repoRoot, stdio: ["ignore", "pipe", "pipe"],
  });
  const lines = createInterface({ input: fixture.stdout });
  try {
    const port = await Promise.race([
      once(lines, "line").then(([line]) => Number(line)),
      once(fixture, "exit").then(() => { throw new Error("Synthetic Live Probe server exited before startup"); }),
      delay(10_000, undefined, { ref: false }).then(() => { throw new Error("Synthetic Live Probe server did not start"); }),
    ]);
    if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error("Invalid synthetic server port");
    await page.goto("/");
    await page.getByLabel("Target Application").fill("targets/juice-shop");
    await page.getByRole("button", { name: "Scan", exact: true }).click();
    await expect(page.getByTestId("run-status")).toHaveAttribute("data-status", "completed", { timeout: 120_000 });
    await page.getByLabel("Live Probe origin").fill(`http://127.0.0.1:${port}`);
    await page.getByLabel("I authorize probing this dedicated synthetic instance").check();
    await page.getByRole("button", { name: "Run Live Probes" }).click();
    await expect(page.getByRole("status")).toContainText(/[1-9]\d* matched Live Probe outcomes/, { timeout: 60_000 });
    await page.getByRole("button", { name: /SEC-07/ }).first().click();
    const evidence = page.getByLabel("Live Probe Evidence");
    await expect(evidence).toContainText("Confirmed");
    await expect(evidence).toContainText("GET /rest/memories");
    await expect(evidence).toContainText("[masked]");
  } finally {
    lines.close();
    if (fixture.exitCode === null && fixture.signalCode === null) {
      fixture.kill();
      await once(fixture, "exit");
    }
  }
});
