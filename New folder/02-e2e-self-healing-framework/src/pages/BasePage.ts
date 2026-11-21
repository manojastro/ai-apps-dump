// File: src/pages/BasePage.ts
/**
 * Base Page Object.
 * All page objects extend this class and route element access through the
 * self-healing locator engine via {@link resilient} and the `*WithHealing`
 * helpers, so every page inherits healing with zero extra wiring.
 */

import { expect, type Page } from '@playwright/test';
import { ResilientLocator } from '../core/ResilientLocator';
import type { ResilientLocatorOptions } from '../core/types';

/** Locator options plus an optional interaction timeout override. */
export interface InteractionOptions extends ResilientLocatorOptions {
  timeoutMs?: number;
}

export abstract class BasePage {
  protected readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Create a self-healing locator bound to this page.
   * @param elementKey Stable logical identity (used as the selector-history key),
   *                   e.g. `login.usernameInput`.
   * @param selector   Authored primary selector.
   */
  public resilient(elementKey: string, selector: string, options: ResilientLocatorOptions = {}): ResilientLocator {
    return new ResilientLocator(this.page, elementKey, selector, options);
  }

  /** Click an element through the healing cascade. */
  public async clickWithHealing(elementKey: string, selector: string, options: InteractionOptions = {}): Promise<void> {
    const { timeoutMs, ...locatorOptions } = options;
    await this.resilient(elementKey, selector, locatorOptions).click({ timeoutMs });
  }

  /** Fill a form control through the healing cascade. */
  public async fillWithHealing(
    elementKey: string,
    value: string,
    selector: string,
    options: InteractionOptions = {},
  ): Promise<void> {
    const { timeoutMs, ...locatorOptions } = options;
    await this.resilient(elementKey, selector, locatorOptions).fill(value, { timeoutMs });
  }

  /** Read visible text through the healing cascade. */
  public async textWithHealing(elementKey: string, selector: string, options: InteractionOptions = {}): Promise<string> {
    const { timeoutMs, ...locatorOptions } = options;
    return this.resilient(elementKey, selector, locatorOptions).textContent({ timeoutMs });
  }

  /** Resolve through the cascade, then assert visibility with standard expect(). */
  public async expectVisibleWithHealing(
    elementKey: string,
    selector: string,
    options: ResilientLocatorOptions = {},
  ): Promise<void> {
    const { locator } = await this.resilient(elementKey, selector, options).resolve();
    await expect(locator).toBeVisible();
  }

  /** Navigate relative to the configured `baseURL`. */
  protected async navigate(pathname: string): Promise<void> {
    await this.page.goto(pathname, { waitUntil: 'domcontentloaded' });
  }
}
