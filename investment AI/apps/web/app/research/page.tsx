"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Panel } from "@/components/Panel";

type Snap = {
  data: {
    snapshot_id: string;
    degraded: boolean;
    data_mode: string;
    assessment_year?: { value: string; mock?: boolean; source_url: string };
    macro_state?: string;
    notes?: string[];
    sources?: Array<{ title: string; url: string; verification: string; as_of: string }>;
    conflicts?: string[];
  };
};

export default function ResearchPage() {
  const [reg, setReg] = useState<Snap | null>(null);
  const [mkt, setMkt] = useState<Snap | null>(null);

  useEffect(() => {
    void api<Snap>("/api/v1/regulatory/snapshot").then(setReg);
    void api<Snap>("/api/v1/market/snapshot").then(setMkt);
  }, []);

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Panel title="Regulatory snapshot" kicker={reg?.data.snapshot_id}>
        <p className="text-sm">
          Mode {reg?.data.data_mode}. Degraded={String(reg?.data.degraded)}. Assessment year{" "}
          {String(reg?.data.assessment_year?.value ?? "—")}.
        </p>
        {reg?.data.conflicts?.length ? (
          <ul className="mt-3 text-sm text-seal">
            {reg.data.conflicts.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        ) : null}
        <ul className="mt-4 space-y-2 text-sm">
          {reg?.data.sources?.slice(0, 8).map((s) => (
            <li key={s.url}>
              {s.title} — {s.verification} — {s.as_of}
            </li>
          ))}
        </ul>
      </Panel>
      <Panel title="Market research" kicker="Not market timing">
        <p className="text-sm">Macro state: {mkt?.data.macro_state ?? "—"}</p>
        <ul className="mt-3 list-disc pl-5 text-sm">
          {(mkt?.data.notes || []).map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
