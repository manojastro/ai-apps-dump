// File: src/core/healEventStore.ts
/**
 * Durable transport between test workers (which heal elements) and the runner
 * process (where the HealingReporter aggregates). Playwright workers are
 * separate OS processes, so in-memory singletons would lose events; instead
 * each worker appends JSONL lines into a run-scoped directory that the
 * reporter reads at `onEnd`.
 */

import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { appendFile, mkdir, readdir, readFile } from 'node:fs/promises';
import type { HealEvent } from './types';

/** Directory holding JSONL heal-event files for the current run. */
export function getHealEventsDir(): string {
  const configured = process.env.HEAL_EVENTS_DIR;
  return configured
    ? path.resolve(process.cwd(), configured)
    : path.resolve(process.cwd(), 'test-results', 'healing-events');
}

let appendChain: Promise<void> = Promise.resolve();

/** Stamp id/timestamp onto a partial event. */
export function createHealEvent(details: Omit<HealEvent, 'id' | 'timestamp'>): HealEvent {
  return { id: randomUUID(), timestamp: new Date().toISOString(), ...details };
}

/** Append one event (serialized per-process to keep lines well-formed). */
export function appendHealEvent(event: HealEvent, dir: string = getHealEventsDir()): Promise<void> {
  const task = appendChain.then(async () => {
    await mkdir(dir, { recursive: true });
    const fileName = `events-worker-${Math.max(event.workerIndex, 0)}.jsonl`;
    await appendFile(path.join(dir, fileName), `${JSON.stringify(event)}\n`, 'utf8');
  });
  appendChain = task.catch((error: unknown) => {
    console.error('[healEventStore] failed to append heal event:', error);
  });
  return appendChain;
}

/** Read and merge every worker's events, oldest first. Tolerates garbage lines. */
export async function readHealEvents(dir: string = getHealEventsDir()): Promise<HealEvent[]> {
  let fileNames: string[];
  try {
    fileNames = (await readdir(dir)).filter((name) => name.endsWith('.jsonl')).sort();
  } catch {
    return [];
  }

  const events: HealEvent[] = [];
  for (const fileName of fileNames) {
    let contents: string;
    try {
      contents = await readFile(path.join(dir, fileName), 'utf8');
    } catch {
      continue;
    }
    for (const line of contents.split('\n')) {
      const trimmed = line.trim();
      if (trimmed.length === 0) continue;
      try {
        events.push(JSON.parse(trimmed) as HealEvent);
      } catch {
        // Corrupt/partial line from a killed worker — skip without failing the report.
      }
    }
  }
  return events.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
}
