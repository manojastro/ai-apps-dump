import { NextResponse } from "next/server";
import { computeTrendingDomains, getMockTrendingData } from "@/lib/trending";
import {
  canUseExaMarketPath,
  computeExaTrendingDomains,
} from "@/lib/exaMarketInsights";
import { isEnvConfigured } from "@/lib/env";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET() {
  try {
    const hasAdzuna =
      isEnvConfigured("ADZUNA_APP_ID") && isEnvConfigured("ADZUNA_APP_KEY");

    // Prefer Adzuna when configured (real vacancy counts)
    if (hasAdzuna) {
      const domains = await computeTrendingDomains();
      return NextResponse.json({
        domains,
        source: "adzuna",
        note: "Live vacancy counts and salary ranges from Adzuna (India).",
      });
    }

    // Exa + Azure Grok path — qualitative web insights, no invented counts
    if (canUseExaMarketPath()) {
      const { domains, synthesisError } = await computeExaTrendingDomains();
      return NextResponse.json({
        domains,
        source: "exa",
        note: synthesisError
          ? "AI research is temporarily unavailable — showing no signals rather than guessing."
          : "Demand signals from current web sources — not official vacancy counts or salaries.",
        ...(synthesisError ? { detail: synthesisError } : {}),
      });
    }

    return NextResponse.json({
      domains: getMockTrendingData(),
      source: "mock",
      note: "Add API keys to see live demand signals.",
    });
  } catch (e) {
    console.error(
      "Trending error:",
      e instanceof Error ? e.message : "unknown"
    );

    // Soft fallback
    if (canUseExaMarketPath()) {
      try {
        const domains = await computeExaTrendingDomains();
        return NextResponse.json({
          domains,
          source: "exa",
          note: "Demand signals from current web sources.",
        });
      } catch {
        /* fall through */
      }
    }

    return NextResponse.json({
      domains: getMockTrendingData(),
      source: "mock",
      note: "Trending temporarily unavailable.",
    });
  }
}
