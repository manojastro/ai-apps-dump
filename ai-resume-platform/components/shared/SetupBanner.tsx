"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface HealthStatus {
  gemini: boolean;
  adzuna: boolean;
}

export function SetupBanner({ context }: { context: "resume" | "jobs" | "all" }) {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth({ gemini: false, adzuna: false }));
  }, []);

  if (!health) return null;

  const needsGemini = (context === "resume" || context === "all") && !health.gemini;
  const needsAdzuna = (context === "jobs" || context === "all") && !health.adzuna;

  if (!needsGemini && !needsAdzuna) return null;

  return (
    <div className="mx-auto max-w-5xl px-6 pt-4">
      <div className="rounded-2xl bg-[#ff9500]/10 border border-[#ff9500]/20 px-5 py-4 text-[13px] text-[#1d1d1f]">
        <p className="font-medium mb-1">Some features need API keys</p>
        <p className="text-[#6e6e73] leading-relaxed">
          Copy <code className="text-[12px] bg-black/[0.04] px-1.5 py-0.5 rounded">.env.example</code> to{" "}
          <code className="text-[12px] bg-black/[0.04] px-1.5 py-0.5 rounded">.env.local</code> and add:
        </p>
        <ul className="mt-2 space-y-1 text-[#6e6e73]">
          {needsGemini && (
            <li>• <strong>GEMINI_API_KEY</strong> — required for AI enhance (Paste, Chat, Upload)</li>
          )}
          {needsAdzuna && (
            <li>• <strong>ADZUNA_APP_ID</strong> + <strong>ADZUNA_APP_KEY</strong> — required for job search & live trends</li>
          )}
        </ul>
        <p className="mt-2 text-[#6e6e73]">
          Restart <code className="text-[12px]">npm run dev</code> after saving.{" "}
          <Link href="https://aistudio.google.com/" target="_blank" className="text-[#0071e3] hover:opacity-70">
            Gemini keys
          </Link>
          {" · "}
          <Link href="https://developer.adzuna.com/" target="_blank" className="text-[#0071e3] hover:opacity-70">
            Adzuna keys
          </Link>
        </p>
      </div>
    </div>
  );
}