"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Badge from "@/components/ui/Badge";
import { getPipeline } from "@/lib/api";
import { fmtTime } from "@/lib/utils";

export default function PipelineDetail() {
  const { id } = useParams<{ id: string }>();
  const [p, setP] = useState<any>(null);
  useEffect(() => {
    getPipeline(id).then(setP).catch(() => {});
  }, [id]);
  if (!p) return <div className="text-zinc-500">Loading…</div>;
  const lin = p.lineage || [];
  const nodes = Array.from(new Set(lin.flatMap((e: string[]) => e)));
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">Pipeline</div>
          <h1 className="text-2xl font-semibold font-mono">{p.id}</h1>
          <p className="text-zinc-400 text-sm mt-1">{p.description}</p>
        </div>
        <Badge status={p.status}>{p.status}</Badge>
      </div>
      <div className="grid grid-cols-4 gap-3">
        <Info label="Last successful run" value={fmtTime(p.last_success_at)} />
        <Info label="Current / last run" value={fmtTime(p.last_run_at)} />
        <Info label="Duration" value={`${p.last_run?.duration_ms || 0} ms`} />
        <Info label="SLA" value={`< ${p.sla_seconds}s`} />
      </div>
      <section className="rounded-lg border border-line p-5">
        <div className="text-[11px] uppercase tracking-[0.16em] text-zinc-500 mb-4">Lineage</div>
        <div className="flex flex-col items-start gap-2">
          {nodes.map((n: string, i: number) => (
            <div key={n} className="flex flex-col items-start">
              <div className="px-3 py-2 rounded border border-line bg-ink-800 font-mono text-[12px]">{n}</div>
              {i < nodes.length - 1 ? <div className="ml-6 h-4 w-px bg-zinc-600" /> : null}
            </div>
          ))}
        </div>
      </section>
      <section className="rounded-lg border border-line overflow-hidden">
        <div className="px-4 py-3 border-b border-line text-[12px] uppercase tracking-[0.16em] text-zinc-500">
          Recent runs
        </div>
        <table className="w-full text-sm">
          <thead className="text-[11px] text-zinc-500 bg-ink-800">
            <tr>
              <th className="text-left px-4 py-2">Run</th>
              <th className="text-left px-4 py-2">Status</th>
              <th className="text-left px-4 py-2">Rows</th>
              <th className="text-left px-4 py-2">Quality</th>
              <th className="text-left px-4 py-2">Error</th>
            </tr>
          </thead>
          <tbody>
            {(p.runs || []).map((r: any) => (
              <tr key={r.id} className="border-t border-line">
                <td className="px-4 py-2 font-mono text-[12px]">{r.id}</td>
                <td className="px-4 py-2">
                  <Badge status={r.status}>{r.status}</Badge>
                </td>
                <td className="px-4 py-2 tabular-nums">{r.rows_written}</td>
                <td className="px-4 py-2">{Math.round(r.quality_score)}%</td>
                <td className="px-4 py-2 text-rose-300 text-[12px] max-w-md truncate">{r.error_message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-line bg-ink-800/70 p-4">
      <div className="text-[11px] uppercase tracking-[0.16em] text-zinc-500">{label}</div>
      <div className="mt-2 text-sm">{value}</div>
    </div>
  );
}
