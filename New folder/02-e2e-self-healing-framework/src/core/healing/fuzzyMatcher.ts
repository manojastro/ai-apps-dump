// File: src/core/healing/fuzzyMatcher.ts
/**
 * Pure, deterministic scoring primitives powering the AI-based healing fallback.
 * No Playwright, no I/O — every function here is trivially unit-testable.
 *
 * Scoring model:
 *   Each expected attribute contributes a weighted term; only attributes the
 *   caller actually provided participate, and weights are re-normalized over
 *   those present so a sparse expectation never drags scores down.
 */

import type { CandidateScore, DomCandidate, ExpectedAttributes } from '../types';

/** Default minimum similarity required to accept a fuzzy match. */
export const DEFAULT_HEAL_THRESHOLD = 0.72;

/** Hard cap on ranked candidates probed after scoring (cost guard). */
export const MAX_RANKED_CANDIDATES = 5;

/** Relative importance of each scored dimension. */
export interface SimilarityWeights {
  text: number;
  ariaLabel: number;
  role: number;
  placeholder: number;
}

export const DEFAULT_WEIGHTS: SimilarityWeights = {
  text: 0.42,
  ariaLabel: 0.28,
  role: 0.16,
  placeholder: 0.14,
};

function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value));
}

function round3(value: number): number {
  return Math.round(value * 1000) / 1000;
}

/** Lowercase, collapse whitespace, trim. */
export function normalizeText(input: string): string {
  return input.replace(/\s+/g, ' ').trim().toLowerCase();
}

/** Split into lowercase alphanumeric tokens (`Add to cart` -> [add,to,cart]). */
export function tokenize(input: string): string[] {
  return normalizeText(input)
    .split(/[^a-z0-9]+/)
    .filter(Boolean);
}

/**
 * Classic Levenshtein edit distance using two rolling rows (O(n*m) time,
 * O(m) space).
 */
export function levenshteinDistance(a: string, b: string): number {
  if (a === b) return 0;
  if (a.length === 0) return b.length;
  if (b.length === 0) return a.length;

  let previous = new Array<number>(b.length + 1);
  let current = new Array<number>(b.length + 1);
  for (let j = 0; j <= b.length; j++) previous[j] = j;

  for (let i = 1; i <= a.length; i++) {
    current[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const substitutionCost = a.charCodeAt(i - 1) === b.charCodeAt(j - 1) ? 0 : 1;
      current[j] = Math.min(
        previous[j] + 1, // deletion
        current[j - 1] + 1, // insertion
        previous[j - 1] + substitutionCost, // substitution
      );
    }
    const swap = previous;
    previous = current;
    current = swap;
  }
  return previous[b.length];
}

/** Edit distance normalized to a `[0..1]` similarity (1 = identical). */
export function normalizedLevenshtein(a: string, b: string): number {
  const longest = Math.max(a.length, b.length);
  if (longest === 0) return 1;
  return clamp01(1 - levenshteinDistance(a, b) / longest);
}

/** Jaccard similarity over token sets (`[0..1]`). */
export function tokenSimilarity(a: string, b: string): number {
  const tokensA = new Set(tokenize(a));
  const tokensB = new Set(tokenize(b));
  if (tokensA.size === 0 && tokensB.size === 0) return 1;
  if (tokensA.size === 0 || tokensB.size === 0) return 0;

  let intersection = 0;
  for (const token of tokensA) if (tokensB.has(token)) intersection++;
  const union = tokensA.size + tokensB.size - intersection;
  return union === 0 ? 0 : intersection / union;
}

/**
 * Blended textual similarity taking the best of two signals:
 * - character level (normalized Levenshtein) catches typos and renames like
 *   `Usename` -> `Username`;
 * - word level (token Jaccard, lightly anchored to character similarity)
 *   catches reorderings like `Cart Shopping` -> `Shopping Cart`.
 */
export function textSimilarity(a: string, b: string): number {
  const left = normalizeText(a);
  const right = normalizeText(b);
  if (left === right) return 1;
  if (left.length === 0 || right.length === 0) return 0;
  const levenshtein = normalizedLevenshtein(left, right);
  const tokens = tokenSimilarity(left, right);
  return clamp01(Math.max(levenshtein, 0.85 * tokens + 0.15 * levenshtein));
}

