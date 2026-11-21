import { NextResponse } from "next/server";
import { healthStatus } from "@/lib/env";
import { azureChatCompletion, isAzureFoundryConfigured } from "@/lib/azureFoundryModel";
import { ProviderError } from "@/lib/liveSearchTypes";

export const dynamic = "force-dynamic";

/**
 * Default: config-only status (fast, free, no model call).
 * ?deep=1 additionally pings the LLM once and reports whether it actually
 * works — distinguishes "env vars present" from "credentials valid".
 * Result is cached briefly so monitoring polls stay cheap.
 */
const DEEP_TTL_MS = 60_000;
let deepCache: { at: number; value: DeepStatus } | null = null;

interface DeepStatus {
  llmReachable: boolean;
  /** Machine-readable failure code when llmReachable is false */
  llmCode?: string;
}

async function deepCheck(): Promise<DeepStatus> {
  if (deepCache && Date.now() - deepCache.at < DEEP_TTL_MS) {
    return deepCache.value;
  }

  let value: DeepStatus;
  if (!isAzureFoundryConfigured()) {
    value = { llmReachable: false, llmCode: "missing_env" };
  } else {
    try {
      const text = await azureChatCompletion({
        system: "Reply with the single word OK.",
        user: "Health check — reply OK.",
      });
      value = { llmReachable: text.trim().length > 0 };
      if (!value.llmReachable) value.llmCode = "empty_response";
    } catch (err) {
      value = {
        llmReachable: false,
        llmCode:
          err instanceof ProviderError
            ? err.code ?? "request_failed"
            : "unknown_error",
      };
    }
  }

  deepCache = { at: Date.now(), value };
  return value;
}

export async function GET(request: Request) {
  const deep = new URL(request.url).searchParams.get("deep") === "1";
  const base = healthStatus();

  if (!deep || !base.llm) {
    return NextResponse.json(base, {
      headers: { "Cache-Control": "no-store" },
    });
  }

  const deepStatus = await deepCheck();
  return NextResponse.json(
    { ...base, ...deepStatus },
    { headers: { "Cache-Control": "no-store" } }
  );
}
