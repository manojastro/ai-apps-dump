"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { DISCLAIMER, NO_EXECUTION } from "@/lib/disclaimer";
import { inr, pct } from "@/lib/format";
import { Panel } from "@/components/Panel";

type Plan = {
  data: {
    plan_id: string;
    version: number;
    generated_at_ist: string;
    snapshot_id: string;
    rules_version: string;
    selected: string | null;
    risk_status: string;
    scenarios: Array<{
      name: string;
      label: string;
      equity_pct: number;
      weights: Array<{ sleeve: string; weight_pct: number; inr_amount: number }>;
    }>;
    actions: Array<{ title: string; detail: string; amount_inr: number | null }>;
    stress: Array<{ name: string; description: string; impact_summary: string }>;
    tax_notes: string[];
    protection_notes: string[];
    data_quality_warnings: string[];
    ips: { risk_band: string; equity_ceiling_pct: number; tax_regime: string };
    household: { first_name: string; age: number };
  };
};

export default function PlanPage() {
  const params = useParams<{ id: string }>();
  const [plan, setPlan] = useState<Plan["data"] | null>(null);

  useEffect(() => {
    void api<Plan>(`/api/v1/plans/${params.id}`).then((res) => setPlan(res.data));
  }, [params.id]);

  if (!plan) return <p>Loading plan…</p>;
  const selected = plan.scenarios.find((s) => s.name === plan.selected) || plan.scenarios[0];

  async function downloadPdf() {
    const res = await fetch(`/api/v1/plans/${params.id}/pdf`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `aegis-plan-${params.id}.pdf`;
    a.click();
  }

  return (
    <div className="space-y-6">
      <Panel title="Aegis Financial Action Plan" kicker={`${plan.plan_id} · v${plan.version}`}>
        <p className="text-sm text-ink/75">{DISCLAIMER}</p>
        <p className="mt-2 text-sm text-seal">{NO_EXECUTION}</p>
        <dl className="mt-4 grid gap-2 text-sm md:grid-cols-2">
          <div>Generated {plan.generated_at_ist}</div>
          <div>Snapshot {plan.snapshot_id}</div>
          <div>Rules {plan.rules_version}</div>
          <div>Risk Officer {plan.risk_status}</div>
          <div>
            Household {plan.household.first_name}, {plan.household.age}
          </div>
          <div>
            IPS {plan.ips.risk_band}, equity ceiling {pct(plan.ips.equity_ceiling_pct)}
          </div>
        </dl>
        <button className="mt-4 bg-navy px-4 py-2 text-sm text-paper" onClick={downloadPdf}>
          Download PDF
        </button>
      </Panel>
      <Panel title="Selected simulation">
        <p className="text-sm">
          {selected?.label}: equity {pct(selected?.equity_pct || 0)}
        </p>
        <table className="mt-3 w-full text-left text-sm">
          <tbody>
            {selected?.weights.map((w) => (
              <tr key={w.sleeve} className="border-b border-rule">
                <td className="py-2">{w.sleeve}</td>
                <td>{pct(w.weight_pct)}</td>
                <td>{inr(w.inr_amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
      <Panel title="Five actions for this month">
        <ol className="list-decimal space-y-2 pl-5 text-sm">
          {plan.actions.map((a) => (
            <li key={a.title}>
              {a.title}
              {a.amount_inr != null ? ` (${inr(a.amount_inr)})` : ""} — {a.detail}
            </li>
          ))}
        </ol>
      </Panel>
      <Panel title="Stress tests">
        {plan.stress.map((s) => (
          <p key={s.name} className="mb-2 text-sm">
            <b>{s.name}</b> (hypothetical): {s.impact_summary}
          </p>
        ))}
      </Panel>
      <Panel title="Tax and protection">
        {plan.tax_notes.map((n) => (
          <p key={n} className="text-sm">
            {n}
          </p>
        ))}
        {plan.protection_notes.map((n) => (
          <p key={n} className="mt-2 text-sm">
            {n}
          </p>
        ))}
      </Panel>
      {plan.data_quality_warnings.length ? (
        <Panel title="Data-quality warnings">
          {plan.data_quality_warnings.map((w) => (
            <p key={w} className="text-sm text-seal">
              {w}
            </p>
          ))}
        </Panel>
      ) : null}
    </div>
  );
}
