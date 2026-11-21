// File: src/core/ResilientLocator.ts
/**
 * The self-healing locator engine.
 *
 * `ResilientLocator` wraps a Playwright `Page` + selector pair and resolves it
 * through a cascading strategy chain:
 *
 *   1. PRIMARY      - the authored selector (fast path, no overhead on green runs).
 *   2. HISTORY      - previously healed selectors from `selector-history.json`
 *                     (instant recovery for known renames, even across workers/runs).
 *   3. FUZZY-DOM    - inspect live DOM candidates and score them against expected
 *                     attributes with Levenshtein/token similarity; probe the best
 *                     matches; persist the winner back to history for next time.
 *
 * Every intervention emits a structured {@link HealEvent} (consumed by the
 * HealingReporter) plus a console warning, so healing is always observable —
 * never silent.
 */

import path from 'node:path';
import { test, type Locator, type Page } from '@playwright/test';
import { collectDomCandidates } from './healing/domInspector';
import { DEFAULT_HEAL_THRESHOLD, rankCandidates } from './healing/fuzzyMatcher';
import { appendHealEvent, createHealEvent } from './healEventStore';
import { loadHistory, lookupHistoricalSelectors, recordHealedSelector } from './selectorHistory';
import type {
  ExpectedAttributes,
  FallbackStrategy,
  HealEvent,
  HealingStrategy,
  ResilientLocatorOptions,
} from './types';

const DEFAULT_PROBE_TIMEOUT_MS = 4_000;
const DEFAULT_INTERACTION_TIMEOUT_MS = 10_000;

/** Result of resolving an element through the cascade. */
export interface ResolvedTarget {
  locator: Locator;
  /** Selector that actually matched. */
  selectorUsed: string;
  healed: boolean;
  strategy: FallbackStrategy;
}

interface TestContextInfo {
  specFile: string;
  testTitle: string;
  workerIndex: number;
}

function getTestContext(): TestContextInfo {
  try {
    const info = test.info();
    return {
      specFile: info.file ? path.basename(info.file) : 'unknown.spec.ts',
      testTitle: info.title,
      workerIndex: info.workerIndex,
    };
  } catch {
    // Called outside a running test (e.g. debugging scripts).
    return { specFile: 'unknown', testTitle: 'unknown', workerIndex: -1 };
  }
}

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function toError(error: unknown): Error {
  return error instanceof Error ? error : new Error(describeError(error));
}

function humanizeToken(value: string): string {
  return value
    .replace(/^add-to-cart-|^remove-/, '')
    .replace(/[-_]+/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .trim();
}

/**
 * Derive fuzzy-matching expectations directly from an authored selector.
 * Used when a Page Object does not supply explicit `expected` attributes:
 * `[data-test="login-button"]` yields `{ text: "login button" }`, quoted
 * text engines yield their literal text, and so on.
 */
export function inferExpectedAttributes(selector: string): ExpectedAttributes {
  const expected: ExpectedAttributes = {};

  const ariaLabel = /\[aria-label="([^"]+)"\]/.exec(selector)?.[1];
  if (ariaLabel) expected.ariaLabel = ariaLabel;

  const role = /\[role="([^"]+)"\]/.exec(selector)?.[1];
  if (role) expected.role = role;

  const placeholder = /\[placeholder="([^"]+)"\]/.exec(selector)?.[1];
  if (placeholder) expected.placeholder = placeholder;

  const quotedText = /text=("([^"]*)"|'([^']*)')/.exec(selector);
  const textValue = quotedText?.[2] ?? quotedText?.[3];
  if (textValue !== undefined && textValue.length > 0) expected.text = textValue;

  const stableAnchor =
    /\[data-(?:testid|test)="([^"]+)"\]/.exec(selector)?.[1] ?? /(?:^|\s)#([A-Za-z][\w-]*)/.exec(selector)?.[1];
  if (stableAnchor !== undefined && expected.text === undefined) {
    expected.text = humanizeToken(stableAnchor);
  }

  return expected;
}

