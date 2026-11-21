"use client";
import Link from "next/link";
import { use } from "react";
import { Alert, Badge, Card, Kv, Spinner, StatusBadge, when } from "@/components/ui";
import { useApi } from "@/lib/hooks";

type Trace = {
  id: string; kind: string; mode: string; state: string; status: string; error: string | null; correlation_id: string | null;
  usage: { model_calls?: number; tokens_in?: number; tokens_out?: number; cost_usd?: number; ocr_pages?: number };
  budget: { max_model_calls?: number; max_cost_usd?: number; max_ocr_pages?: number }; created_at: string; finished_at: string | null;
  tasks: { id: string; stage: string; status: string; attempts: number; max_attempts: number; duration_ms: number | null; error: string | null }[];
  agent_executions: { id: string; agent: string; mode: string; model: string | null; status: string; tools: { tool: string; ms: number; input_digest: string; output_digest: string }[];
    input_artifacts: string[]; output_artifact: string | null; retries: number; tokens_in: number; tokens_out: number; cost_usd: number; duration_ms: number; error: string | null; created_at: string }[];
};

export default function RunTrace({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, error } = useApi<Trace>(`/runs/${id}`, (d) => (d?.status === "running" ? 1500 : undefined));
  if (error) return <Alert tone="bad">{error}</Alert>;
  if (!data) return <Spinner />;
  const totalMs = data.tasks.reduce((a, t) => a + (t.duration_ms ?? 0), 0);
  return (
    <div className="space-y-5">
      <h1 className="text-xl font-semibold">Workflow trace</h1>
      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="Run">
          <Kv items={[["Run", <span key="r" className="font-mono text-xs">{data.id}</span>], ["Kind", data.kind],
            ["Processing mode", <Badge key="m" tone={data.mode === "demo" ? "warn" : "info"}>{data.mode === "demo" ? "demo — deterministic local adapters, no model calls" : "live — eve agents via Vercel AI Gateway"}</Badge>],
            ["Status", <StatusBadge key="s" status={data.status} />], ["State", data.state], ["Correlation ID", <span key="c" className="font-mono text-xs">{data.correlation_id}</span>],
            ["Started / finished", `${when(data.created_at)} / ${when(data.finished_at)}`], ["Stage time", `${(totalMs / 1000).toFixed(2)} s`]]} />
          {data.error && <div className="mt-3"><Alert tone="bad">{data.error}</Alert></div>}
        </Card>
        <Card title="Cost and budget (per document)">
          <Kv items={[["Model calls", `${data.usage.model_calls ?? 0} / ${data.budget.max_model_calls ?? "∞"}`],
            ["Tokens in / out", `${data.usage.tokens_in ?? 0} / ${data.usage.tokens_out ?? 0}`],
            ["Estimated cost", `$${(data.usage.cost_usd ?? 0).toFixed(4)} / $${(data.budget.max_cost_usd ?? 0).toFixed(2)}`],
            ["OCR pages (local)", `${data.usage.ocr_pages ?? 0} / ${data.budget.max_ocr_pages ?? "∞"}`]]} />
        </Card>
      </div>
      <Card title="Durable stages (allowed transitions only)">
        <ol className="space-y-1 text-sm">
          {data.tasks.map((t) => (
            <li key={t.id} className="flex flex-wrap items-center gap-2">
              <span className="w-36 font-medium">{t.stage}</span><StatusBadge status={t.status} />
              <span className="text-xs text-muted">attempt {t.attempts}/{t.max_attempts}{t.duration_ms != null ? ` · ${t.duration_ms} ms` : ""}</span>
              {t.error && <span className="text-xs text-bad">{t.error}</span>}
            </li>
          ))}
        </ol>
      </Card>
      <Card title="Agent executions (which agent used which tool and produced which artifact)">
        <div className="space-y-3">
          {data.agent_executions.map((e) => (
            <div key={e.id} className="rounded border border-line p-3 text-sm">
              <div className="flex flex-wrap items-center gap-2"><span className="font-semibold">{e.agent}</span><Badge tone={e.mode === "demo" ? "warn" : "info"}>{e.mode}</Badge>{e.model && <Badge>{e.model}</Badge>}<StatusBadge status={e.status} />
                <span className="ml-auto text-xs text-muted">{e.duration_ms} ms · retries {e.retries} · tokens {e.tokens_in}/{e.tokens_out} · ${e.cost_usd.toFixed(4)}</span></div>
              {e.error && <Alert tone="bad">{e.error}</Alert>}
              <div className="mt-1 text-xs">Tools: {e.tools.map((t, i) => <code key={i} className="mr-2" title={`in ${t.input_digest} / out ${t.output_digest}`}>{t.tool} ({t.ms} ms)</code>)}</div>
              <div className="text-xs text-muted">Input artifacts: {e.input_artifacts.join(", ") || "—"} · Output artifact: {e.output_artifact ?? "—"}</div>
            </div>
          ))}
          {data.agent_executions.length === 0 && <p className="text-sm text-muted">No agent executions yet.</p>}
        </div>
      </Card>
      <Link href="/" className="text-sm text-brand hover:underline">← Dashboard</Link>
    </div>
  );
}