/**
 * Score one DOM candidate against the expected attributes in `[0..1]`.
 * Only provided expectations are weighted (re-normalized); with no
 * expectations at all the score is `0` (caller should not heal blind).
 */
export function scoreCandidate(
  expected: ExpectedAttributes,
  candidate: DomCandidate,
  weights: SimilarityWeights = DEFAULT_WEIGHTS,
): number {
  const terms: Array<{ weight: number; value: number }> = [];

  if (expected.text !== undefined && expected.text.trim().length > 0) {
    terms.push({ weight: weights.text, value: textSimilarity(expected.text, candidate.text) });
  }
  if (expected.ariaLabel !== undefined && expected.ariaLabel.trim().length > 0) {
    terms.push({ weight: weights.ariaLabel, value: textSimilarity(expected.ariaLabel, candidate.ariaLabel ?? '') });
  }
  if (expected.placeholder !== undefined && expected.placeholder.trim().length > 0) {
    terms.push({ weight: weights.placeholder, value: textSimilarity(expected.placeholder, candidate.placeholder ?? '') });
  }
  if (expected.role !== undefined && expected.role.trim().length > 0) {
    const actualRole = candidate.role ?? '';
    const roleScore = actualRole.toLowerCase() === expected.role.toLowerCase() ? 1 : textSimilarity(expected.role, actualRole);
    terms.push({ weight: weights.role, value: roleScore });
  }

  if (terms.length === 0) return 0;
  const totalWeight = terms.reduce((sum, term) => sum + term.weight, 0);
  if (totalWeight <= 0) return 0;
  return round3(terms.reduce((sum, term) => sum + term.weight * term.value, 0) / totalWeight);
}

/** Escape a dynamic value for safe embedding inside a CSS attribute selector. */
export function cssEscapeAttributeValue(value: string): string {
  return value.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
}

/**
 * Translate a DOM candidate into a concrete selector string, preferring the
 * most stable anchors in order: test id > element id >
 * role+aria-label > aria-label > placeholder > exact text engine > tag.
 */
export function buildSelectorFromCandidate(candidate: DomCandidate): string {
  if (candidate.testIdAttr !== null && candidate.testId !== null && candidate.testId.length > 0) {
    return `[${candidate.testIdAttr}="${cssEscapeAttributeValue(candidate.testId)}"]`;
  }
  if (candidate.id.length > 0) {
    return `#${cssEscapeAttributeValue(candidate.id)}`;
  }
  if (candidate.ariaLabel !== null && candidate.ariaLabel.length > 0 && candidate.role !== null && candidate.role.length > 0) {
    return `[role="${cssEscapeAttributeValue(candidate.role)}"][aria-label="${cssEscapeAttributeValue(candidate.ariaLabel)}"]`;
  }
  if (candidate.ariaLabel !== null && candidate.ariaLabel.length > 0) {
    return `[aria-label="${cssEscapeAttributeValue(candidate.ariaLabel)}"]`;
  }
  if (candidate.placeholder !== null && candidate.placeholder.length > 0) {
    return `[placeholder="${cssEscapeAttributeValue(candidate.placeholder)}"]`;
  }
  const text = candidate.text.trim();
  if (text.length > 0) {
    // Quoted text engine => exact match; JSON.stringify provides valid escaping.
    const truncated = text.length > 80 ? `${text.slice(0, 77)}...` : text;
    return `text=${JSON.stringify(truncated)}`;
  }
  return candidate.tag;
}

/**
 * Score every candidate, keep those at/above `threshold`, and return the top
 * matches sorted by descending score.
 */
export function rankCandidates(
  expected: ExpectedAttributes,
  candidates: readonly DomCandidate[],
  threshold: number = DEFAULT_HEAL_THRESHOLD,
): CandidateScore[] {
  return candidates
    .map((candidate) => ({
      candidate,
      selector: buildSelectorFromCandidate(candidate),
      score: scoreCandidate(expected, candidate),
    }))
    .filter((scored) => scored.score >= threshold && scored.selector.length > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, MAX_RANKED_CANDIDATES);
}
