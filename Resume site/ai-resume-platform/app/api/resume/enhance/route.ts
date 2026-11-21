import { NextRequest, NextResponse } from "next/server";
import { enhanceResume, isAzureFoundryConfigured } from "@/lib/azureFoundryModel";
import type { ResumeData } from "@/lib/resumeSchema";
import { ProviderError } from "@/lib/liveSearchTypes";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { rawText, targetJobDescription, existingResumeJson } = body;

    if (!rawText || typeof rawText !== "string" || !rawText.trim()) {
      return NextResponse.json({ error: "rawText is required" }, { status: 400 });
    }

    if (!isAzureFoundryConfigured()) {
      return NextResponse.json(
        {
          error:
            "Azure Foundry is not configured. Set AZURE_FOUNDRY_API_KEY, AZURE_FOUNDRY_BASE_URL, and AZURE_FOUNDRY_MODEL in .env.local",
          code: "missing_env",
        },
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
    if (e instanceof ProviderError) {
      console.error("Resume enhance provider error", {
        provider: e.provider,
        status: e.status,
        code: e.code,
      });
      return NextResponse.json(
        { error: e.message, code: e.code },
        { status: e.status }
      );
    }
    console.error("Resume enhance error:", e instanceof Error ? e.message : "unknown");
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Enhancement failed" },
      { status: 500 }
    );
  }
}
