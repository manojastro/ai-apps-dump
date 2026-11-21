// File: scripts/create-jira-bug.ts
/**
 * Automated Jira triage for failed E2E runs.
 *
 * Inputs (first match wins):
 *   1. `--report <path>`   : Playwright JSON report (CI sets
 *                            PLAYWRIGHT_JSON_OUTPUT_NAME=test-results/results.json);
 *                            every failed test becomes a failure payload.
 *   2. `--payload <path>`  : a hand-written JSON file matching FailurePayload.
 *   3. Environment         : TEST_TITLE (+ optional ERROR_MESSAGE, SPEC_FILE,
 *                            SCREENSHOT_PATH, RUN_URL, BROWSER, SHARD).
 *
 * Behavior:
 *   - Idempotent: before creating, searches open bugs in the configured Jira
 *     project with the exact summary `[E2E] <test title>`; duplicates are skipped.
 *   - Creates a Bug via REST API v3 with an ADF description (error in a code
 *     block, metadata bullet list, link to the CI run).
 *   - Attaches the failure screenshot through the attachment endpoint
 *     (`X-Atlassian-Token: no-check`).
 *
 * Exit codes: 0 = ok/nothing to do, 1 = configuration error, 2 = Jira API failure.
 */

import 'dotenv/config';
import path from 'node:path';
import { readFile, stat } from 'node:fs/promises';

/* ------------------------------------------------------------------ */
/* Domain types                                                        */
/* ------------------------------------------------------------------ */

export interface FailurePayload {
  testTitle: string;
  errorMessage: string;
  specFile?: string;
  screenshotPath?: string;
  runUrl?: string;
  browser?: string;
  shard?: string;
}

interface JiraCredentials {
  host: string;
  email: string;
  apiToken: string;
  projectKey: string;
  issueTypeName: string;
}

interface JiraSearchResponse {
  issues?: Array<{ key: string; fields?: { summary?: string } }>;
}

interface JiraCreateIssueResponse {
  id: string;
  key: string;
  self: string;
}

/** Minimal Atlassian Document Format types for issue descriptions. */
type AdfMark = { type: 'link'; attrs: { href: string } } | { type: 'strong' };
interface AdfText {
  type: 'text';
  text: string;
  marks?: AdfMark[];
}
interface AdfListItem {
  type: 'listItem';
  content: AdfBlock[];
}
type AdfBlock =
  | { type: 'paragraph'; content: AdfText[] }
  | { type: 'codeBlock'; attrs: { language: string }; content: AdfText[] }
  | { type: 'bulletList'; content: AdfListItem[] };
interface AdfDocument {
  type: 'doc';
  version: 1;
  content: AdfBlock[];
}

class ConfigurationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ConfigurationError';
  }
}

class JiraApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly details: string,
  ) {
    super(message);
    this.name = 'JiraApiError';
  }
}

/* ------------------------------------------------------------------ */
/* Config + HTTP                                                       */
/* ------------------------------------------------------------------ */

function requiredEnv(name: string): string {
  const value = process.env[name];
  if (value === undefined || value.trim().length === 0) {
    throw new ConfigurationError(`Missing required environment variable: ${name}`);
  }
  return value.trim();
}

