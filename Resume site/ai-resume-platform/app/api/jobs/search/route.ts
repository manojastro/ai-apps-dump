import { NextRequest, NextResponse } from "next/server";
import { searchJobs } from "@/lib/adzuna";
import { isEnvConfigured } from "@/lib/env";
import {
  canUseExaListingsOnly,
  searchJobsViaExa,
} from "@/lib/exaMarketInsights";
import { JOB_DOMAINS } from "@/lib/domains";
import { ProviderError } from "@/lib/liveSearchTypes";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = req.nextUrl;
    const q = searchParams.get("q") || undefined;
    const location = searchParams.get("location") || undefined;
    const minCtc = searchParams.get("minCtc")
      ? Number(searchParams.get("minCtc"))
      : undefined;
    const maxCtc = searchParams.get("maxCtc")
      ? Number(searchParams.get("maxCtc"))
      : undefined;
    const page = searchParams.get("page")
      ? Number(searchParams.get("page"))
      : 1;
    const domainId = searchParams.get("domain") || undefined;

    const hasAdzuna =
      isEnvConfigured("ADZUNA_APP_ID") && isEnvConfigured("ADZUNA_APP_KEY");

    if (hasAdzuna) {
      const result = await searchJobs({ q, location, minCtc, maxCtc, page });
      return NextResponse.json({ ...result, source: "adzuna" });
    }

    if (canUseExaListingsOnly()) {
      let domainKeyword: string | undefined;
      if (domainId) {
        const domain = JOB_DOMAINS.find((d) => d.id === domainId);
        domainKeyword = domain?.keywords[0];
      }

      const result = await searchJobsViaExa({ q, location, domainKeyword });
      return NextResponse.json({
        ...result,
        note: "Public listings found on the web. Salaries are not estimated — open a listing for details.",
      });
    }

    return NextResponse.json(
      {
        error:
          "Job search needs either Adzuna keys or EXA_API_KEY. Configure EXA_API_KEY in .env.local for web-based listings.",
        code: "missing_env",
      },
      { status: 503 }
    );
  } catch (e) {
    if (e instanceof ProviderError) {
      return NextResponse.json(
        { error: e.message, code: e.code },
        { status: e.status }
      );
    }
    console.error("Job search error:", e instanceof Error ? e.message : "unknown");
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Search failed" },
      { status: 500 }
    );
  }
}
