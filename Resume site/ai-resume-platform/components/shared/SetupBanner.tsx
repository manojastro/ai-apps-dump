"use client";

import { useEffect, useState } from "react";

interface HealthStatus {
  llm?: boolean;
  azureFoundry?: boolean;
  adzuna: boolean;
  exa?: boolean;
  /** legacy alias — same as azureFoundry */
  gemini?: boolean;
}

export function SetupBanner({ context }: { context: "resume" | "jobs" | "all" }) {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() =>
        setHealth({
          llm: false,
          azureFoundry: false,
          adzuna: false,
          exa: false,
          gemini: false,
        })
      );
  }, []);

  if (!health) return null;

  const llmReady = health.llm ?? health.azureFoundry ?? health.gemini ?? false;
  const needsLlm = !llmReady;
  const needsExa =
    (context === "jobs" || context === "all") && health.exa === false;
  // Adzuna is fully optional — Exa powers trends + web listings without it
  if (!needsLlm && !needsExa) return null;

  const missing = [
    needsLlm && "AZURE_FOUNDRY_API_KEY",
    needsExa && "EXA_API_KEY",
  ].filter(Boolean);

  return (
    <div className="mb-8 rounded-xl border border-[#ff9500]/25 bg-[#ff9500]/[0.08] px-4 py-3 text-[13px]">
      <p className="text-[#1d1d1f]">
        {needsLlm && !needsExa
          ? "AI enhance is unavailable until an API key is set."
          : needsExa && !needsLlm
            ? "Live web search is unavailable until an API key is set."
            : "AI features are unavailable until API keys are set."}
      </p>
      <p className="mt-1 text-[#6e6e73]">
        Add {missing.join(" and ")} to{" "}
        <code className="rounded bg-black/[0.05] px-1.5 py-0.5 text-[12px]">
          .env.local
        </code>
        , then restart the dev server.
      </p>
    </div>
  );
}