export class ResilientLocator {
  private resolvedSelector?: string;

  constructor(
    private readonly page: Page,
    private readonly elementKey: string,
    private readonly primarySelector: string,
    private readonly options: ResilientLocatorOptions = {},
  ) {}

  /** Logical identity of this element (also the history-map key). */
  public get elementName(): string {
    return this.elementKey;
  }

  /** The authored selector. */
  public get authoredSelector(): string {
    return this.primarySelector;
  }

  /** Best-known working selector (authored until a heal occurs). */
  public get currentSelector(): string {
    return this.resolvedSelector ?? this.primarySelector;
  }

  // ------------------------------------------------------------------ //
  // Element interactions (each routes through the healing cascade)
  // ------------------------------------------------------------------ //

  public async click(interaction: { timeoutMs?: number } = {}): Promise<void> {
    const { locator } = await this.resolve();
    await locator.click({ timeout: interaction.timeoutMs ?? DEFAULT_INTERACTION_TIMEOUT_MS });
  }

  public async fill(value: string, interaction: { timeoutMs?: number } = {}): Promise<void> {
    const { locator } = await this.resolve();
    await locator.fill(value, { timeout: interaction.timeoutMs ?? DEFAULT_INTERACTION_TIMEOUT_MS });
  }

  public async press(key: string, interaction: { timeoutMs?: number } = {}): Promise<void> {
    const { locator } = await this.resolve();
    await locator.press(key, { timeout: interaction.timeoutMs ?? DEFAULT_INTERACTION_TIMEOUT_MS });
  }

  public async textContent(interaction: { timeoutMs?: number } = {}): Promise<string> {
    const { locator } = await this.resolve();
    const value = await locator.textContent({ timeout: interaction.timeoutMs ?? DEFAULT_INTERACTION_TIMEOUT_MS });
    return value ?? '';
  }

  public async inputValue(interaction: { timeoutMs?: number } = {}): Promise<string> {
    const { locator } = await this.resolve();
    return locator.inputValue({ timeout: interaction.timeoutMs ?? DEFAULT_INTERACTION_TIMEOUT_MS });
  }

  /**
   * Cheap visibility check against the best-known selector.
   * Deliberately does NOT trigger the healing scan (healing is reserved for
   * real interaction failures, keeping assertions fast).
   */
  public async isVisible(): Promise<boolean> {
    try {
      return await this.page.locator(this.currentSelector).first().isVisible();
    } catch {
      return false;
    }
  }

  public async waitFor(
    state: 'attached' | 'detached' | 'visible' | 'hidden' = 'visible',
    interaction: { timeoutMs?: number } = {},
  ): Promise<void> {
    const { locator } = await this.resolve();
    await locator.waitFor({ state, timeout: interaction.timeoutMs ?? DEFAULT_INTERACTION_TIMEOUT_MS });
  }

  // ------------------------------------------------------------------ //
  // Resolution cascade
  // ------------------------------------------------------------------ //

  /**
   * Resolve through primary -> historical map -> fuzzy DOM matching.
   * Throws an enriched error when every strategy fails.
   */
  public async resolve(): Promise<ResolvedTarget> {
    const startedAt = Date.now();
    const primaryError = await this.probe(this.currentSelector);

    if (primaryError === null) {
      const healed = this.resolvedSelector !== undefined && this.resolvedSelector !== this.primarySelector;
      return { locator: this.toLocator(this.currentSelector), selectorUsed: this.currentSelector, healed, strategy: 'primary' };
    }

    if (this.options.disableHealing === true) throw primaryError;

    const viaHistory = await this.attemptHistoricalHealing(startedAt, primaryError);
    if (viaHistory !== null) return viaHistory;

    const viaFuzzy = await this.attemptFuzzyHealing(startedAt, primaryError);
    if (viaFuzzy !== null) return viaFuzzy;

    throw new Error(
      [
        `[self-healing] unable to locate element "${this.elementKey}" (${this.options.description ?? 'no description'}).`,
        `  primary selector : ${this.primarySelector}`,
        `  strategies tried : primary, historical-map, fuzzy-dom`,
        `  original error   : ${primaryError.message}`,
      ].join('\n'),
      { cause: primaryError },
    );
  }

