// File: src/core/reporters/HealingReporter.ts
/**
 * Custom Playwright reporter that aggregates every self-healing intervention
 * from the run into a single self-contained HTML dashboard
 * (`test-results/healing-report.html`) and prints a terminal summary.
 *
 * Register in `playwright.config.ts`:
 *   reporter: [['list'], ['./src/core/reporters/HealingReporter.ts']]
 */

import path from 'node:path';
import { mkdir, writeFile } from 'node:fs/promises';
import { rmSync } from 'node:fs';
import type { FullConfig, FullResult, Reporter, Suite } from '@playwright/test/reporter';
import { getHealEventsDir, readHealEvents } from '../healEventStore';
import type { HealEvent, HealingStrategy } from '../types';

const REPORT_FILE_NAME = 'healing-report.html';

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function confidenceColor(score: number): string {
  if (score >= 0.9) return '#22c55e'; // green
  if (score >= 0.8) return '#eab308'; // amber
  return '#f97316'; // orange
}

function strategyBadge(strategy: HealingStrategy): string {
  const palette: Record<HealingStrategy, string> = {
    'historical-map': 'background:#3f2d12;color:#fbbf24;border:1px solid #a16207;',
    'fuzzy-dom': 'background:#2b2140;color:#c4b5fd;border:1px solid #7c3aed;',
  };
  return `<span class="badge" style="${palette[strategy]}">${escapeHtml(strategy)}</span>`;
}

function renderEventCard(event: HealEvent): string {
  const pct = Math.round(event.confidence * 100);
  return `
  <article class="card">
    <header>
      <div>
        <div class="key">${escapeHtml(event.elementKey)}</div>
        <div class="test">${escapeHtml(event.specFile)} &rsaquo; ${escapeHtml(event.testTitle)} (worker ${event.workerIndex})</div>
      </div>
      ${strategyBadge(event.strategy)}
    </header>
    <table class="selectors">
      <tr><td class="label">primary</td><td><code>${escapeHtml(event.primarySelector)}</code></td></tr>
      <tr><td class="label">healed</td><td><code>${escapeHtml(event.healedSelector)}</code></td></tr>
    </table>
    <div class="confidence-row">
      <span>confidence</span>
      <div class="bar"><div class="fill" style="width:${pct}%;background:${confidenceColor(event.confidence)}"></div></div>
      <strong style="color:${confidenceColor(event.confidence)}">${(event.confidence * 100).toFixed(1)}%</strong>
    </div>
    <footer>
      scanned ${event.candidatesScanned} candidates &middot; healed in ${event.durationMs}ms &middot; ${escapeHtml(event.timestamp)}
      <details><summary>original error</summary><pre>${escapeHtml(event.originalError)}</pre></details>
    </footer>
  </article>`;
}

