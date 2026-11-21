"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Kpi from "@/components/ui/Kpi";
import Badge from "@/components/ui/Badge";
import { getIncidents, getMetrics, getPipelines } from "@/lib/api";
import { fmtSec, fmtTime } from "@/lib/utils";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [pipelines, setPipelines] = useState<any[]>([]);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getMetrics(), getPipelines(), getIncidents()])
      .then(([m, p, i]) => {
        setMetrics(m);
        setPipelines(p);
        setIncidents(i);
      })
      .catch((e) => setErr(String(e)));
  }, []);

  if (err) return <ErrorBox err={err} />;
  if (!metrics) return <div className="text-zinc-500">Loading platform…</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Data platform health</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Autonomous investigation graph watching simulated enterprise pipelines.
        </p>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-8 gap-3">
        <Kpi label="Pipeline health" value={`${metrics.pipeline_health}%`} />
        <Kpi label="Active pipelines" value={metrics.active_pipelines} />
        <Kpi label="Healthy" value={metrics.healthy} />
        <Kpi label="Warning" value={metrics.warning} />
        <Kpi label="Failed" value={metrics.failed} />
        <Kpi label="Open incidents" value={metrics.open_incidents} />
        <Kpi label="Auto recovery" value={`${metrics.auto_recovery_rate}%`} />
        <Kpi label="MTTD / MTTR" value={`${fmtSec(metrics.mttd_sec)} / ${fmtSec(metrics.mttr_sec)}`} />
      </div>

      <section className="rounded-lg border border-line overflow-hidden">
        <div className="px-4 py-3 border-b border-line text-[12px] uppercase tracking-[0.16em] text-zinc-500">
          Pipelines
        </div>
        <table className="w-full text-sm">
          <thead className="text-[11px] uppercase tracking-wider text-zinc-500 bg-ink-800">
            <tr>
              <th className="text-left px-4 py-2 font-medium">Pipeline</th>
              <th className="text-left px-4 py-2 font-medium">Status</th>
              <th className="text-left px-4 py-2 font-medium">Quality</th>
              <th className="text-left px-4 py-2 font-medium">Last run</th>
            </tr>
          </thead>
          <tbody>
            {pipelines.map((p) => (
              <tr key={p.id} className="border-t border-line hover:bg-white/[0.03]">
                <td className="px-4 py-2">
                  <Link href={`/pipelines/${p.id}`} className="text-teal-200 hover:underline font-medium">
                    {p.id}
                  </Link>
                  <div className="text-[11px] text-zinc-500">{p.name}</div>
                </td>
                <td className="px-4 py-2">
                  <Badge status={p.status}>{p.status}</Badge>
                </td>
                <td className="px-4 py-2 tabular-nums">{Math.round(p.quality_score)}%</td>
                <td className="px-4 py-2 text-zinc-400">{fmtTime(p.last_run_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="rounded-lg border border-line overflow-hidden">
        <div className="px-4 py-3 border-b border-line text-[12px] uppercase tracking-[0.16em] text-zinc-500">
          Recent incidents
        </div>
        <table className="w-full text-sm">
          <thead className="text-[11px] uppercase tracking-wider text-zinc-500 bg-ink-800">
            <tr>
              <th className="text-left px-4 py-2 font-medium">Incident</th>
              <th className="text-left px-4 py-2 font-medium">Pipeline</th>
              <th className="text-left px-4 py-2 font-medium">Severity</th>
              <th className="text-left px-4 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {incidents.slice(0, 8).map((i) => (
              <tr key={i.id} className="border-t border-line hover:bg-white/[0.03]">
                <td className="px-4 py-2">
                  <Link href={`/incidents/${i.id}`} className="text-teal-200 hover:underline">
                    {i.id}
                  </Link>
                  <div className="text-[11px] text-zinc-500">{i.title}</div>
                </td>
                <td className="px-4 py-2 font-mono text-[12px]">{i.pipeline_id}</td>
                <td className="px-4 py-2">
                  <Badge status={i.severity}>{i.severity}</Badge>
                </td>
                <td className="px-4 py-2">
                  <Badge status={i.status}>{i.status}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function ErrorBox({ err }: { err: string }) {
  return (
    <div className="rounded border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200">
      Backend unreachable. Start the API on :8000. {err}
    </div>
  );
}
