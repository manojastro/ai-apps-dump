// File: src/core/types.ts
/**
 * Shared type contracts for the self-healing locator engine.
 * Keep this module dependency-free (types only) so it can be imported
 * from tests, page objects, reporters and CI scripts alike.
 */

/**
 * How an element was ultimately resolved.
 * - `primary`         : the selector authored in the Page Object worked as-is.
 * - `historical-map`  : a previously healed selector stored in `selector-history.json` worked.
 * - `fuzzy-dom`       : the AI/fuzzy matcher scored DOM candidates and picked a winner.
 * - `failed`          : all strategies exhausted (never persisted).
 */
export type FallbackStrategy = 'primary' | 'historical-map' | 'fuzzy-dom' | 'failed';

/** Strategies that produce a usable healed element. */
export type HealingStrategy = Exclude<FallbackStrategy, 'primary' | 'failed'>;

/**
 * Attributes the fuzzy matcher scores DOM candidates against.
 * Every field is optional; only provided fields participate in scoring
 * (weights are re-normalized across present fields).
 */
export interface ExpectedAttributes {
  /** Visible text expected on/near the element (e.g. button label). */
  text?: string;
  /** Expected `aria-label`. */
  ariaLabel?: string;
  /** Expected ARIA role (`button`, `textbox`, ...). */
  role?: string;
  /** Expected input `placeholder`. */
  placeholder?: string;
  /** Expected tag name (`input`, `button`, ...). */
  tagName?: string;
  /** Expected input `type` attribute (`password`, `submit`, ...). */
  inputType?: string;
}

/** A single interactive DOM candidate extracted by {@link inspectDomCandidates}. */
export interface DomCandidate {
  tag: string;
  id: string;
  classes: string[];
  /** Which attribute held the test id: `data-testid`, `data-test`, or null. */
  testIdAttr: string | null;
  /** The test id value itself. */
  testId: string | null;
  role: string | null;
  text: string;
  ariaLabel: string | null;
  placeholder: string | null;
  inputType: string | null;
}

/** A scored healing candidate produced by the fuzzy matcher. */
export interface CandidateScore {
  candidate: DomCandidate;
  /** Selector string that can be handed to `page.locator()`. */
  selector: string;
  /** Similarity score in `[0..1]`. */
  score: number;
}

/** One self-healing intervention, persisted for the HTML report. */
export interface HealEvent {
  id: string;
  timestamp: string;
  workerIndex: number;
  specFile: string;
  testTitle: string;
  /** Logical element identity used as the history key (e.g. `login.usernameInput`). */
  elementKey: string;
  primarySelector: string;
  healedSelector: string;
  strategy: HealingStrategy;
  /** Matcher confidence in `[0..1]`; `1` for proven historical selectors. */
  confidence: number;
  candidatesScanned: number;
  attemptsBeforeHeal: number;
  durationMs: number;
  originalError: string;
}

/** Per-locator configuration. */
export interface ResilientLocatorOptions {
  /** Human-readable intent, surfaced in logs and reports. */
  description?: string;
  /** Attributes for the fuzzy fallback; inferred from the selector when omitted. */
  expected?: ExpectedAttributes;
  /** Minimum similarity in `[0..1]` to accept a fuzzy match. Default `0.72`. */
  healThreshold?: number;
  /** Timeout applied while probing any single selector. Default `4000ms`. */
  probeTimeoutMs?: number;
  /** Hard-disable healing for this locator (strict mode for critical flows). */
  disableHealing?: boolean;
}

/** A healed selector record persisted inside the selector history map. */
export interface HealedSelectorRecord {
  selector: string;
  strategy: HealingStrategy;
  confidence: number;
  healedAt: string;
}

/** History entry for one logical element key. */
export interface SelectorHistoryEntry {
  key: string;
  /** Current best-known working selector. */
  current: string;
  /** Previously known-good selectors, newest first. */
  history: HealedSelectorRecord[];
}

/** Full on-disk shape of `selector-history.json`. */
export type SelectorHistoryMap = Record<string, SelectorHistoryEntry>;
