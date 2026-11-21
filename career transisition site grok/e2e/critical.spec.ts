import { test, expect } from "@playwright/test";

test("onboarding to dashboard", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("First run")).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Start Clean" }).click();
  await expect(page.getByText("AI Career Transition — 2026")).toBeVisible();
});

test("skill persists across refresh", async ({ page }) => {
  await page.goto("/");
  if (await page.getByText("First run").isVisible()) {
    for (let i = 0; i < 5; i += 1) await page.getByRole("button", { name: "Continue" }).click();
    await page.getByRole("button", { name: "Start Clean" }).click();
  }
  await page.goto("/skills");
  await page.getByRole("button", { name: "Add Skill" }).click();
  await page.getByLabel("Name").fill("LangGraph");
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText("LangGraph")).toBeVisible();
  await page.reload();
  await expect(page.getByText("LangGraph")).toBeVisible();
});
