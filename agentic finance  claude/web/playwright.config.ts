import { defineConfig } from "@playwright/test";

// Expects the engine (http://127.0.0.1:8000, demo mode, seeded) and the web app (http://localhost:3000) to be running.
// See docs/local-setup.md. `npm run test:e2e` from web/.
export default defineConfig({
  testDir: "./tests",
  timeout: 180_000,
  expect: { timeout: 20_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: process.env.WEB_URL ?? "http://localhost:3000",
    acceptDownloads: true,
    trace: "retain-on-failure",
  },
});
