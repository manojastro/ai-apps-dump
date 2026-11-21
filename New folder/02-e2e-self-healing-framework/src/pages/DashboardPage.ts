// File: src/pages/DashboardPage.ts
/**
 * Product-catalog dashboard page object (SauceDemo inventory page).
 * Demonstrates healing-friendly dynamic selectors built from domain data
 * (item names) instead of brittle positional indexes.
 */

import { expect, type Page } from '@playwright/test';
import { BasePage } from './BasePage';
import { CheckoutPage } from './CheckoutPage';
import { LoginPage } from './LoginPage';

export const DASHBOARD_SELECTORS = {
  titleLabel: '[data-test="title"]',
  inventoryItem: '[data-test="inventory-item"]',
  itemName: '[data-test="inventory-item-name"]',
  cartBadge: '[data-test="shopping-cart-badge"]',
  cartLink: '[data-test="shopping-cart-link"]',
  burgerMenuButton: '#react-burger-menu-btn',
  logoutLink: '#logout_sidebar_link',
} as const;

/** Convert a product name into its URL/test-id slug (`Sauce Labs Backpack` -> `sauce-labs-backpack`). */
function toSlug(productName: string): string {
  return productName.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

export class DashboardPage extends BasePage {
  private readonly cartLink = this.resilient('dashboard.cartLink', DASHBOARD_SELECTORS.cartLink, {
    description: 'Shopping cart icon/link in the header',
    expected: { ariaLabel: 'Shopping Cart' },
  });

  private readonly burgerMenuButton = this.resilient('dashboard.burgerMenuButton', DASHBOARD_SELECTORS.burgerMenuButton, {
    description: 'Hamburger menu button',
    expected: { ariaLabel: 'Open Menu' },
  });

  constructor(page: Page) {
    super(page);
  }

  /** Assert the catalog finished loading. */
  public async expectLoaded(): Promise<void> {
    await expect(this.page.locator(DASHBOARD_SELECTORS.titleLabel)).toHaveText('Products');
  }

  /** Add a specific product to the cart via its scoped add-to-cart button. */
  public async addItemToCart(productName: string): Promise<void> {
    const selector = `${DASHBOARD_SELECTORS.inventoryItem}:has-text("${productName}") button[data-test^="add-to-cart"]`;
    await this.clickWithHealing(`dashboard.addToCart.${toSlug(productName)}`, selector, {
      description: `Add "${productName}" to cart`,
      expected: { text: 'Add to cart', role: 'button' },
    });
  }

  /** Read the header cart badge count (0 when the badge is absent). */
  public async cartBadgeCount(): Promise<number> {
    const badge = this.page.locator(DASHBOARD_SELECTORS.cartBadge);
    if ((await badge.count()) === 0) return 0;
    const raw = await badge.first().textContent();
    const parsed = Number.parseInt(raw?.trim() ?? '', 10);
    return Number.isNaN(parsed) ? 0 : parsed;
  }

  /** Names of every product currently listed on the dashboard. */
  public async getItemNames(): Promise<string[]> {
    return this.page.locator(DASHBOARD_SELECTORS.itemName).allInnerTexts();
  }

  /** Open the shopping cart; returns the cart-scoped checkout page object. */
  public async openCart(): Promise<CheckoutPage> {
    await this.cartLink.click();
    return new CheckoutPage(this.page);
  }

  /** Log out through the burger menu; returns to a fresh LoginPage. */
  public async logout(): Promise<LoginPage> {
    await this.burgerMenuButton.click();
    const logoutLink = this.resilient('dashboard.logoutLink', DASHBOARD_SELECTORS.logoutLink, {
      description: 'Sidebar logout link',
      expected: { text: 'Logout' },
    });
    await logoutLink.waitFor('visible');
    await logoutLink.click();
    return new LoginPage(this.page);
  }
}
