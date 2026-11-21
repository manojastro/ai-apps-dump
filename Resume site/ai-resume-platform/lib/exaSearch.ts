import Exa from "exa-js";
import type { LiveSearchSource } from "./liveSearchTypes";
import { ProviderError } from "./liveSearchTypes";
import { getEnv, isEnvConfigured } from "./env";

const MAX_SOURCES = 5;
const MAX_CONTEXT_CHARS = 9_500;
const MAX_HIGHLIGHT_CHARS_PER_SOURCE = 1_800;
const EXA_TIMEOUT_MS = 25_000;
const MAX_RETRIES = 1;

const TIME_SENSITIVE_RE =
  /\b(today|latest|current|recently|breaking|this\s+week|new\s+announcement)\b/i;

function getExaClient(): Exa {
  if (!isEnvConfigured("EXA_API_KEY")) {
    throw new ProviderError("EXA_API_KEY is not configured", {
      status: 503,
      provider: "exa",
      code: "missing_env",
    });
  }
  const apiKey = getEnv("EXA_API_KEY")!;
  return new Exa(apiKey);
}

function isHttpUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

function isTimeSensitive(query: string): boolean {
  return TIME_SENSITIVE_RE.test(query);
}

function daysAgoIso(days: number): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - days);
  return d.toISOString().slice(0, 10);
}

function withTimeout<T>(promise: Promise<T>, ms: number, label: string): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(
        new ProviderError(`${label} timed out`, {
          status: 504,
          provider: "exa",
          code: "timeout",
        })
      );
    }, ms);
    promise
      .then((value) => {
        clearTimeout(timer);
        resolve(value);
      })
      .catch((err) => {
        clearTimeout(timer);
        reject(err);
      });
  });
}

function mapExaError(err: unknown): ProviderError {
  if (err instanceof ProviderError) return err;

  const anyErr = err as {
    statusCode?: number;
    status?: number;
    message?: string;
    name?: string;
  };

  const status =
    typeof anyErr?.statusCode === "number"
      ? anyErr.statusCode
      : typeof anyErr?.status === "number"
        ? anyErr.status
        : 502;

  const message = typeof anyErr?.message === "string" ? anyErr.message : "Exa request failed";

  if (status === 401 || status === 403) {
    return new ProviderError("Exa authentication or permission error", {
      status,
      provider: "exa",
      code: "auth_error",
    });
  }
  if (status === 429) {
    return new ProviderError("Exa rate limit or quota exceeded", {
      status: 429,
      provider: "exa",
      code: "rate_limit",
    });
  }
  if (status === 504 || /timeout|aborted|ETIMEDOUT/i.test(message)) {
    return new ProviderError("Exa request timed out", {
      status: 504,
      provider: "exa",
      code: "timeout",
    });
  }
  if (status >= 500) {
    return new ProviderError("Exa upstream failure", {
      status: 502,
      provider: "exa",
      code: "upstream_error",
    });
  }

  console.error("[exa] search error", {
    provider: "exa",
    status,
    code: "request_failed",
  });

  return new ProviderError("Exa search failed", {
    status: status >= 400 && status < 600 ? status : 502,
    provider: "exa",
    code: "request_failed",
  });
}

function truncateHighlights(highlights: string[], budget: number): string[] {
  const out: string[] = [];
  let used = 0;
  for (const h of highlights) {
    const text = h.trim();
    if (!text) continue;
    if (used >= budget) break;
    const remaining = budget - used;
    if (text.length <= remaining) {
      out.push(text);
      used += text.length;
    } else {
      out.push(text.slice(0, remaining).trimEnd());
      used = budget;
      break;
    }
  }
  return out;
}

