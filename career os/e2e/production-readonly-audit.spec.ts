import { test, expect } from "@playwright/test";

const URL = "https://career-os-manoj.lovable.app";
test("live anonymous production pages, protection, sample workspace and browser health", async ({ page }, testInfo) => {
  const errors: string[] = [];
  const failed: { path: string; status: number }[] = [];
  const measurements: { route: string; width: number; ready_ms: number; document_width: number }[] = [];
  page.on("pageerror", error => errors.push(error.message.slice(0, 300)));
  page.on("response", response => {
    if (response.status() >= 400) failed.push({ path: new globalThis.URL(response.url()).pathname, status: response.status() });
  });
  const started = Date.now();
  try {
  await page.goto(`${URL}/login`);
  await page.waitForLoadState("networkidle");
  await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();
  measurements.push({ route: "/login", width: 1280, ready_ms: Date.now() - started, document_width: await page.evaluate(() => document.documentElement.scrollWidth) });
  await page.screenshot({ path: testInfo.outputPath("production-login.png"), fullPage: true });
  await page.goto(`${URL}/tasks`);
  await expect(page.getByText("Sign in to Career OS", { exact: true })).toBeVisible();
  // Product's existing sample mode writes only browser storage in a fresh,
  // unauthenticated test context. Never sign in, create an account or submit
  // personal records. These are UI checks, not hosted database verification.
  await page.goto(`${URL}/login`);
  await page.waitForLoadState("networkidle");
  await page.getByRole("button", { name: "Explore the sample workspace" }).click();
  await expect(page.getByRole("heading", { name: "Your career, in motion" })).toBeVisible();
  for (const width of [1440, 768, 390]) {
    await page.setViewportSize({ width, height: 900 });
    for (const route of ["/", "/today", "/planner", "/tasks", "/goals", "/skills", "/projects", "/networking", "/interviews", "/jobs", "/daily-log", "/copilot", "/more", "/settings"]) {
      const begin = Date.now();
      await page.goto(`${URL}${route}`);
      await expect(page.locator("main h1")).toBeVisible();
      measurements.push({ route, width, ready_ms: Date.now() - begin, document_width: await page.evaluate(() => document.documentElement.scrollWidth) });
    }
    await page.goto(`${URL}/`);
    await page.screenshot({ path: testInfo.outputPath(`production-demo-${width}.png`), fullPage: true });
  }
  // Real unauthenticated response. No interception and no live model request.
  await page.goto(`${URL}/copilot`);
  await page.getByLabel("Copilot command").fill("Create AUDIT sample-only proposal");
  await page.getByRole("button", { name: "Run command" }).click();
  await expect(page.getByRole("alert")).toContainText("Sign in to use AI commands");
  expect(errors).toEqual([]);
  } finally {
    await testInfo.attach("production-observations", { body: JSON.stringify({ errors, failed, measurements }, null, 2), contentType: "application/json" });
  }
});

test("live sample-only agent gates and console diagnostics", async ({ page }, testInfo) => {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  page.on("console", message => {
    if (message.type() === "error") consoleErrors.push(message.text().slice(0, 300));
  });
  page.on("pageerror", error => pageErrors.push(error.message.slice(0, 300)));
  await page.goto(`${URL}/login`);
  await page.waitForLoadState("networkidle");
  await page.getByRole("button", { name: "Explore the sample workspace" }).click();
  await expect(page.getByRole("heading", { name: "Your career, in motion" })).toBeVisible();
  const gates: { route: string; gated: boolean }[] = [];
  for (const route of ["/vault", "/agent"]) {
    await page.goto(`${URL}${route}`);
    await page.waitForLoadState("networkidle");
    const gate = page.getByText("Sign in to see agent records", { exact: true });
    await expect(gate).toBeVisible();
    gates.push({ route, gated: await gate.isVisible() });
  }
  await testInfo.attach("production-console-and-gates", {
    body: JSON.stringify({ consoleErrors, pageErrors, gates }, null, 2),
    contentType: "application/json",
  });
  expect(pageErrors).toEqual([]);
});
