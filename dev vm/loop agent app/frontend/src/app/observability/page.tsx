"use client";

import { useEffect, useState } from "react";
import { getObservability } from "@/lib/api";
import Kpi from "@/components/ui/Kpi";

export default function ObservabilityPage() {
  const [o, setO] = useState<any>(null);
  useEffect(() => {
    getObservability().then(setO).catch(() => {});
  }, []);
  if (!o) return <div className="text-zinc-500">Loading telemetry…</div>;
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Observability</h1>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <Kpi label="Agent runs" value={o.agent_runs} />
        <Kpi label="Auto recovery" value={`${Math.round(o.auto_recovery_rate)}%`} />
        <Kpi label="Avg RCA iterations" value={Number(o.average_rca_iterations).toFixed(1)} />
        <Kpi label="Cost / incident" value={`$${Number(o.cost_per_incident || 0).toFixed(3)}`} />
        <Kpi label="Token usage" value={o.token_usage} />
        <Kpi label="Tool calls" value={o.tool_calls} />
        <Kpi label="LLM calls" value={o.llm_calls} />
        <Kpi label="Escalation rate" value={`${Math.round(o.escalation_rate)}%`} />
        <Kpi label="Pipeline MTTR" value={`${Math.round(o.pipeline_mttr)}s`} />
        <Kpi label="Unsafe auto-remediation" value={`${o.unsafe_automatic_remediation_rate}%`} />
      </div>
      <pre className="text-[11px] text-zinc-500 border border-line rounded p-3 overflow-auto">
        {JSON.stringify(o.live, null, 2)}
      </pre>
    </div>
  );
}
