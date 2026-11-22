import { defineConfig } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

export default defineConfig({
  testDir: "./e2e",
  timeout: 180_000,
  workers: 1,
  use: { baseURL: "http://127.0.0.1:8000" },
  webServer: {
    command: ".venv/bin/python -m uvicorn dashboard.backend.app:app --host 127.0.0.1 --port 8000",
    cwd: repoRoot,
    url: "http://127.0.0.1:8000/",
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
