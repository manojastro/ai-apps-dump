// File: src/core/selectorHistory.ts
/**
 * Persistent memory for healed selectors (`selector-history.json`).
 *
 * Design notes:
 * - Writes are serialized through an in-process promise chain; cross-process
 *   safety comes from atomic tmp-file + rename writes (last writer wins per
 *   shard, which is acceptable because each worker heals distinct elements
 *   in practice and the next run replays the merged map).
 * - All reads tolerate a missing or corrupted file and degrade to `{}` so a
 *   broken history file can never take a test suite down.
 */

import path from 'node:path';
import { mkdir, readFile, rename, writeFile } from 'node:fs/promises';
import type { HealedSelectorRecord, SelectorHistoryEntry, SelectorHistoryMap } from './types';

/** Maximum remembered selectors per logical element key. */
export const MAX_SELECTORS_PER_KEY = 10;

/** Resolve the effective history file location (env-overridable). */
export function getHistoryFilePath(): string {
  const configured = process.env.SELECTOR_HISTORY_PATH;
  return configured
    ? path.resolve(process.cwd(), configured)
    : path.resolve(process.cwd(), 'selector-history.json');
}

/** Structural guard for untrusted JSON loaded from disk. */
function isSelectorHistoryMap(value: unknown): value is SelectorHistoryMap {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) return false;
  return Object.values(value).every((entry) => {
    if (typeof entry !== 'object' || entry === null) return false;
    const candidate = entry as Partial<SelectorHistoryEntry>;
    return (
      typeof candidate.key === 'string' &&
      typeof candidate.current === 'string' &&
      Array.isArray(candidate.history)
    );
  });
}

/**
 * Load the selector history map. Missing file => empty map; corrupted file =>
 * warn once and continue with an empty map (healing still works, just cold).
 */
export async function loadHistory(filePath: string = getHistoryFilePath()): Promise<SelectorHistoryMap> {
  try {
    const contents = await readFile(filePath, 'utf8');
    const parsed: unknown = JSON.parse(contents);
    if (isSelectorHistoryMap(parsed)) return parsed;
    console.warn(`[selectorHistory] "${filePath}" has an unexpected shape; starting cold.`);
    return {};
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return {};
    console.warn(`[selectorHistory] unable to read "${filePath}": ${(error as Error).message}`);
    return {};
  }
}

/**
 * Ordered candidate list for a logical element: current selector first,
 * then previously known-good ones, de-duplicated.
 */
export function lookupHistoricalSelectors(history: SelectorHistoryMap, elementKey: string): string[] {
  const entry = history[elementKey];
  if (!entry) return [];
  const ordered = [entry.current, ...entry.history.map((record) => record.selector)];
  return [...new Set(ordered)];
}

/** Atomic save: write to a pid-scoped temp file, then rename over the target. */
export async function saveHistory(map: SelectorHistoryMap, filePath: string = getHistoryFilePath()): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const tempPath = `${filePath}.${process.pid}.tmp`;
  const payload = `${JSON.stringify(map, null, 2)}\n`;
  await writeFile(tempPath, payload, 'utf8');
  await rename(tempPath, filePath); // atomic on POSIX; replace-on-rename on Windows
}

let mutationChain: Promise<void> = Promise.resolve();

/**
 * Persist a newly healed selector under `elementKey`.
 *
 * The new selector becomes `current`; the previous current selector is
 * demoted into the bounded history ring. Failures are logged, never thrown,
 * so persistence problems cannot fail a green test.
 */
export function recordHealedSelector(
  elementKey: string,
  record: HealedSelectorRecord,
  filePath: string = getHistoryFilePath(),
): Promise<void> {
  const task = mutationChain.then(async () => {
    const map = await loadHistory(filePath);
    const existing = map[elementKey];
    const entry: SelectorHistoryEntry = existing ?? { key: elementKey, current: '', history: [] };

    const previousCurrent = entry.current;
    const incoming: HealedSelectorRecord[] = [record];
    if (previousCurrent.length > 0 && previousCurrent !== record.selector) {
      incoming.push({
        selector: previousCurrent,
        strategy: record.strategy,
        confidence: record.confidence,
        healedAt: record.healedAt,
      });
    }

    const seen = new Set<string>();
    const merged: HealedSelectorRecord[] = [];
    for (const candidate of [...incoming, ...entry.history]) {
      if (seen.has(candidate.selector)) continue;
      seen.add(candidate.selector);
      merged.push(candidate);
      if (merged.length >= MAX_SELECTORS_PER_KEY) break;
    }

    entry.history = merged;
    entry.current = record.selector;
    map[elementKey] = entry;
    await saveHistory(map, filePath);
  });

  mutationChain = task.catch((error: unknown) => {
    console.error(`[selectorHistory] failed to persist heal for "${elementKey}":`, error);
  });
  return mutationChain;
}
