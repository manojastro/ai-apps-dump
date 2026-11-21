// File: src/pages/LoginPage.ts
/**
 * Authentication page object (SauceDemo login screen).
 * Fields route through the self-healing engine with explicit expected
 * attributes, so a renamed test id is recovered automatically.
 */

import { expect, type Page } from '@playwright/test';
import { BasePage } from './BasePage';
import type { InteractionOptions } from './BasePage';
import { DashboardPage } from './DashboardPage';

export const LOGIN_SELECTORS = {
  usernameInput: '[data-test="username"]',
  passwordInput: '[data-test="password"]',
  loginButton: '[data-test="login-button"]',
  errorMessage: '[data-test="error"]',
} as const;

export class LoginPage extends BasePage {
  private readonly usernameInput = this.resilient('login.usernameInput', LOGIN_SELECTORS.usernameInput, {
    description: 'Username text input',
    expected: { placeholder: 'Username', role: 'textbox', tagName: 'input' },
  });

  private readonly passwordInput = this.resilient('login.passwordInput', LOGIN_SELECTORS.passwordInput, {
    description: 'Password text input',
    expected: { placeholder: 'Password', inputType: 'password', tagName: 'input' },
  });

  private readonly loginButton = this.resilient('login.loginButton', LOGIN_SELECTORS.loginButton, {
    description: 'Login submit button',
    expected: { text: 'Login', role: 'button' },
  });

  constructor(page: Page) {
    super(page);
  }

  /** Open the login screen (app root). */
  public async open(): Promise<this> {
    await this.navigate('/');
    return this;
  }

  /** Submit credentials; resolves once the post-login navigation settles. */
  public async login(username: string, password: string): Promise<DashboardPage> {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
    return new DashboardPage(this.page);
  }

  /** Attempt a login and expect an inline error; returns the message text. */
  public async loginExpectingError(username: string, password: string, options: InteractionOptions = {}): Promise<string> {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.loginButton.click(options);
    const alert = this.resilient('login.errorMessage', LOGIN_SELECTORS.errorMessage, {
      description: 'Inline authentication error banner',
      expected: { role: 'alert' },
    });
    await alert.waitFor('visible');
    const message = await alert.textContent();
    expect(message.trim().length).toBeGreaterThan(0);
    return message;
  }

  /** Assert the inline error banner contains `fragment` (case-insensitive). */
  public async expectErrorContains(fragment: string): Promise<void> {
    const message = await this.textWithHealing('login.errorMessage', LOGIN_SELECTORS.errorMessage, {
      description: 'Inline authentication error banner',
    });
    expect(message.toLowerCase()).toContain(fragment.toLowerCase());
  }
}
