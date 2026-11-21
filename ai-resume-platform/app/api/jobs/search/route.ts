import { NextRequest, NextResponse } from "next/server";
import { searchJobs } from "@/lib/adzuna";

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

    if (!process.env.ADZUNA_APP_ID || !process.env.ADZUNA_APP_KEY) {
      return NextResponse.json(
        { error: "Adzuna API credentials not configured" },
        { status: 503 }
      );
    }

    const result = await searchJobs({ q, location, minCtc, maxCtc, page });
    return NextResponse.json(result);
  } catch (e) {
    console.error("Job search error:", e);
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Search failed" },
      { status: 500 }
    );
  }
}