function renderDocument(events: readonly HealEvent[], status: FullResult['status']): string {
  const generatedAt = new Date().toISOString();
  const uniqueKeys = new Set(events.map((event) => event.elementKey)).size;
  const avgConfidence =
    events.length === 0 ? 0 : events.reduce((sum, event) => sum + event.confidence, 0) / events.length;
  const historyHits = events.filter((event) => event.strategy === 'historical-map').length;
  const fuzzyHeals = events.filter((event) => event.strategy === 'fuzzy-dom').length;
  const cards = events.map(renderEventCard).join('\n');

  const summaryBlock = `
    <section class="summary">
      <div class="stat"><span>${events.length}</span>heals this run</div>
      <div class="stat"><span>${uniqueKeys}</span>distinct elements</div>
      <div class="stat"><span>${historyHits}</span>history replays</div>
      <div class="stat"><span>${fuzzyHeals}</span>fuzzy DOM heals</div>
      <div class="stat"><span>${(avgConfidence * 100).toFixed(1)}%</span>avg confidence</div>
      <div class="stat"><span>${escapeHtml(status)}</span>run status</div>
    </section>`;

  const emptyState = `
    <section class="empty">
      <h2>No healing required</h2>
      <p>All primary selectors resolved on their first attempt. The suite is healthy.</p>
    </section>`;

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Self-Healing Report</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
         background:#0b1020; color:#e2e8f0; padding:32px; }
  h1 { font-size:22px; letter-spacing:.02em; margin-bottom:4px; }
  .generated { color:#64748b; font-size:12px; margin-bottom:24px; }
  .summary { display:flex; flex-wrap:wrap; gap:12px; margin-bottom:28px; }
  .stat { background:#111a33; border:1px solid #1e293b; border-radius:10px; padding:14px 18px; min-width:130px; }
  .stat span { display:block; font-size:24px; font-weight:700; color:#7dd3fc; }
  .card { background:#111a33; border:1px solid #1e293b; border-radius:12px; padding:18px; max-width:860px;
          margin-bottom:16px; box-shadow:0 6px 24px rgba(2,6,23,.45); }
  .card header { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:12px; }
  .key { font-weight:700; font-size:15px; }
  .test { color:#94a3b8; font-size:12px; margin-top:3px; }
  .badge { border-radius:999px; padding:3px 10px; font-size:11px; font-weight:600; white-space:nowrap; }
  .selectors { width:100%; border-collapse:collapse; margin-bottom:10px; }
  .selectors td { padding:5px 8px; vertical-align:top; }
  .selectors .label { color:#64748b; width:70px; text-transform:uppercase; font-size:10px; letter-spacing:.08em; }
  code { font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size:12.5px;
         background:#0b1020; border:1px solid #1e293b; border-radius:6px; padding:2px 6px; word-break:break-all; }
  .confidence-row { display:flex; align-items:center; gap:10px; font-size:12px; color:#94a3b8; margin-bottom:10px; }
  .bar { flex:1; height:6px; background:#1e293b; border-radius:999px; overflow:hidden; }
  .fill { height:100%; border-radius:999px; }
  footer { font-size:11.5px; color:#64748b; border-top:1px dashed #1e293b; padding-top:10px; }
  details { margin-top:8px; }
  summary { cursor:pointer; color:#94a3b8; }
  pre { white-space:pre-wrap; font-size:11.5px; background:#0b1020; border:1px solid #7f1d1d55;
        border-radius:8px; padding:10px; margin-top:8px; color:#fca5a5; }
  .empty { text-align:center; padding:60px 20px; background:#0f172a33; border:1px dashed #1e293b; border-radius:12px; }
  .empty p { color:#64748b; margin-top:8px; }
</style>
</head>
<body>
  <h1>Self-Healing Locator Report</h1>
  <div class="generated">Generated ${escapeHtml(generatedAt)}</div>
  ${summaryBlock}
  ${events.length === 0 ? emptyState : cards}
</body>
</html>`;
}

/**
 * Playwright reporter implementation. Clears stale events on begin, then at
 * the end of the run merges all worker JSONL files into one HTML report.
 */
export default class HealingReporter implements Reporter {
  private readonly eventsDir: string = getHealEventsDir();

  public onBegin(_config: FullConfig, _suite: Suite): void {
    // Synchronous clear guarantees no race with workers appending fresh events.
    rmSync(this.eventsDir, { recursive: true, force: true });
  }

  public printsToStdio(): boolean {
    return true;
  }

  public async onEnd(result: FullResult): Promise<void> {
    const events = await readHealEvents(this.eventsDir);

    for (const event of events) {
      process.stdout.write(
        `[healing-report] ${event.strategy.padEnd(15)} ${(event.confidence * 100).toFixed(1).padStart(5)}%  ` +
          `${event.elementKey}: ${event.primarySelector} -> ${event.healedSelector}\n`,
      );
    }

    if (events.length === 0) {
      process.stdout.write('[healing-report] no self-healing interventions were recorded this run.\n');
    }

    const reportPath = path.resolve(this.eventsDir, '..', REPORT_FILE_NAME);
    await mkdir(path.dirname(reportPath), { recursive: true });
    await writeFile(reportPath, renderDocument(events, result.status), 'utf8');
    process.stdout.write(`[healing-report] full dashboard written to ${reportPath}\n`);
  }
}
