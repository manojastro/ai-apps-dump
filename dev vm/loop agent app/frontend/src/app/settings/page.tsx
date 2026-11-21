"use client";

import { useEffect, useState } from "react";
import { getSettings } from "@/lib/api";

export default function SettingsPage() {
  const [s, setS] = useState<any>(null);
  useEffect(() => {
    getSettings().then(setS).catch(() => {});
  }, []);
  if (!s) return <div className="text-zinc-500">Loading…</div>;
  const budgets = [
    ["MAX_RCA_ITERATIONS", s.max_rca_iterations],
    ["MAX_HYPOTHESES", s.max_hypotheses],
    ["MAX_REMEDIATION_ATTEMPTS", s.max_remediation_attempts],
    ["MAX_RECOVERY_CYCLES", s.max_recovery_cycles],
    ["MAX_LLM_CALLS", s.max_llm_calls],
    ["MAX_TOOL_CALLS", s.max_tool_calls],
    ["MAX_INCIDENT_COST_USD", s.max_incident_cost_usd],
    ["MAX_EXECUTION_TIME_SEC", s.max_execution_time_sec],
    ["LLM_PROVIDER", s.llm_provider],
    ["FAST_MODEL", s.llm_fast_model],
    ["REASONING_MODEL", s.llm_reasoning_model],
  ];
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Settings & bounded autonomy</h1>
      <div className="rounded-lg border border-line divide-y divide-line">
        {budgets.map(([k, v]) => (
          <div key={k} className="flex justify-between px-4 py-3 text-sm">
            <span className="font-mono text-zinc-400">{k}</span>
            <span className="font-mono text-teal-200">{String(v)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
