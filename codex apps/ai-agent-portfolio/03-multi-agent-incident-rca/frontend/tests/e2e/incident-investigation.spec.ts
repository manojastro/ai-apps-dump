import { expect, test } from "@playwright/test";

const api = process.env.API_URL_EXTERNAL ?? "http://localhost:8003";

test("injects an incident and watches all workers complete", async ({ page, request }) => {
  const created = await request.post(`${api}/api/v1/incidents`, {
    headers: { "X-Role": "investigator" },
    data: { title: "E2E bad deployment", service: "checkout-api", scenario: "bad-deployment", severity: "SEV-2", alert_summary: "5xx alert" },
  });
  expect(created.ok()).toBeTruthy();
  const incident = await created.json();
  await page.goto(`/investigations/${incident.id}`);
  await page.getByRole("button", { name: "Investigate now" }).click();
  await expect(page.getByText("Worker activity")).toBeVisible();
  await expect(page.getByText("Metrics Investigator")).toBeVisible();
  await expect(page.getByText("Ticket/Incident History Investigator")).toBeVisible();
});

test("explores immutable evidence, timeline, and dependency graph", async ({ page, request }) => {
  const created = await request.post(`${api}/api/v1/incidents`, {
    headers: { "X-Role": "investigator" },
    data: { title: "E2E database pool", service: "checkout-api", scenario: "db-connection-exhaustion", severity: "SEV-2", alert_summary: "timeouts" },
  });
  const incident = await created.json();
  expect((await request.post(`${api}/api/v1/incidents/${incident.id}/investigate`, { headers: { "X-Role": "investigator" } })).ok()).toBeTruthy();
  await page.goto(`/evidence/${incident.id}`);
  await expect(page.getByText("Evidence explorer")).toBeVisible();
  await expect(page.locator(".evidence-id").first()).toContainText("EV-");
  await page.goto(`/timeline/${incident.id}`);
  await expect(page.getByText("Incident timeline")).toBeVisible();
  await page.goto("/graph");
  await expect(page.getByText("checkout-api", { exact: true }).first()).toBeVisible();
  await expect(page.getByText(/checkout-api → payment-api/)).toBeVisible();
});

test("shows critic overturn, citation-gated RCA editor, and evaluation", async ({ page, request }) => {
  const created = await request.post(`${api}/api/v1/incidents`, {
    headers: { "X-Role": "investigator" },
    data: { title: "E2E misleading signal", service: "storefront", scenario: "misleading-signal", severity: "SEV-2", alert_summary: "payment failures" },
  });
  const incident = await created.json();
  await request.post(`${api}/api/v1/incidents/${incident.id}/investigate`, { headers: { "X-Role": "investigator" } });
  await page.goto(`/hypotheses/${incident.id}`);
  await expect(page.getByText("Original leader overturned")).toBeVisible();
  await page.goto(`/rca/${incident.id}`);
  await expect(page.getByLabel("RCA markdown")).toContainText("[EV-");
  await page.getByRole("button", { name: "Validate & save" }).click();
  await expect(page.getByText("Saved — citation gate passed")).toBeVisible();
  await page.goto("/evaluation");
  await expect(page.getByText("Evaluation dashboard")).toBeVisible();
  await expect(page.getByText("60", { exact: true }).first()).toBeVisible();
});

