/**
 * Browser-safe helper for ResumeAI live web search.
 * Calls only POST /api/live-search — never Exa or Azure directly.
 */

import type {
  LiveSearchRequest,
  LiveSearchResponse,
  LiveSearchErrorBody,
} from "./liveSearchTypes";

export type { LiveSearchRequest, LiveSearchResponse, LiveSearchCitation } from "./liveSearchTypes";

export class LiveSearchClientError extends Error {
  readonly status: number;
  readonly code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "LiveSearchClientError";
    this.status = status;
    this.code = code;
  }
}

export async function liveSearch(
  query: string,
  init?: { signal?: AbortSignal }
): Promise<LiveSearchResponse> {
  const body: LiveSearchRequest = { query };

  const res = await fetch("/api/live-search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: init?.signal,
    cache: "no-store",
  });

  let data: LiveSearchResponse | LiveSearchErrorBody | null = null;
  try {
    data = (await res.json()) as LiveSearchResponse | LiveSearchErrorBody;
  } catch {
    throw new LiveSearchClientError(
      `Live search failed (${res.status})`,
      res.status
    );
  }

  if (!res.ok) {
    const errBody = data as LiveSearchErrorBody;
    throw new LiveSearchClientError(
      errBody?.error || `Live search failed (${res.status})`,
      res.status,
      errBody?.code
    );
  }

  const ok = data as LiveSearchResponse;
  if (typeof ok?.answer !== "string" || !Array.isArray(ok?.citations)) {
    throw new LiveSearchClientError("Invalid live search response", 502, "invalid_response");
  }

  return ok;
}
