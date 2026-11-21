import { NextRequest, NextResponse } from "next/server";
import {
  searchLiveSources,
  sourcesToCitations,
} from "@/lib/exaSearch";
import { generateGroundedAnswer } from "@/lib/azureFoundryModel";
import { ProviderError } from "@/lib/liveSearchTypes";
import type { LiveSearchResponse } from "@/lib/liveSearchTypes";
import { isEnvConfigured } from "@/lib/env";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const MAX_QUERY_LENGTH = 1_000;

const EMAIL_RE = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/;
const PHONE_RE =
  /(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?)?\d{3,5}[\s.-]\d{3,5}\b/;
const SECRET_RE =
  /\b(?:api[_-]?key|password|passwd|secret|token|authorization)\s*[:=]\s*\S+/i;
const HOME_ADDRESS_RE =
  /\b\d{1,5}\s+[A-Za-z0-9.'\s]{3,40}\b(?:street|st|road|rd|avenue|ave|lane|ln|boulevard|blvd|nagar|colony|sector)\b/i;
const RESUME_MARKERS_RE =
  /\b(?:work\s+experience|professional\s+summary|curriculum\s+vitae|\bcv\b|linkedin\.com\/in\/)\b/i;

function noStoreJson(body: unknown, status = 200) {
  return NextResponse.json(body, {
    status,
    headers: {
      "Cache-Control": "no-store",
    },
  });
}

function looksSensitive(query: string): string | null {
  if (EMAIL_RE.test(query)) {
    return "Query appears to contain an email address. Remove personal contact details.";
  }
  if (SECRET_RE.test(query)) {
    return "Query appears to contain secrets or credentials. Remove them before searching.";
  }
  // Phone: require enough digits to avoid flagging years/CTC alone
  const phoneMatch = query.match(PHONE_RE);
  if (phoneMatch) {
    const digits = phoneMatch[0].replace(/\D/g, "");
    if (digits.length >= 10) {
      return "Query appears to contain a phone number. Remove personal contact details.";
    }
  }
  if (HOME_ADDRESS_RE.test(query)) {
    return "Query appears to contain a home address. Remove personal location details.";
  }
  // Heuristic: long multi-section paste that looks like a full resume
  if (query.length > 600 && RESUME_MARKERS_RE.test(query)) {
    return "Do not paste a complete resume into live search. Ask a specific market or skills question instead.";
  }
  if (RESUME_MARKERS_RE.test(query) && query.split(/\n/).length >= 8) {
    return "Do not paste a complete resume into live search. Ask a specific market or skills question instead.";
  }
  return null;
}

function validateQuery(raw: unknown): { ok: true; query: string } | { ok: false; error: string } {
  if (typeof raw !== "string") {
    return { ok: false, error: "query must be a string" };
  }
  const query = raw.trim();
  if (!query) {
    return { ok: false, error: "query is required" };
  }
  if (query.length > MAX_QUERY_LENGTH) {
    return {
      ok: false,
      error: `query must be at most ${MAX_QUERY_LENGTH} characters`,
    };
  }
  const sensitive = looksSensitive(query);
  if (sensitive) {
    return { ok: false, error: sensitive };
  }
  return { ok: true, query };
}

function mapError(err: unknown): { status: number; error: string; code?: string } {
  if (err instanceof ProviderError) {
    console.error("[live-search] provider error", {
      provider: err.provider,
      status: err.status,
      code: err.code,
      requestId: err.requestId,
    });
    return {
      status: err.status,
      error: err.message,
      code: err.code,
    };
  }

  console.error("[live-search] unexpected error", {
    provider: "internal",
    status: 500,
    code: "internal_error",
  });

  return {
    status: 500,
    error: "Unexpected internal server error",
    code: "internal_error",
  };
}

export async function POST(req: NextRequest) {
  try {
    let body: unknown;
    try {
      body = await req.json();
    } catch {
      return noStoreJson({ error: "Invalid JSON body" }, 400);
    }

    const queryField =
      body && typeof body === "object" && body !== null && "query" in body
        ? (body as { query: unknown }).query
        : undefined;

    const validated = validateQuery(queryField);
    if (!validated.ok) {
      return noStoreJson({ error: validated.error, code: "validation_error" }, 400);
    }

    const { query } = validated;

    // Env checks early for clear 503s (placeholders count as missing)
    if (!isEnvConfigured("EXA_API_KEY")) {
      return noStoreJson(
        { error: "EXA_API_KEY is not configured", code: "missing_env" },
        503
      );
    }
    if (
      !isEnvConfigured("AZURE_FOUNDRY_API_KEY") ||
      !isEnvConfigured("AZURE_FOUNDRY_BASE_URL") ||
      !isEnvConfigured("AZURE_FOUNDRY_MODEL")
    ) {
      return noStoreJson(
        {
          error:
            "Azure Foundry is not configured (AZURE_FOUNDRY_API_KEY, AZURE_FOUNDRY_BASE_URL, AZURE_FOUNDRY_MODEL)",
          code: "missing_env",
        },
        503
      );
    }

    const sources = await searchLiveSources(query);

    if (sources.length === 0) {
      const empty: LiveSearchResponse = {
        answer:
          "No usable public sources were found for that query. Try rephrasing with more specific skills, companies, or topics. Vacancy counts and salaries still come from Adzuna job search, not live web search.",
        citations: [],
      };
      return noStoreJson(empty);
    }

    const answer = await generateGroundedAnswer(query, sources);
    const citations = sourcesToCitations(sources);

    const response: LiveSearchResponse = {
      answer,
      citations,
    };

    return noStoreJson(response);
  } catch (err) {
    const mapped = mapError(err);
    return noStoreJson(
      { error: mapped.error, code: mapped.code },
      mapped.status
    );
  }
}
