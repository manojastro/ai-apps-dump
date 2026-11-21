"use client";

import { useEffect, useState } from "react";
import { getQuality } from "@/lib/api";
import Badge from "@/components/ui/Badge";

export default function QualityPage() {
  const [q, setQ] = useState<any>(null);
  useEffect(() => {
    getQuality().then(setQ).catch(() => {});
  }, []);
  if (!q) return <div className="text-zinc-500">Loading quality…</div>;
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Data quality</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {(q.live || []).map((d: any) => (
          <div key={d.dataset} className="rounded-lg border border-line bg-ink-800/70 p-4">
            <div className="text-[11px] uppercase tracking-[0.16em] text-zinc-500">{d.dataset}</div>
            <div className="text-3xl font-semibold mt-2 tabular-nums">{Math.round(d.score)}</div>
            <div className="text-[12px] text-zinc-500 mt-1">{d.failed?.length || 0} failing checks</div>
          </div>
        ))}
      </div>
      <section className="rounded-lg border border-line overflow-hidden">
        <div className="px-4 py-3 border-b border-line text-[12px] uppercase tracking-[0.16em] text-zinc-500">
          Failing checks
        </div>
        <table className="w-full text-sm">
          <thead className="text-[11px] text-zinc-500 bg-ink-800">
            <tr>
              <th className="text-left px-4 py-2">Dataset</th>
              <th className="text-left px-4 py-2">Rule</th>
              <th className="text-left px-4 py-2">Expected</th>
              <th className="text-left px-4 py-2">Actual</th>
              <th className="text-left px-4 py-2">Severity</th>
            </tr>
          </thead>
          <tbody>
            {(q.live || [])
              .flatMap((d: any) => (d.failed || []).map((f: any) => ({ ...f, dataset: d.dataset })))
              .map((f: any, i: number) => (
                <tr key={i} className="border-t border-line">
                  <td className="px-4 py-2 font-mono text-[12px]">{f.dataset}</td>
                  <td className="px-4 py-2">{f.rule}</td>
                  <td className="px-4 py-2">{f.expected}</td>
                  <td className="px-4 py-2">{f.actual}</td>
                  <td className="px-4 py-2">
                    <Badge status={f.severity}>{f.severity}</Badge>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
