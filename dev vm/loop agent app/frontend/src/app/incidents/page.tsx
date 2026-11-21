"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Badge from "@/components/ui/Badge";
import { getIncidents, getScenarios, runScenario } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function IncidentsPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [scenarios, setScenarios] = useState<any[]>([]);
  const router = useRouter();
  const load = () => getIncidents().then(setRows).catch(() => {});
  useEffect(() => {
    load();
    getScenarios().then(setScenarios).catch(() => {});
  }, []);
  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-semibold">Incidents</h1>
          <p className="text-sm text-zinc-500 mt-1">Investigate with the cyclic recovery graph. Do not treat this as a chatbot.</p>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {scenarios.map((s) => (
          <button
            key={s.id}
            onClick={async () => {
              const inc = await runScenario(s.id);
              router.push(`/incidents/${inc.id}`);
            }}
            className="text-left rounded-lg border border-line bg-ink-800/70 p-4 hover:border-teal-400/40"
          >
            <div className="text-[11px] uppercase tracking-[0.16em] text-zinc-500">{s.id}</div>
            <div className="mt-1 font-medium">{s.name}</div>
            <div className="mt-1 text-[12px] text-zinc-500">{s.description}</div>
          </button>
        ))}
      </div>
      <div className="rounded-lg border border-line overflow-hidden">
        <table className="w-full text-sm">
          <thead className="text-[11px] uppercase tracking-wider text-zinc-500 bg-ink-800">
            <tr>
              <th className="text-left px-4 py-2">ID</th>
              <th className="text-left px-4 py-2">Title</th>
              <th className="text-left px-4 py-2">Pipeline</th>
              <th className="text-left px-4 py-2">Severity</th>
              <th className="text-left px-4 py-2">Status</th>
              <th className="text-left px-4 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((i) => (
              <tr key={i.id} className="border-t border-line hover:bg-white/[0.03]">
                <td className="px-4 py-2 font-mono text-[12px]">{i.id}</td>
                <td className="px-4 py-2">{i.title}</td>
                <td className="px-4 py-2 font-mono text-[12px]">{i.pipeline_id}</td>
                <td className="px-4 py-2">
                  <Badge status={i.severity}>{i.severity}</Badge>
                </td>
                <td className="px-4 py-2">
                  <Badge status={i.status}>{i.status}</Badge>
                </td>
                <td className="px-4 py-2">
                  <Link href={`/incidents/${i.id}`} className="text-teal-200 hover:underline">
                    Open
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
