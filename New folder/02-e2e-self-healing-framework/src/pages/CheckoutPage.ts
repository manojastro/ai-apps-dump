// File: src/pages/CheckoutPage.ts
/**
 * Cart + checkout flow page object (SauceDemo cart -> checkout-step-one ->
 * checkout-step-two -> checkout-complete). Covers quantity assertions,
 * item removal, shipping form fill, price math and order confirmation.
 */

import { expect, type Page } from '@playwright/test';
import { BasePage } from './BasePage';
import type { InteractionOptions } from './BasePage';
import { DashboardPage } from './DashboardPage';

export const CHECKOUT_SELECTORS = {
  cartItem: '[data-test="cart-item"]',
  itemName: '[data-test="inventory-item-name"]',
  continueShoppingButton: '[data-test="continue-shopping"]',
  removeButtonTemplate: 'button[data-test="remove-{slug}"]',
  checkoutButton: '[data-test="checkout"]',
  firstNameInput: '[data-test="firstName"]',
  lastNameInput: '[data-test="lastName"]',
  postalCodeInput: '[data-test="postalCode"]',
  continueButton: '[data-test="continue"]',
  subtotalLabel: '[data-test="subtotal-label"]',
  taxLabel: '[data-test="tax-label"]',
  totalLabel: '[data-test="total-label"]',
  finishButton: '[data-test="finish"]',
  completeHeader: '[data-test="complete-header"]',
} as const;

export interface ShippingDetails {
  firstName: string;
  lastName: string;
  postalCode: string;
}

/** Extract the first monetary amount from text like "Item total: $39.98". */
function parseMoney(raw: string): number {
  const match = /(-?\d[\d,]*(?:\.\d+)?)/.exec(raw);
  if (match === null) return 0;
  return Number.parseFloat(match[1].replace(/,/g, ''));
}

/** Convert a product name into its test-id slug (`Sauce Labs Backpack` -> `sauce-labs-backpack`). */
function toSlug(productName: string): string {
  return productName.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

export class CheckoutPage extends BasePage {
  private readonly continueShoppingButton = this.resilient(
    'checkout.continueShoppingButton',
    CHECKOUT_SELECTORS.continueShoppingButton,
    { description: 'Continue shopping button on the cart page', expected: { text: 'Continue Shopping', role: 'button' } },
  );

  private readonly checkoutButton = this.resilient('checkout.checkoutButton', CHECKOUT_SELECTORS.checkoutButton, {
    description: 'Checkout button on the cart page',
    expected: { text: 'Checkout', role: 'button' },
  });

  private readonly continueButton = this.resilient('checkout.continueButton', CHECKOUT_SELECTORS.continueButton, {
    description: 'Continue button on the shipping form',
    expected: { text: 'Continue', role: 'button' },
  });

  private readonly finishButton = this.resilient('checkout.finishButton', CHECKOUT_SELECTORS.finishButton, {
    description: 'Finish order button on the review step',
    expected: { text: 'Finish', role: 'button' },
  });

  constructor(page: Page) {
    super(page);
  }

  /** Assert exactly `expected` items sit in the cart. */
  public async expectCartItemCount(expected: number): Promise<void> {
    await expect(this.page.locator(CHECKOUT_SELECTORS.cartItem)).toHaveCount(expected);
  }

  /** Assert the listed product names match (order-insensitive). */
  public async expectCartItemNames(expected: string[]): Promise<void> {
    const actual = (await this.page.locator(CHECKOUT_SELECTORS.itemName).allInnerTexts()).sort();
    expect(actual).toEqual([...expected].sort());
  }

  /** Remove one product from the cart via its per-item remove button. */
  public async removeItem(productName: string, options: InteractionOptions = {}): Promise<void> {
    const selector = CHECKOUT_SELECTORS.removeButtonTemplate.replace('{slug}', toSlug(productName));
    await this.clickWithHealing(`checkout.remove.${toSlug(productName)}`, selector, {
      description: `Remove "${productName}" from cart`,
      expected: { text: 'Remove', role: 'button' },
      ...options,
    });
  }

  /** Leave the cart back to the catalog; returns a fresh dashboard object. */
  public async continueShopping(): Promise<DashboardPage> {
    await this.continueShoppingButton.click();
    const dashboard = new DashboardPage(this.page);
    await dashboard.expectLoaded();
    return dashboard;
  }

  /** Proceed from the cart to the shipping-information step. */
  public async startCheckout(): Promise<void> {
    await this.checkoutButton.click();
    await expect(this.page).toHaveURL(/checkout-step-one\.html$/);
  }

  /** Fill buyer details with healing enabled per field. */
  public async fillShippingDetails(details: ShippingDetails): Promise<void> {
    await this.fillWithHealing('checkout.firstNameInput', details.firstName, CHECKOUT_SELECTORS.firstNameInput, {
      description: 'First name input',
      expected: { placeholder: 'First Name' },
    });
    await this.fillWithHealing('checkout.lastNameInput', details.lastName, CHECKOUT_SELECTORS.lastNameInput, {
      description: 'Last name input',
      expected: { placeholder: 'Last Name' },
    });
    await this.fillWithHealing('checkout.postalCodeInput', details.postalCode, CHECKOUT_SELECTORS.postalCodeInput, {
      description: 'Zip/postal code input',
      expected: { placeholder: 'Zip/Postal Code' },
    });
  }

  /** Submit shipping details and land on the order-review step. */
  public async continueToReview(): Promise<void> {
    await this.continueButton.click();
    await expect(this.page).toHaveURL(/checkout-step-two\.html$/);
  }

  /** Item subtotal shown on the review step. */
  public async getSubtotalAmount(): Promise<number> {
    return parseMoney(await this.textWithHealing('checkout.subtotalLabel', CHECKOUT_SELECTORS.subtotalLabel));
  }

  /** Sales tax shown on the review step. */
  public async getTaxAmount(): Promise<number> {
    return parseMoney(await this.textWithHealing('checkout.taxLabel', CHECKOUT_SELECTORS.taxLabel));
  }

  /** Grand total (subtotal + tax) shown on the review step. */
  public async getTotalAmount(): Promise<number> {
    return parseMoney(await this.textWithHealing('checkout.totalLabel', CHECKOUT_SELECTORS.totalLabel));
  }

  /** Place the order and land on the confirmation screen. */
  public async finishOrder(): Promise<void> {
    await this.finishButton.click();
    await expect(this.page).toHaveURL(/checkout-complete\.html$/);
  }

  /** Assert the canonical success banner is displayed. */
  public async expectOrderComplete(): Promise<void> {
    await expect(this.page.locator(CHECKOUT_SELECTORS.completeHeader)).toHaveText('Thank you for your order!');
  }
}