function normalizeResults(
  raw: Array<{
    title?: string | null;
    url?: string | null;
    publishedDate?: string | null;
    highlights?: string[] | null;
  }>,
  maxSources = MAX_SOURCES
): LiveSearchSource[] {
  const seen = new Set<string>();
  const sources: LiveSearchSource[] = [];
  const limit = Math.min(Math.max(maxSources, 1), 10);

  for (const item of raw) {
    const url = (item.url ?? "").trim();
    if (!url || !isHttpUrl(url)) continue;

    const key = url.replace(/\/+$/, "").toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);

    const highlights = Array.isArray(item.highlights)
      ? item.highlights.filter((h): h is string => typeof h === "string" && h.trim().length > 0)
      : [];

    sources.push({
      title: (item.title && item.title.trim()) || "Untitled source",
      url,
      publishedDate:
        typeof item.publishedDate === "string" && item.publishedDate.trim()
          ? item.publishedDate.trim()
          : null,
      highlights: truncateHighlights(highlights, MAX_HIGHLIGHT_CHARS_PER_SOURCE),
    });

    if (sources.length >= limit) break;
  }

  // Cap total context size across all sources
  let total = 0;
  for (const source of sources) {
    const overhead = source.title.length + source.url.length + 40;
    total += overhead;
    if (total >= MAX_CONTEXT_CHARS) {
      source.highlights = [];
      continue;
    }
    const remaining = MAX_CONTEXT_CHARS - total;
    source.highlights = truncateHighlights(source.highlights, remaining);
    total += source.highlights.reduce((n, h) => n + h.length, 0);
  }

  return sources;
}

export interface ExaSearchOptions {
  /** Max results to keep after normalize (default 5, max 10) */
  numResults?: number;
  /** Force fresher content window in days */
  freshnessDays?: number;
  /** Always fetch fresh page contents when true */
  forceFresh?: boolean;
}

async function runExaSearch(
  query: string,
  options: ExaSearchOptions = {}
): Promise<LiveSearchSource[]> {
  const exa = getExaClient();
  const timeSensitive = isTimeSensitive(query) || options.forceFresh === true;
  const numResults = Math.min(Math.max(options.numResults ?? MAX_SOURCES, 1), 10);

  const searchOptions: {
    type: "auto";
    numResults: number;
    contents: { highlights: true; maxAgeHours?: number };
    startPublishedDate?: string;
    userLocation?: string;
  } = {
    type: "auto",
    numResults,
    contents: {
      highlights: true,
      ...(timeSensitive || options.forceFresh ? { maxAgeHours: 0 } : {}),
    },
    userLocation: "IN",
  };

  const freshnessDays =
    options.freshnessDays ?? (timeSensitive ? 14 : undefined);
  if (freshnessDays !== undefined) {
    searchOptions.startPublishedDate = daysAgoIso(freshnessDays);
  }

  const result = await withTimeout(
    exa.search(query, searchOptions),
    EXA_TIMEOUT_MS,
    "Exa"
  );

  const results = Array.isArray(result?.results) ? result.results : [];
  return normalizeResults(results, numResults);
}

/**
 * Search the public web via Exa and return normalized, deduplicated sources.
 * Treat returned content as untrusted reference material only.
 */
export async function searchLiveSources(
  query: string,
  options: ExaSearchOptions = {}
): Promise<LiveSearchSource[]> {
  let lastError: ProviderError | null = null;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      return await runExaSearch(query, options);
    } catch (err) {
      const mapped = mapExaError(err);
      lastError = mapped;
      const retryable = [429, 500, 502, 503, 504].includes(mapped.status);
      if (!retryable || attempt >= MAX_RETRIES) {
        throw mapped;
      }
      // Brief backoff before single retry
      await new Promise((r) => setTimeout(r, 400 * (attempt + 1)));
    }
  }

  throw lastError ?? new ProviderError("Exa search failed", { status: 502, provider: "exa" });
}

/** Format numbered sources for the Azure Grok system/user context. */
export function formatSourcesForModel(sources: LiveSearchSource[]): string {
  return sources
    .map((s, i) => {
      const n = i + 1;
      const highlightLines =
        s.highlights.length > 0
          ? s.highlights.map((h) => `- ${h}`).join("\n")
          : "- (no highlights available)";
      return [
        `SOURCE [${n}]`,
        `Title: ${s.title}`,
        `URL: ${s.url}`,
        `Published: ${s.publishedDate ?? "unknown"}`,
        `Highlights:`,
        highlightLines,
      ].join("\n");
    })
    .join("\n\n");
}

export function sourcesToCitations(sources: LiveSearchSource[]) {
  return sources.map((s, i) => ({
    id: i + 1,
    title: s.title,
    url: s.url,
    publishedDate: s.publishedDate,
  }));
}
