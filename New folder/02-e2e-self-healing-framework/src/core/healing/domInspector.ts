// File: src/core/healing/domInspector.ts
/**
 * Browser-side candidate extraction for the fuzzy healing fallback.
 * Runs a single `page.evaluate` pass over interactive elements and returns a
 * serializable snapshot of everything the matcher needs to score candidates.
 */

import type { Page } from '@playwright/test';
import type { DomCandidate } from '../types';

const TARGETED_ELEMENTS_SELECTOR = [
  'a',
  'button',
  'input',
  'select',
  'textarea',
  'label',
  '[role]',
  '[data-testid]',
  '[data-test]',
].join(',');

/** Upper bound on returned candidates; keeps healing latency predictable. */
export const DEFAULT_MAX_CANDIDATES = 500;

export interface DomInspectionOptions {
  /** Maximum candidates to return (default {@link DEFAULT_MAX_CANDIDATES}). */
  maxCandidates?: number;
}

interface SerializedCandidate {
  tag: string;
  id: string;
  classes: string[];
  testIdAttr: string | null;
  testId: string | null;
  role: string | null;
  text: string;
  ariaLabel: string | null;
  placeholder: string | null;
  inputType: string | null;
}

/**
 * Collect visible, interactive DOM candidates from the current page.
 * Hidden elements are skipped up-front so the matcher never heals onto an
 * invisible twin. The evaluate callback is intentionally self-contained
 * (no closure capture) so it survives Playwright serialization.
 */
export async function collectDomCandidates(page: Page, options: DomInspectionOptions = {}): Promise<DomCandidate[]> {
  const maxCandidates = options.maxCandidates ?? DEFAULT_MAX_CANDIDATES;

  const serialized = await page.evaluate((max: number): SerializedCandidate[] => {
    const collapseWhitespace = (value: string): string => value.replace(/\s+/g, ' ').trim();

    const results: SerializedCandidate[] = [];
    const elements = Array.from(document.querySelectorAll<HTMLElement>(TARGETED_ELEMENTS_SELECTOR));

    for (const element of elements) {
      if (results.length >= max) break;

      const style = window.getComputedStyle(element);
      if (style.display === 'none' || style.visibility === 'hidden') continue;
      const rect = element.getBoundingClientRect();
      if (rect.width === 0 && rect.height === 0) continue;

      const testIdAttribute =
        element.getAttribute('data-testid') !== null
          ? 'data-testid'
          : element.getAttribute('data-test') !== null
            ? 'data-test'
            : null;

      const rawText = (element.innerText || element.textContent || '').slice(0, 200);

      results.push({
        tag: element.tagName.toLowerCase(),
        id: typeof element.id === 'string' ? element.id : '',
        classes: typeof element.className === 'string' ? element.className.split(/\s+/).filter(Boolean).slice(0, 6) : [],
        testIdAttr: testIdAttribute,
        testId: testIdAttribute === null ? null : element.getAttribute(testIdAttribute),
        role: element.getAttribute('role'),
        text: collapseWhitespace(rawText),
        ariaLabel: element.getAttribute('aria-label'),
        placeholder: element.getAttribute('placeholder'),
        inputType: element.getAttribute('type'),
      });
    }
    return results;
  }, maxCandidates);

  return serialized.map((raw): DomCandidate => ({ ...raw }));
}
