"use client";

import Link from "next/link";
import { useMemo } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CompensationTrack, MetricCard, ProgressBar, ProgressRing } from "@/components/shared/metric-card";
import { Badge } from "@/components/ui/badge";
import { formatLpa } from "@/lib/currency";
import { derivePhase } from "@/lib/phase";
import { rankActions } from "@/lib/priority-engine";
import { careerInsights } from "@/lib/recommendations";
import { allRoleReadiness } from "@/lib/role-readiness";
import { funnelMetrics, velocitySeries } from "@/lib/analytics";
import { computeReadiness } from "@/lib/scoring";
import { active } from "@/lib/utils";
import { weekStartIso as weekStart } from "@/lib/dates";
import { useCareerStore } from "@/store/career-store";

export default function DashboardPage() {
  const state = useCareerStore((s) => s.state);
  const privacy = state.ui.privacyMode;
  const readiness = useMemo(() => computeReadiness(state), [state]);
  const insights = useMemo(() => careerInsights(state), [state]);
  const roles = useMemo(() => allRoleReadiness(state), [state]);
  const actions = useMemo(() => rankActions(state), [state]);
  const funnel = useMemo(() => funnelMetrics(active(state.applications)), [state]);
  const velocity = velocitySeries(state);
  const phase = derivePhase(state);
  const week = weekStart();
  const sprint = active(state.weeklySprints).find((s) => s.weekStart === week);
  const pipeline = active(state.applications).filter((a) => ["Screening", "Technical", "Offer"].includes(a.status)).length;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[11px] font-medium tracking-[0.18em] text-cyan-300 uppercase">AI Career Transition — 2026</p>
          <h1 className="mt-1 text-[26px] leading-tight font-semibold tracking-tight">₹11 LPA → ₹20–35+ LPA AI Engineering</h1>
          <p className="mt-1.5 text-[13px] text-slate-400">
            Phase {phase}. Scores are derived from evidence quality, not record count.
          </p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
        <div className="card flex items-center gap-5 p-5 sm:col-span-2">
          <ProgressRing value={readiness.global} label="Ready" />
          <div>
            <p className="text-[11px] font-medium tracking-[0.14em] text-slate-400 uppercase">Transition Readiness</p>
            <p className="tabular mt-1 text-[32px] leading-none font-semibold">{readiness.global}</p>
            <p className="mt-2 text-[12px] text-slate-500">Derived metric</p>
          </div>
        </div>
        <MetricCard label="Capability" value={readiness.capability} tone="emerald" trust="Derived" />
        <MetricCard label="Evidence" value={readiness.evidence} tone="cyan" trust="Derived" />
        <MetricCard label="Interview" value={readiness.interview} tone="indigo" trust="Derived" />
        <MetricCard label="Market" value={readiness.marketExecution} tone="amber" trust="Derived" hint={`${pipeline} active interview-stage apps`} />
      </div>

      <div className="grid gap-3 lg:grid-cols-3">
        <section className="card p-5 lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold tracking-tight">Current Career Bottleneck</h2>
            <Badge tone="amber">Recommendation</Badge>
          </div>
          <p className="text-[17px] font-medium tracking-tight text-white">{insights.bottleneck.kind}</p>
          <p className="mt-2 text-[13px] leading-5 text-slate-400">{insights.bottleneck.detail}</p>
        </section>
        <section className="card p-5">
          <h2 className="text-sm font-semibold tracking-tight">Compensation path</h2>
          <p className="tabular mt-2 text-[13px] text-slate-300">
            {formatLpa(state.settings.baselineCtc, privacy)} → {formatLpa(state.settings.targetMinCtc, privacy)}–
            {formatLpa(state.settings.targetMaxCtc, privacy)}
          </p>
          <CompensationTrack
            baseline={state.settings.baselineCtc}
            floor={state.settings.targetMinCtc}
            target={state.settings.targetMaxCtc}
            stretch={state.settings.stretchCtc}
            privacy={privacy}
          />
          <p className="mt-3 text-[12px] text-slate-500">Readiness is not a guarantee of compensation.</p>
        </section>
      </div>

      <section className="card p-4">
        <h2 className="mb-3 text-sm font-semibold">Highest-Leverage Actions</h2>
        <div className="grid gap-2 md:grid-cols-3">
          {actions.slice(0, 5).map((a) => (
            <Link key={a.id} href={a.href} className="card-2 p-3 hover:border-cyan-400/30">
              <div className="flex items-center justify-between gap-2">
                <p className="text-[13px] font-medium text-white">{a.title}</p>
                <Badge tone={a.priority === "Very High" ? "red" : "amber"}>{a.priority}</Badge>
              </div>
              <ul className="mt-2 list-disc pl-4 text-[12px] text-slate-400">
                {a.why.slice(0, 3).map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            </Link>
          ))}
          {actions.length === 0 ? <p className="text-[13px] text-slate-500">No ranked actions yet. Add a project or job.</p> : null}
        </div>
      </section>

      <section className="card p-4">
        <h2 className="mb-3 text-sm font-semibold">Role Readiness</h2>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {roles.map((r) => (
            <Link key={r.role.id} href={`/roles/${r.role.id}`} className="card-2 p-3">
              <div className="flex items-center justify-between">
                <p className="text-[13px] font-medium">{r.role.name}</p>
                <Badge tone="indigo">{r.role.priority}</Badge>
              </div>
              <div className="mt-2">
                <ProgressBar value={r.score} />
              </div>
              <p className="mt-2 text-[12px] text-slate-500">
                {r.strong.length} strong · {r.partial.length} partial · {r.evidenceMissing.length} evidence missing
              </p>
            </Link>
          ))}
        </div>
      </section>

      <div className="grid gap-3 lg:grid-cols-2">
        <section className="card p-4">
          <h2 className="mb-3 text-sm font-semibold">Transition Risks</h2>
          <div className="space-y-2">
            {insights.risks.length === 0 ? <p className="text-[13px] text-slate-500">No active risk rules fired.</p> : null}
            {insights.risks.map((r) => (
              <div key={r.kind} className="card-2 p-3">
                <div className="flex items-center justify-between">
                  <p className="text-[13px] font-medium">{r.title}</p>
                  <Badge tone={r.severity === "high" ? "red" : "amber"}>{r.severity}</Badge>
                </div>
                <p className="mt-1 text-[12px] text-slate-400">{r.detail}</p>
              </div>
            ))}
          </div>
        </section>
        <section className="card p-4">
          <h2 className="mb-3 text-sm font-semibold">Weekly Sprint</h2>
          {sprint ? (
            <div className="space-y-2 text-[13px]">
              <p className="font-medium">{sprint.title}</p>
              <p className="text-slate-400">
                Learning {sprint.learningHours}h · Building {sprint.buildingHours}h · Apps {sprint.applicationsSubmitted}/
                {state.settings.weeklyApplicationsTarget}
              </p>
              <ul className="list-disc pl-4 text-slate-400">
                {sprint.objectives.map((o) => (
                  <li key={o} className={sprint.completedObjectives.includes(o) ? "text-emerald-300" : ""}>
                    {o}
                  </li>
                ))}
              </ul>
              <Link href="/execution" className="text-cyan-300">
                Open execution →
              </Link>
            </div>
          ) : (
            <p className="text-[13px] text-slate-500">No sprint for week of {week}. Create one in Execution.</p>
          )}
        </section>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <section className="card p-4">
          <h2 className="mb-3 text-sm font-semibold">Application Funnel</h2>
          <div className="space-y-2">
            {Object.entries(funnel.counts).map(([k, v]) => (
              <div key={k} className="flex items-center gap-3 text-[13px]">
                <span className="w-24 text-slate-400">{k}</span>
                <div className="h-1.5 flex-1 rounded bg-white/10">
                  <div className="h-full rounded bg-cyan-400/80" style={{ width: `${Math.min(100, (v as number) * 12)}%` }} />
                </div>
                <span className="tabular w-6 text-right">{v as number}</span>
              </div>
            ))}
          </div>
        </section>
        <section className="card p-4">
          <h2 className="mb-3 text-sm font-semibold">Career Velocity</h2>
          {velocity.length === 0 ? (
            <p className="text-[13px] text-slate-500">Snapshots appear after the OS has real history. Nothing is fabricated.</p>
          ) : (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={velocity}>
                  <CartesianGrid stroke="rgba(148,163,184,0.08)" />
                  <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} domain={[0, 100]} />
                  <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,0.12)" }} />
                  <Area type="monotone" dataKey="readiness" stroke="#22d3ee" fill="#22d3ee33" />
                  <Area type="monotone" dataKey="evidence" stroke="#34d399" fill="transparent" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
