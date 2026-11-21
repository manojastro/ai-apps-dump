// File: tests/e2e/auth.spec.ts
/**
 * Authentication flows exercised through the healing-enabled page objects:
 * happy path, locked-out account, bad credentials, and session teardown.
 */

import { expect, test } from '@playwright/test';
import { DashboardPage } from '../../src/pages/DashboardPage';
import { LoginPage } from '../../src/pages/LoginPage';

const STANDARD_USER = process.env.E2E_USERNAME ?? 'standard_user';
const LOCKED_USER = process.env.E2E_LOCKED_USER ?? 'locked_out_user';
const PASSWORD = process.env.E2E_PASSWORD ?? 'secret_sauce';

test.describe('Authentication', () => {
  test('valid credentials land on the product catalog', async ({ page }) => {
    const login = await new LoginPage(page).open();
    await login.login(STANDARD_USER, PASSWORD);

    const dashboard = new DashboardPage(page);
    await dashboard.expectLoaded();
    await expect(page).toHaveURL(/inventory\.html$/);

    const products = await dashboard.getItemNames();
    expect(products.length).toBeGreaterThan(0);

    const loggedOut = await dashboard.logout();
    await expect(page).toHaveURL(/\/$/);
    void loggedOut;
  });

  test('locked-out account receives an explanatory error', async ({ page }) => {
    const login = await new LoginPage(page).open();
    const message = await login.loginExpectingError(LOCKED_USER, PASSWORD);
    expect(message.toLowerCase()).toContain('sorry, this user has been locked out');
    await expect(page).not.toHaveURL(/inventory\.html$/);
  });

  test('wrong password is rejected with a generic error', async ({ page }) => {
    const login = await new LoginPage(page).open();
    await login.login(STANDARD_USER, 'definitely-wrong-password');
    await login.expectErrorContains('do not match any user in this service');
    await expect(page).toHaveURL(/\/$/);
  });
});
