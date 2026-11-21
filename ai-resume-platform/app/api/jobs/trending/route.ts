import { NextResponse } from "next/server";
import { computeTrendingDomains, getMockTrendingData } from "@/lib/trending";

export async function GET() {
  try {
    if (!process.env.ADZUNA_APP_ID || !process.env.ADZUNA_APP_KEY) {
      return NextResponse.json(getMockTrendingData());
    }

    const domains = await computeTrendingDomains();
    return NextResponse.json(domains);
  } catch (e) {
    console.error("Trending error:", e);
    return NextResponse.json(getMockTrendingData());
  }
}