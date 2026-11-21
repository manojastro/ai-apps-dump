// Browser tests: source inspection, correction, approval and downloads (demo mode, synthetic fixtures).
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, type Page, request, test } from "@playwright/test";

const ENGINE = process.env.ENGINE_URL ?? "http://127.0.0.1:8000";
const PASSWORD = process.env.SPREADLENS_SEED_PASSWORD ?? "spreadlens-demo";
const FIXTURES = join(__dirname, "..", "..", "engine", "fixtures", "documents");

async function engineSetup(): Promise<{ companyId: string; spreadId: string }> {
  const api = await request.newContext({ baseURL: ENGINE });
  const tok = (await (await api.post("/api/auth/login", { data: { email: "analyst@demo.local", password: PASSWORD } })).json()).token;
  const h = { authorization: `Bearer ${tok}` };
  const me = await (await api.get("/api/me", { headers: h })).json();
  const ws = me.workspaces.find((w: { name: string }) => w.name === "Demo Credit Team").id;
  const name = `E2E Aravalli ${Date.now()}`;
  const companyId = (await (await api.post(`/api/workspaces/${ws}/companies`, { headers: h, data: { name } })).json()).id;
  const up = await api.post(`/api/companies/${companyId}/documents`, {
    headers: h,
    multipart: { file: { name: "01_aravalli_fy25_standalone.pdf", mimeType: "application/pdf", buffer: readFileSync(join(FIXTURES, "01_aravalli_fy25_standalone.pdf")) } },
  });
  expect(up.status()).toBe(201);
  const dv = (await up.json()).document_version_id;
  for (let i = 0; i < 120; i++) {
    const d = await (await api.get(`/api/documents/${dv}`, { headers: h })).json();
    if (d.status === "ready_for_review") break;
    if (["failed", "partial"].includes(d.status)) throw new Error(`processing failed: ${JSON.stringify(d.runs[0])}`);
    await new Promise((r) => setTimeout(r, 1000));
  }
  const c = await (await api.get(`/api/companies/${companyId}`, { headers: h })).json();
  return { companyId, spreadId: c.spreads[0].id };
}

async function login(page: Page, email: string) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("navigation", { name: "Main" })).toBeVisible();
}

test("analyst inspects source, corrects a figure; reviewer approves; exports download", async ({ page, browser }) => {
  const { spreadId } = await engineSetup();
  await login(page, "analyst@demo.local");
  await page.goto(`/spreads/${spreadId}`);
  await expect(page.getByText("UNREVIEWED — not signed off")).toBeVisible();

  // Source inspection: clicking a figure opens its exact source location (page image + highlighted box)
  await page.getByRole("button", { name: /^Inventories 2025-03-31: 412\.80/ }).first().click();
  const drawer = page.getByRole("dialog");
  await expect(drawer.getByRole("img", { name: "Source page 2" })).toBeVisible();
  await expect(drawer.getByLabel("Exact source cell")).toBeVisible();
  await expect(drawer.getByText("412.80", { exact: true }).first()).toBeVisible();

  // Correction -> recalculation -> new version
  await drawer.getByLabel(/Value as shown in source/).fill("422.80");
  await drawer.getByLabel(/Reason/).fill("E2E: correct inventories");
  await drawer.getByRole("button", { name: "Apply" }).click();
  await expect(drawer.getByText(/Recalculated as spread version 2/)).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByRole("tab", { name: "Exception queue" }).click();
  await expect(page.getByText(/R04 failed: Components reconcile to 'Total current assets'/)).toBeVisible();

  // Revert, then submit for review
  await page.getByRole("tab", { name: "Balance sheet" }).click();
  await page.getByRole("button", { name: /^Inventories 2025-03-31: 422\.80/ }).first().click();
  await drawer.getByLabel(/Value as shown in source/).fill("412.80");
  await drawer.getByLabel(/Reason/).fill("E2E: revert");
  await drawer.getByRole("button", { name: "Apply" }).click();
  await expect(drawer.getByText(/Recalculated as spread version 3/)).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByRole("tab", { name: "Review, approval & exports" }).click();
  await page.getByRole("button", { name: /Submit v3 for review/ }).click();
  await expect(page.getByText("Submitted for review.")).toBeVisible();

  // Draft export is downloadable and labelled unreviewed
  await page.getByRole("button", { name: "Create draft export" }).click();
  await expect(page.getByText("DRAFT — unreviewed").first()).toBeVisible();
  const [draft] = await Promise.all([page.waitForEvent("download"), page.getByRole("link", { name: "Download Excel" }).first().click()]);
  expect(draft.suggestedFilename()).toMatch(/_v3_draft\.xlsx$/);

  // Reviewer (a different person) approves the specific version
  const ctx = await browser.newContext();
  const rp = await ctx.newPage();
  await login(rp, "reviewer@demo.local");
  await rp.goto(`/spreads/${spreadId}`);
  await rp.getByRole("tab", { name: "Review, approval & exports" }).click();
  await rp.getByRole("button", { name: /Approve v3/ }).click();
  await expect(rp.getByText(/Approved v3/)).toBeVisible();
  await expect(rp.getByText("APPROVED").first()).toBeVisible();
  const [xlsx] = await Promise.all([rp.waitForEvent("download"), rp.getByRole("link", { name: "Download Excel" }).first().click()]);
  expect(xlsx.suggestedFilename()).toMatch(/_v3_approved\.xlsx$/);
  const [pdf] = await Promise.all([rp.waitForEvent("download"), rp.getByRole("link", { name: "Download PDF" }).first().click()]);
  expect(pdf.suggestedFilename()).toMatch(/_v3_approved\.pdf$/);
  await ctx.close();
});

test("unauthenticated users are redirected to login", async ({ page }) => {
  await page.context().clearCookies();
  await page.goto("/");
  await expect(page).toHaveURL(/\/login$/);
});
