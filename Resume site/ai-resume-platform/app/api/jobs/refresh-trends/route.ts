import { NextResponse } from "next/server";
import { clearCache } from "@/lib/cache";
import { computeTrendingDomains } from "@/lib/trending";

export async function POST() {
  try {
    clearCache("trending-domains");
    const domains = await computeTrendingDomains();
    return NextResponse.json({ refreshed: true, count: domains.length });
  } catch (e) {
    console.error("Refresh trends error:", e);
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Refresh failed" },
      { status: 500 }
    );
  }
}