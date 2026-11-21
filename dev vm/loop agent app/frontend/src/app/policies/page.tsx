"use client";

import { useEffect, useState } from "react";
import { getPolicies } from "@/lib/api";
import Badge from "@/components/ui/Badge";

export default function PoliciesPage() {
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => {
    getPolicies().then(setRows).catch(() => {});
  }, []);
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Deterministic policies</h1>
        <p className="text-sm text-zinc-500 mt-1">LLM judgment cannot override these gates.</p>
      </div>
      <div className="space-y-3">
        {rows.map((p) => (
          <div key={p.id} className="rounded-lg border border-line bg-ink-800/70 p-4 flex items-start justify-between">
            <div>
              <div className="font-mono text-sm text-teal-200">{p.id}</div>
              <div className="text-sm text-zinc-300 mt-1">{p.description}</div>
            </div>
            <Badge status={p.action}>{p.action}</Badge>
          </div>
        ))}
      </div>
    </div>
  );
}
