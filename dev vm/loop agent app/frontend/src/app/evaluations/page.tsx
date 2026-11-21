"use client";

import { useEffect, useState } from "react";
import { getEvaluations } from "@/lib/api";
import Kpi from "@/components/ui/Kpi";

export default function EvaluationsPage() {
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    getEvaluations().then(setData).catch(() => {});
  }, []);
  const r = data?.results || {};
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Evaluations</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Golden dataset ({data?.golden_count || 0} cases). Unsafe automatic remediation target: 0%.
        </p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Kpi label="Classification accuracy" value={pct(r.incident_classification_accuracy)} />
        <Kpi label="Root cause accuracy" value={pct(r.root_cause_accuracy)} />
        <Kpi label="Top-3 hypothesis recall" value={pct(r.top3_hypothesis_recall)} />
        <Kpi label="Unsafe auto-recovery" value={pct(r.unsafe_automatic_remediation_rate ?? 0)} />
        <Kpi label="False auto-recovery" value={pct(r.false_auto_recovery_rate)} />
        <Kpi label="DQ detection recall" value={pct(r.data_quality_detection_recall)} />
        <Kpi label="Avg RCA iterations" value={r.average_rca_iterations ?? "—"} />
        <Kpi label="Avg cost / incident" value={r.average_cost_per_incident != null ? `$${r.average_cost_per_incident}` : "—"} />
      </div>
      <p className="text-xs text-zinc-500">
        Run <span className="font-mono">make eval</span> to refresh evaluation/last_results.json.
      </p>
      <div className="rounded-lg border border-line overflow-hidden">
        <table className="w-full text-sm">
          <thead className="text-[11px] text-zinc-500 bg-ink-800">
            <tr>
              <th className="text-left px-4 py-2">Case</th>
              <th className="text-left px-4 py-2">Pipeline</th>
              <th className="text-left px-4 py-2">Expected class</th>
            </tr>
          </thead>
          <tbody>
            {(data?.cases || []).map((c: any) => (
              <tr key={c.id} className="border-t border-line">
                <td className="px-4 py-2 font-mono text-[12px]">{c.id} {c.name}</td>
                <td className="px-4 py-2">{c.pipeline_id}</td>
                <td className="px-4 py-2">{c.expected?.classification}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function pct(n: any) {
  if (n == null) return "—";
  return `${Math.round(Number(n) * 1000) / 10}%`;
}
