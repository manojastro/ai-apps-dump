"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { KEYS, readKey } from "@/lib/session";
import { Panel } from "@/components/Panel";

type Agent = {
  agent: string;
  status: string;
  message: string;
};

const NAMES = [
  "profile_analyst",
  "holdings_analyst",
  "regulatory_research",
  "macro_research",
  "universe_research",
  "construction",
  "risk_officer",
  "plan_critic",
];

export default function WarRoomPage() {
  const [status, setStatus] = useState("queued");
  const [progress, setProgress] = useState(0);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [planId, setPlanId] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const id = readKey(KEYS.plan);
    setPlanId(id);
    if (!id) return;
    let stop = false;
    async function tick() {
      try {
        const res = await api<{
          data: { status: string; progress_pct: number; agents: Agent[]; message: string };
        }>(`/api/v1/plans/${id}/status`);
        if (stop) return;
        setStatus(res.data.status);
        setProgress(res.data.progress_pct);
        setAgents(res.data.agents || []);
        setMessage(res.data.message);
        if (["complete", "warning", "failed"].includes(res.data.status)) return;
      } catch {
        /* still generating */
      }
      setTimeout(tick, 800);
    }
    void tick();
    return () => {
      stop = true;
    };
  }, []);

  const latest = new Map(agents.map((a) => [a.agent, a]));

  return (
    <div>
      <Panel title="Research war room" kicker={planId || "No plan in session"}>
        <p className="text-sm">
          Status {status} · {progress}% · {message}. Chain-of-thought is not shown.
        </p>
        <div className="mt-6 grid gap-3 md:grid-cols-2">
          {NAMES.map((name) => {
            const row = latest.get(name);
            const st = row?.status || "queued";
            return (
              <div key={name} className="border border-rule p-4">
                <div className="flex items-baseline justify-between gap-2">
                  <h3 className="font-display text-lg text-navy">{name.replaceAll("_", " ")}</h3>
                  <span className="text-xs text-brass">{st}</span>
                </div>
                <p className="mt-2 text-sm text-ink/80">{row?.message || "Waiting for high-level event."}</p>
              </div>
            );
          })}
        </div>
        {["complete", "warning"].includes(status) && planId ? (
          <Link href="/compare" className="mt-6 inline-block bg-navy px-4 py-2 text-sm text-paper">
            Compare scenarios
          </Link>
        ) : null}
      </Panel>
    </div>
  );
}
