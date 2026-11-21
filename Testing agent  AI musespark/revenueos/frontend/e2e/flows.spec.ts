import { type Page, expect, test } from "@playwright/test";

const password = process.env.E2E_PASSWORD;
if (!password) throw new Error("Set E2E_PASSWORD to the DEMO_USER_PASSWORD used when loading data.");

async function signIn(page: Page, email: string) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password as string);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
}

test("a wrong password shows an error and stays on login", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill("cro@revenueos.example");
  await page.getByLabel("Password").fill("definitely-wrong");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText("Incorrect email or password")).toBeVisible();
});

test("CRO sees the forecast, risk-sorted deals and reasons", async ({ page }) => {
  await signIn(page, "cro@revenueos.example");
  await expect(page.getByText("Expected revenue")).toBeVisible();
  await expect(page.getByText(/Range \$/)).toBeVisible();

  await page.getByRole("link", { name: "Deals", exact: true }).click();
  const rows = page.getByTestId("deal-row");
  await expect(rows.first()).toBeVisible();
  await expect(rows.first().getByText("At risk")).toBeVisible();
  await rows.first().getByRole("link").first().click();
  await expect(page.getByText("What is hurting this deal")).toBeVisible();
});

test("Account 360 brings every system together", async ({ page }) => {
  await signIn(page, "cro@revenueos.example");
  await page.getByRole("link", { name: "Accounts", exact: true }).click();
  const start = Date.now();
  await page.getByTestId("account-row").first().getByRole("link").click();
  await expect(page.getByText("Usage trend")).toBeVisible();
  console.log(`Account 360 visible after ${Date.now() - start} ms`);
  await expect(page.getByRole("heading", { name: "Deals" })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Tickets/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Invoices" })).toBeVisible();
  await page.getByRole("button", { name: /Open source/ }).first().click();
  await expect(page.getByRole("dialog")).toContainText("Source:");
});

test("a manager only sees their own team, and no Admin link", async ({ page }) => {
  await signIn(page, "manager1.emea@revenueos.example");
  await expect(page.getByText("Sales Manager · EMEA")).toBeVisible();
  await expect(page.getByRole("link", { name: "Admin" })).toHaveCount(0);
  await page.getByRole("link", { name: "Accounts", exact: true }).click();
  await expect(page.getByTestId("account-row").first()).toBeVisible();
  for (const row of await page.getByTestId("account-row").all()) {
    await expect(row.getByRole("cell").nth(2)).toHaveText("EMEA");
  }
});

test("theme toggle switches to dark mode", async ({ page }) => {
  await signIn(page, "cro@revenueos.example");
  await page.getByRole("button", { name: /Switch to dark mode/ }).click();
  await expect(page.locator("html")).toHaveClass(/dark/);
});
