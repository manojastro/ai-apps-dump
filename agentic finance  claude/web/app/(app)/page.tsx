"use client";
import Link from "next/link";
import { useState } from "react";
import { useSession } from "@/components/shell";
import { Alert, Badge, Button, Card, Field, inputClass, Spinner, StatusBadge, when } from "@/components/ui";
import { errorText, post } from "@/lib/api";
import { useApi } from "@/lib/hooks";

type Dash = {
  workspace: { id: string; name: string; role: string; retention_days: number };
  agent_mode: string;
  companies: { id: string; name: string; industry: string | null; supported: boolean; unsupported_reason: string | null;
    spreads: { id: string; scope: string; currency: string; version: number; review_status: string }[] }[];
  open_exceptions: Record<string, number>;
  runs: Record<string, number>;
  correction_rate: number;
  observations: number;
  cost: { usd: number; tokens_in: number; tokens_out: number };
  recent_runs: { id: string; status: string; state: string; mode: string; created_at: string }[];
};

export default function Dashboard() {
  const { workspaceId } = useSession();
  const { data, error, reload } = useApi<Dash>(workspaceId ? `/workspaces/${workspaceId}/dashboard` : null, 5000);
  const [name, setName] = useState("");
  const [msg, setMsg] = useState<string>();

  if (!workspaceId) return <Spinner />;
  if (error) return <Alert tone="bad">{error}</Alert>;
  if (!data) return <Spinner />;

  async function createCompany(e: React.FormEvent) {
    e.preventDefault();
    try {
      await post(`/workspaces/${workspaceId}/companies`, { name });
      setName("");
      setMsg(undefined);
      reload();
    } catch (err) { setMsg(errorText(err)); }
  }

  const stat = (label: string, value: React.ReactNode, tone?: "bad" | "warn") => (
    <div className="rounded-lg border border-line bg-panel p-3">
      <div className="text-xs text-muted">{label}</div>
      <div className={`mt-1 text-xl font-semibold ${tone === "bad" ? "text-bad" : tone === "warn" ? "text-warn" : ""}`}>{value}</div>
    </div>
  );

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="text-xl font-semibold">{data.workspace.name}</h1>
        <span className="text-sm text-muted">Role: {data.workspace.role} · Retention {data.workspace.retention_days} days</span>
      </div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        {stat("Companies", data.companies.length)}
        {stat("Critical open", data.open_exceptions.critical ?? 0, (data.open_exceptions.critical ?? 0) > 0 ? "bad" : undefined)}
        {stat("Review queue (warnings)", data.open_exceptions.warning ?? 0, (data.open_exceptions.warning ?? 0) > 0 ? "warn" : undefined)}
        {stat("Runs in progress / waiting", `${data.runs.running ?? 0} / ${data.runs.awaiting_input ?? 0}`)}
        {stat("Analyst correction rate", `${(data.correction_rate * 100).toFixed(1)}% of ${data.observations}`)}
        {stat("Model cost (est.)", `$${data.cost.usd.toFixed(4)}`)}
      </div>
      {data.agent_mode === "demo" && (
        <Alert tone="warn">Demo processing: agents use deterministic local adapters. No model calls are made and no document content leaves this machine.</Alert>
      )}
      <div className="grid gap-5 lg:grid-cols-3">
        <Card title="Companies" className="lg:col-span-2">
          <form onSubmit={createCompany} className="mb-4 flex flex-wrap items-end gap-2">
            <div className="min-w-64 flex-1"><Field label="New company"><input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} placeholder="Company name" required /></Field></div>
            <Button type="submit">Create company</Button>
          </form>
          {msg && <Alert tone="bad">{msg}</Alert>}
          <ul className="divide-y divide-line">
            {data.companies.map((c) => (
              <li key={c.id} className="flex flex-wrap items-center gap-3 py-2.5">
                <Link href={`/companies/${c.id}`} className="font-medium text-brand underline-offset-2 hover:underline">{c.name}</Link>
                {!c.supported && <Badge tone="bad" title={c.unsupported_reason ?? ""}>unsupported entity type</Badge>}
                <div className="ml-auto flex flex-wrap gap-2">
                  {c.spreads.map((s) => (
                    <Link key={s.id} href={`/spreads/${s.id}`} className="flex items-center gap-1.5 rounded border border-line px-2 py-0.5 text-xs hover:bg-bg">
                      {s.scope} · {s.currency} · v{s.version} <StatusBadge status={s.review_status} />
                    </Link>
                  ))}
                  {c.spreads.length === 0 && <span className="text-xs text-muted">no spreads yet</span>}
                </div>
              </li>
            ))}
            {data.companies.length === 0 && <li className="py-3 text-sm text-muted">No companies yet.</li>}
          </ul>
        </Card>
        <Card title="Recent processing runs">
          <ul className="space-y-2 text-sm">
            {data.recent_runs.map((r) => (
              <li key={r.id} className="flex items-center justify-between gap-2">
                <Link href={`/runs/${r.id}`} className="text-brand hover:underline">{r.state}</Link>
                <span className="flex items-center gap-1.5"><Badge>{r.mode}</Badge><StatusBadge status={r.status} /></span>
                <span className="text-xs text-muted">{when(r.created_at)}</span>
              </li>
            ))}
            {data.recent_runs.length === 0 && <li className="text-muted">No runs yet.</li>}
          </ul>
        </Card>
      </div>
    </div>
  );
}
