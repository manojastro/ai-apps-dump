"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Badge from "@/components/ui/Badge";
import { getPipelines } from "@/lib/api";
import { fmtTime } from "@/lib/utils";

export default function PipelinesPage() {
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => {
    getPipelines().then(setRows).catch(() => setRows([]));
  }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Pipelines</h1>
      <div className="rounded-lg border border-line overflow-hidden">
        <table className="w-full text-sm">
          <thead className="text-[11px] uppercase tracking-wider text-zinc-500 bg-ink-800">
            <tr>
              <th className="text-left px-4 py-2">ID</th>
              <th className="text-left px-4 py-2">Name</th>
              <th className="text-left px-4 py-2">Status</th>
              <th className="text-left px-4 py-2">Quality</th>
              <th className="text-left px-4 py-2">Schedule</th>
              <th className="text-left px-4 py-2">Last run</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id} className="border-t border-line hover:bg-white/[0.03]">
                <td className="px-4 py-2">
                  <Link className="text-teal-200 hover:underline font-mono text-[12px]" href={`/pipelines/${p.id}`}>
                    {p.id}
                  </Link>
                </td>
                <td className="px-4 py-2">{p.name}</td>
                <td className="px-4 py-2">
                  <Badge status={p.status}>{p.status}</Badge>
                </td>
                <td className="px-4 py-2 tabular-nums">{Math.round(p.quality_score)}%</td>
                <td className="px-4 py-2 text-zinc-400">{p.schedule}</td>
                <td className="px-4 py-2 text-zinc-400">{fmtTime(p.last_run_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