  /** Probe one selector; resolve to `null` when visible within the probe timeout. */
  private async probe(selector: string): Promise<Error | null> {
    const timeout = this.options.probeTimeoutMs ?? DEFAULT_PROBE_TIMEOUT_MS;
    try {
      await this.page.locator(selector).first().waitFor({ state: 'visible', timeout });
      return null;
    } catch (error: unknown) {
      return toError(error);
    }
  }

  private toLocator(selector: string): Locator {
    return this.page.locator(selector).first();
  }

  /** Strategy 2: replay selectors that healed this element in previous runs. */
  private async attemptHistoricalHealing(startedAt: number, primaryError: Error): Promise<ResolvedTarget | null> {
    const history = await loadHistory();
    const candidates = lookupHistoricalSelectors(history, this.elementKey).filter(
      (selector) => selector !== this.primarySelector && selector !== this.resolvedSelector,
    );

    for (const candidateSelector of candidates) {
      if ((await this.probe(candidateSelector)) !== null) continue;
      this.resolvedSelector = candidateSelector;
      await this.emitHealEvent({
        healedSelector: candidateSelector,
        strategy: 'historical-map',
        confidence: 1,
        candidatesScanned: candidates.length,
        startedAt,
        originalError: primaryError,
      });
      return { locator: this.toLocator(candidateSelector), selectorUsed: candidateSelector, healed: true, strategy: 'historical-map' };
    }
    return null;
  }

  /** Strategy 3: score live DOM candidates with the fuzzy matcher and adopt the best. */
  private async attemptFuzzyHealing(startedAt: number, primaryError: Error): Promise<ResolvedTarget | null> {
    const threshold = this.options.healThreshold ?? DEFAULT_HEAL_THRESHOLD;
    const expected = this.options.expected ?? inferExpectedAttributes(this.primarySelector);

    const allCandidates = await collectDomCandidates(this.page);
    const ranked = rankCandidates(expected, allCandidates, threshold);

    for (const scored of ranked) {
      if ((await this.probe(scored.selector)) !== null) continue;

      this.resolvedSelector = scored.selector;
      await recordHealedSelector(this.elementKey, {
        selector: scored.selector,
        strategy: 'fuzzy-dom',
        confidence: scored.score,
        healedAt: new Date().toISOString(),
      });
      await this.emitHealEvent({
        healedSelector: scored.selector,
        strategy: 'fuzzy-dom',
        confidence: scored.score,
        candidatesScanned: allCandidates.length,
        startedAt,
        originalError: primaryError,
      });
      return { locator: this.toLocator(scored.selector), selectorUsed: scored.selector, healed: true, strategy: 'fuzzy-dom' };
    }
    return null;
  }

  /** Persist a heal event for the reporter and surface a loud console warning. */
  private async emitHealEvent(payload: {
    healedSelector: string;
    strategy: HealingStrategy;
    confidence: number;
    candidatesScanned: number;
    startedAt: number;
    originalError: Error;
  }): Promise<void> {
    const context = getTestContext();
    const event: HealEvent = createHealEvent({
      workerIndex: context.workerIndex,
      specFile: context.specFile,
      testTitle: context.testTitle,
      elementKey: this.elementKey,
      primarySelector: this.primarySelector,
      healedSelector: payload.healedSelector,
      strategy: payload.strategy,
      confidence: payload.confidence,
      candidatesScanned: payload.candidatesScanned,
      attemptsBeforeHeal: 1,
      durationMs: Date.now() - payload.startedAt,
      originalError: describeError(payload.originalError),
    });

    await appendHealEvent(event);
    console.warn(
      `[self-healing] "${this.elementKey}" healed: "${this.primarySelector}" -> "${payload.healedSelector}" ` +
        `(strategy=${payload.strategy}, confidence=${payload.confidence.toFixed(3)}, ${event.durationMs}ms)`,
    );
  }
}
