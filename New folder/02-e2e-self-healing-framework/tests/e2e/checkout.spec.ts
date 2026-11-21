// File: tests/e2e/checkout.spec.ts
/**
 * End-to-end purchase flow: add products, validate the cart, complete the
 * shipping form, verify price math on the review step, and confirm the order.
 * Every element interaction flows through the self-healing locator engine.
 */

import { expect, test } from '@playwright/test';
import { DashboardPage } from '../../src/pages/DashboardPage';
import { LoginPage } from '../../src/pages/LoginPage';

const STANDARD_USER = process.env.E2E_USERNAME ?? 'standard_user';
const PASSWORD = process.env.E2E_PASSWORD ?? 'secret_sauce';

/** Catalog prices used to verify subtotal math independently of the UI. */
const CATALOG_PRICES: Record<string, number> = {
  'Sauce Labs Backpack': 29.99,
  'Sauce Labs Bike Light': 9.99,
};

test.describe('Checkout', () => {
  let dashboard: DashboardPage;

  test.beforeEach(async ({ page }) => {
    const login = await new LoginPage(page).open();
    dashboard = await login.login(STANDARD_USER, PASSWORD);
    await dashboard.expectLoaded();
  });

  test('completes a two-item purchase end to end', async ({ page }) => {
    await dashboard.addItemToCart('Sauce Labs Backpack');
    await dashboard.addItemToCart('Sauce Labs Bike Light');
    expect(await dashboard.cartBadgeCount()).toBe(2);

    const checkout = await dashboard.openCart();
    await checkout.expectCartItemCount(2);
    await checkout.expectCartItemNames(['Sauce Labs Backpack', 'Sauce Labs Bike Light']);

    await checkout.startCheckout();
    await checkout.fillShippingDetails({ firstName: 'Ada', lastName: 'Lovelace', postalCode: '94040' });
    await checkout.continueToReview();

    const expectedSubtotal = CATALOG_PRICES['Sauce Labs Backpack'] + CATALOG_PRICES['Sauce Labs Bike Light'];
    const subtotal = await checkout.getSubtotalAmount();
    expect(subtotal).toBeCloseTo(expectedSubtotal, 2);

    const total = await checkout.getTotalAmount();
    expect(total).toBeGreaterThanOrEqual(subtotal);
    expect(total - subtotal).toBeLessThan(15); // sanity bound on computed tax

    await checkout.finishOrder();
    await checkout.expectOrderComplete();
    void page;
  });

  test('removing an item from the cart updates the badge', async ({ page }) => {
    await dashboard.addItemToCart('Sauce Labs Backpack');
    await dashboard.addItemToCart('Sauce Labs Bike Light');

    const checkout = await dashboard.openCart();
    await checkout.removeItem('Sauce Labs Bike Light');
    await checkout.expectCartItemCount(1);

    const backOnDashboard = await checkout.continueShopping();
    expect(await backOnDashboard.cartBadgeCount()).toBe(1);

    void page;
  });
});