function loadCredentials(): JiraCredentials {
  const rawHost = requiredEnv('JIRA_HOST');
  return {
    host: rawHost.replace(/^https?:\/\//, '').replace(/\/+$/, ''),
    email: requiredEnv('JIRA_EMAIL'),
    apiToken: requiredEnv('JIRA_API_TOKEN'),
    projectKey: requiredEnv('JIRA_PROJECT_KEY'),
    issueTypeName: process.env.JIRA_ISSUE_TYPE?.trim() || 'Bug',
  };
}

async function jiraRequest<T>(creds: JiraCredentials, pathname: string, init: RequestInit = {}): Promise<T> {
  const url = `https://${creds.host}${pathname}`;
  const headers = new Headers(init.headers);
  headers.set('Authorization', `Basic ${Buffer.from(`${creds.email}:${creds.apiToken}`).toString('base64')}`);
  headers.set('Accept', 'application/json');
  if (init.body !== undefined && !(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  let response: Response;
  try {
    response = await fetch(url, { ...init, headers });
  } catch (error: unknown) {
    throw new JiraApiError(`Network error calling ${url}: ${String(error)}`, 0, '');
  }

  if (!response.ok) {
    const details = (await response.text().catch(() => '')).slice(0, 2000);
    throw new JiraApiError(`Jira API ${response.status} ${response.statusText} for ${pathname}`, response.status, details);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function escapeJql(value: string): string {
  return value.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
}

function summaryFor(testTitle: string): string {
  return `[E2E] ${testTitle}`.slice(0, 250); // Jira caps summaries at 255 chars
}

/* ------------------------------------------------------------------ */
/* Jira operations                                                     */
/* ------------------------------------------------------------------ */

/**
 * Return the key of an OPEN bug whose summary exactly matches this test, or null.
 * Tries the modern POST search endpoint first and falls back to the legacy
 * GET endpoint for older Jira Cloud/Server deployments.
 */
export async function findExistingOpenBug(creds: JiraCredentials, testTitle: string): Promise<string | null> {
  const summary = summaryFor(testTitle);
  const jql =
    `project = "${escapeJql(creds.projectKey)}" AND issuetype = "${escapeJql(creds.issueTypeName)}" ` +
    `AND statusCategory != Done AND summary ~ "${escapeJql(testTitle)}" ORDER BY created DESC`;
  const body = JSON.stringify({ jql, maxResults: 10, fields: ['summary'] });

  let data: JiraSearchResponse;
  try {
    data = await jiraRequest<JiraSearchResponse>(creds, '/rest/api/3/search/jql', { method: 'POST', body });
  } catch (error: unknown) {
    const isClientError = error instanceof JiraApiError && error.status >= 400 && error.status < 500 && error.status !== 429;
    if (!isClientError) throw error;
    // Legacy fallback: deprecated but widely available GET /rest/api/3/search.
    const query = new URLSearchParams({ jql, maxResults: '10', fields: 'summary' }).toString();
    data = await jiraRequest<JiraSearchResponse>(creds, `/rest/api/3/search?${query}`);
  }

  const match = (data.issues ?? []).find((issue) => issue.fields?.summary === summary);
  return match?.key ?? null;
}

function buildAdfDescription(payload: FailurePayload): AdfDocument {
  const textNode = (text: string, marks?: AdfMark[]): AdfText => ({ type: 'text', text, marks });
  const paragraph = (nodes: AdfText[]): AdfBlock => ({ type: 'paragraph', content: nodes });
  const listItem = (nodes: AdfText[]): AdfListItem => ({
    type: 'listItem',
    content: [paragraph(nodes)],
  });

  const bullets: AdfListItem[] = [
    listItem([textNode(`Spec file: ${payload.specFile ?? 'unknown'}`)]),
    listItem([
      textNode(`Environment: ${payload.browser ?? 'unknown browser'}${payload.shard ? ` · shard ${payload.shard}` : ''}`),
    ]),
  ];
  if (payload.runUrl !== undefined && payload.runUrl.length > 0) {
    bullets.push(
      listItem([
        textNode('CI run: '),
        textNode('View failing workflow run', [{ type: 'link', attrs: { href: payload.runUrl } }]),
      ]),
    );
  }

  return {
    type: 'doc',
    version: 1,
    content: [
      paragraph([
        textNode('An automated E2E test failed on ', [{ type: 'strong' }]),
        textNode('main', [{ type: 'strong' }]),
        textNode('. Filed automatically by the self-healing E2E framework.'),
      ]),
      {
        type: 'codeBlock',
        attrs: { language: 'text' },
        content: [textNode((payload.errorMessage || '(no error message captured)').slice(0, 3000))],
      },
      { type: 'bulletList', content: bullets },
    ],
  };
}

export async function createBug(creds: JiraCredentials, payload: FailurePayload): Promise<JiraCreateIssueResponse> {
  const body = JSON.stringify({
    fields: {
      project: { key: creds.projectKey },
      issuetype: { name: creds.issueTypeName },
      summary: summaryFor(payload.testTitle),
      priority: { name: process.env.JIRA_PRIORITY?.trim() || 'Medium' },
      labels: ['e2e-failure', 'automated-ci'],
      description: buildAdfDescription(payload),
    },
  });
  return jiraRequest<JiraCreateIssueResponse>(creds, '/rest/api/3/issue', { method: 'POST', body });
}

/** Attach a screenshot to an issue; returns false when the file is absent. */
export async function attachScreenshot(creds: JiraCredentials, issueKey: string, filePath: string): Promise<boolean> {
  let size: number;
  try {
    size = (await stat(filePath)).size;
  } catch {
    console.warn(`[jira] screenshot not found, skipping attachment: ${filePath}`);
    return false;
  }
  if (size === 0) return false;

  const buffer = await readFile(filePath);
  const form = new FormData();
  form.append('file', new Blob([new Uint8Array(buffer)], { type: 'image/png' }), path.basename(filePath));

  await jiraRequest<unknown>(creds, `/rest/api/3/issue/${issueKey}/attachments`, {
    method: 'POST',
    body: form,
    headers: { 'X-Atlassian-Token': 'no-check' },
  });
  return true;
}

/* ------------------------------------------------------------------ */
/* Payload extraction                                                  */
/* ------------------------------------------------------------------ */

interface PlaywrightTestCase {
  ok: boolean;
  title: string;
  results: Array<{
    error?: { message?: string };
    attachments?: Array<{ name?: string; contentType?: string; path?: string }>;
  }>;
}

interface PlaywrightSuite {
  title?: string;
  file?: string;
  suites?: PlaywrightSuite[];
  specs?: Array<{ title?: string; file?: string; tests?: PlaywrightTestCase[] }>;
}

function collectFailures(suite: PlaywrightSuite, out: FailurePayload[], context: { browser?: string }): void {
  for (const child of suite.suites ?? []) {
    collectFailures(child, out, { browser: child.title ?? context.browser });
  }
  for (const spec of suite.specs ?? []) {
    for (const testCase of spec.tests ?? []) {
      if (testCase.ok) continue;
      const lastResult = testCase.results[testCase.results.length - 1];
      const screenshot = lastResult?.attachments?.find(
        (attachment) => attachment.contentType?.startsWith('image/') === true && typeof attachment.path === 'string',
      );
      out.push({
        testTitle: spec.title ?? testCase.title,
        errorMessage: lastResult?.error?.message ?? '(no error message captured)',
        specFile: spec.file ?? suite.file,
        screenshotPath: screenshot?.path,
        browser: context.browser,
      });
    }
  }
}

interface CliArgs {
  reportPath?: string;
  payloadPath?: string;
}

function parseCliArgs(argv: readonly string[]): CliArgs {
  const args: CliArgs = {};
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--report' && i + 1 < argv.length) args.reportPath = argv[i + 1];
    else if (arg === '--payload' && i + 1 < argv.length) args.payloadPath = argv[i + 1];
  }
  return args;
}

async function gatherPayloads(args: CliArgs): Promise<FailurePayload[]> {
  if (args.reportPath !== undefined) {
    const report = JSON.parse(await readFile(args.reportPath, 'utf8')) as PlaywrightSuite;
    const failures: FailurePayload[] = [];
    collectFailures(report, failures, {});
    return failures.map((failure) => ({ ...failure, runUrl: process.env.RUN_URL }));
  }
  if (args.payloadPath !== undefined) {
    return [JSON.parse(await readFile(args.payloadPath, 'utf8')) as FailurePayload];
  }
  const testTitle = process.env.TEST_TITLE;
  if (testTitle === undefined || testTitle.trim().length === 0) return [];
  return [
    {
      testTitle,
      errorMessage: process.env.ERROR_MESSAGE ?? '',
      specFile: process.env.SPEC_FILE,
      screenshotPath: process.env.SCREENSHOT_PATH,
      runUrl: process.env.RUN_URL,
      browser: process.env.BROWSER,
      shard: process.env.SHARD,
    },
  ];
}

/* ------------------------------------------------------------------ */
/* Orchestration                                                       */
/* ------------------------------------------------------------------ */

async function main(): Promise<void> {
  const creds = loadCredentials();
  const payloads = await gatherPayloads(parseCliArgs(process.argv.slice(2)));

  if (payloads.length === 0) {
    console.log('[jira] no failure payloads supplied; nothing to do.');
    return;
  }
  console.log(`[jira] processing ${payloads.length} failure payload(s) against project ${creds.projectKey}`);

  let created = 0;
  let duplicates = 0;
  let failed = 0;

  for (const payload of payloads) {
    try {
      const existingKey = await findExistingOpenBug(creds, payload.testTitle);
      if (existingKey !== null) {
        duplicates++;
        console.log(`[jira] duplicate open bug ${existingKey} for "${payload.testTitle}" — skipping creation.`);
        continue;
      }

      const issue = await createBug(creds, payload);
      created++;
      const attached = payload.screenshotPath !== undefined
        ? await attachScreenshot(creds, issue.key, payload.screenshotPath)
        : false;
      console.log(`[jira] created https://${creds.host}/browse/${issue.key} for "${payload.testTitle}"${attached ? ' (screenshot attached)' : ''}`);
    } catch (error: unknown) {
      failed++;
      console.error(`[jira] failed while filing "${payload.testTitle}":`, error instanceof Error ? error.message : error);
      if (error instanceof ConfigurationError) process.exitCode = 1;
      else if (error instanceof JiraApiError) {
        console.error('[jira] api details:', error.details);
        process.exitCode = 2;
      }
    }
  }

  console.log(`[jira] done — created: ${created}, duplicates skipped: ${duplicates}, errors: ${failed}`);
}

main().catch((error: unknown) => {
  console.error('[jira] fatal:', error);
  process.exitCode = 1;
});
