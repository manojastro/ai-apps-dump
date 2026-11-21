import { NextRequest, NextResponse } from "next/server";
import { enhanceResume } from "@/lib/gemini";
import type { ResumeData } from "@/lib/resumeSchema";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { rawText, targetJobDescription, existingResumeJson } = body;

    if (!rawText || typeof rawText !== "string" || !rawText.trim()) {
      return NextResponse.json({ error: "rawText is required" }, { status: 400 });
    }

    if (!process.env.GEMINI_API_KEY) {
      return NextResponse.json(
        { error: "GEMINI_API_KEY is not configured. Add it to .env.local" },
        { status: 503 }
      );
    }

    const result = await enhanceResume({
      rawText,
      targetJobDescription,
      existingResumeJson: existingResumeJson as ResumeData | undefined,
    });

    return NextResponse.json(result);
  } catch (e) {
    console.error("Resume enhance error:", e);
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Enhancement failed" },
      { status: 500 }
    );
  }
}