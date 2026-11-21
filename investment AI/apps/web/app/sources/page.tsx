"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { KEYS, readKey } from "@/lib/session";
import { Panel } from "@/components/Panel";

type Source = {
  title: string;
  authority: string;
  url: string;
  as_of: string;
  fetched_at: string | null;
  tier: number;
  verification: string;
  affected_facts: string[];
};

export default function SourcesPage() {
  const [rows, setRows] = useState<Source[]>([]);

  useEffect(() => {
    const plan = readKey(KEYS.plan);
    const q = plan ? `?plan_id=${plan}` : "";
    void api<{ data: Source[] }>(`/api/v1/sources${q}`).then((res) => setRows(res.data));
  }, []);

  return (
    <Panel title="Source register" kicker="Authoritative first">
      <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead>
          <tr className="border-b border-rule">
            <th className="py-2 pr-3">Source</th>
            <th className="pr-3">Authority</th>
            <th className="pr-3">As of</th>
            <th className="pr-3">Fetched</th>
            <th className="pr-3">Tier</th>
            <th className="pr-3">Verification</th>
            <th className="pr-3">Facts</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((s) => (
            <tr key={s.url + s.title} className="border-b border-rule/80 align-top">
              <td className="py-2">
                <a className="text-navy underline" href={s.url} target="_blank" rel="noreferrer">
                  {s.title}
                </a>
              </td>
              <td>{s.authority}</td>
              <td>{s.as_of}</td>
              <td>{s.fetched_at ? String(s.fetched_at).slice(0, 19) : "—"}</td>
              <td>{s.tier}</td>
              <td>{s.verification}</td>
              <td>{(s.affected_facts || []).join(", ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </Panel>
  );
}
