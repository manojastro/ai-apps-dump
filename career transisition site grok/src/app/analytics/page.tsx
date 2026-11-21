"use client";

import { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { MetricCard } from "@/components/shared/metric-card";
import { SectionHeader } from "@/components/shared/empty-state";
import { analyticsModel, hoursBreakdown, rangeFromPreset, type DateRange } from "@/lib/analytics";
import { learningBuildingRatio } from "@/lib/recommendations";
import { derivePhase } from "@/lib/phase";
import { useCareerStore } from "@/store/career-store";

export default function AnalyticsPage() {
  const state = useCareerStore((s) => s.state);
  const [preset, setPreset] = useState<DateRange["preset"]>("30d");
  const range = rangeFromPreset(preset);
  const model = useMemo(() => analyticsModel(state, range), [state, range]);
  const hours = hoursBreakdown(state, range);
  const ratio = learningBuildingRatio(state, range.from, range.to);
  const phase = derivePhase(state);

  return (
    <div className="space-y-5">
      <SectionHeader title="Analytics" description="Facts are stored records. Scores are derived. Insights are rules. Nothing is labeled AI-powered." />
      <div className="flex flex-wrap gap-2">
        {(["7d", "30d", "90d", "all"] as const).map((p) => (
          <button key={p} type="button" onClick={() => setPreset(p)} className={`rounded-md px-3 py-1.5 text-[13px] ${preset === p ? "bg-white/10" : "text-slate-400"}`}>
            {p}
          </button>
        ))}
      </div>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">Transition</h2>
        <p className="text-[12px] text-slate-500">Derived</p>
        <div className="mt-3 grid gap-3 md:grid-cols-4">
          <MetricCard label="Readiness" value={model.readiness.global} trust="Derived" />
          <MetricCard label="Phase" value={phase} trust="Derived" />
          <MetricCard label="Evidence" value={model.readiness.evidence} trust="Derived" />
          <MetricCard label="Snapshots" value={model.snapshots.length} trust="Fact" />
        </div>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">Capability & evidence</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <MetricCard label="Capability" value={model.readiness.capability} trust="Derived" />
          <MetricCard label="Interview" value={model.readiness.interview} trust="Derived" />
          <MetricCard label="Avg application quality" value={Math.round(model.qualityAvg)} trust="Derived" />
        </div>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">Jobs</h2>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={Object.entries(model.funnel.counts).map(([k, v]) => ({ name: k, n: v }))}>
              <CartesianGrid stroke="rgba(148,163,184,0.08)" />
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} allowDecimals={false} />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,0.12)" }} />
              <Bar dataKey="n" fill="#22d3ee" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-[13px]">
            <thead className="text-[11px] text-slate-500"><tr><th>Source</th><th>Apps</th><th>Screen</th><th>Tech</th><th></th></tr></thead>
            <tbody>
              {model.bySource.map((r) => (
                <tr key={r.key} className="border-t border-white/5">
                  <td className="py-1">{r.key}</td>
                  <td className="tabular">{r.apps}</td>
                  <td className="tabular">{r.screening}</td>
                  <td className="tabular">{r.technical}</td>
                  <td className="text-amber-300">{r.warning ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h3 className="mt-4 text-[13px] font-medium">Resume performance</h3>
        <table className="w-full text-left text-[13px]">
          <thead className="text-[11px] text-slate-500"><tr><th>Resume</th><th>Apps</th><th>Screen</th><th>Tech</th></tr></thead>
          <tbody>
            {model.resumes.map((r) => (
              <tr key={r.resume.id} className="border-t border-white/5">
                <td>{r.resume.name} {r.resume.versionLabel}</td>
                <td className="tabular">{r.apps}</td>
                <td className="tabular">{r.screening}</td>
                <td className="tabular">{r.technical} {r.warning ? <span className="text-amber-300">{r.warning}</span> : null}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">Execution · last period</h2>
        <p className="text-[13px] text-slate-400">
          Learning {hours.learning.toFixed(1)}h · Building {hours.building.toFixed(1)}h · Interview {hours.interview.toFixed(1)}h · Job search {hours.jobSearch.toFixed(1)}h
        </p>
        {ratio.learning > ratio.building * 2 && ratio.learning > 240 ? (
          <p className="mt-2 text-[13px] text-amber-300">Recommendation: learning dominates building. Convert study into a deployed artifact.</p>
        ) : null}
      </section>
    </div>
  );
}
