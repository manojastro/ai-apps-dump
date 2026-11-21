import { test, expect } from '@playwright/test';

test('dashboard starts a deterministic run and opens details', async ({ page }) => {
  await page.goto('http://localhost:3004');
  await expect(page.getByText('Ship agents with')).toBeVisible();
  await page.getByRole('button', { name: 'Run evaluation' }).first().click();
  await expect(page.getByText('EXPERIMENT RUN')).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText('TASK SUCCESS')).toBeVisible();
});

test('API documentation is reachable', async ({ request }) => {
  expect((await request.get('http://localhost:8004/openapi.json')).ok()).toBeTruthy();
});

test('seeded dataset is visible in the overview', async ({ page }) => {
  await page.goto('http://localhost:3004');
  await expect(page.getByText('GOLDEN CASES')).toBeVisible();
  await expect(page.getByText('Coverage mix')).toBeVisible();
});

