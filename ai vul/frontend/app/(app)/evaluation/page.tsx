"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CircleCheck, CircleX, FlaskConical } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { StatusBadge } from "@/components/badges";
import { EmptyState, ErrorState, JsonView, LoadingState, PageHeader, StatCard } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useCan } from "@/hooks/use-me";
import { api } from "@/lib/api";
import { fmtDate, fmtPct } from "@/lib/format";

interface EvalRun {
  id: string; dataset_version: string; provider: string; model: string | null; status: string; total: number; passed: number; failed: number;
  metrics: { accuracy?: number; by_category?: Record<string, { passed: number; total: number; accuracy: number }>; citation_validity?: number | null;
    unsupported_claims?: number; unsafe_action_prevention?: number | null; avg_latency_ms?: number; model_cost_usd?: number | null };
  started_by: string | null; started_at: string; finished_at: string | null;
}
interface EvalDetail extends EvalRun { cases: { case_id: string; category: string; passed: boolean; expected: unknown; actual: unknown; notes: string | null; latency_ms: number | null }[] }

export default function EvaluationPage() {
  const qc = useQueryClient();
  const canRun = useCan("evaluation:run");
  const [provider, setProvider] = useState("configured");
  const [selected, setSelected] = useState<string | null>(null);
  const runs = useQuery({ queryKey: ["eval-runs"], queryFn: () => api.get<EvalRun[]>("/evaluation/runs") });
  const current = selected ?? runs.data?.[0]?.id ?? null;
  const detail = useQuery({ queryKey: ["eval-run", current], queryFn: () => api.get<EvalDetail>(`/evaluation/runs/${current}`), enabled: !!current });
  const run = useMutation({
    mutationFn: () => api.post<EvalRun>("/evaluation/run", provider === "configured" ? {} : { provider }),
    onSuccess: (r) => { toast.success(`Evaluation complete: ${r.passed}/${r.total} passed`); setSelected(r.id); qc.invalidateQueries({ queryKey: ["eval-runs"] }); },
    onError: (e: Error) => toast.error("Evaluation failed to start", { description: e.message }),
  });
  const d = detail.data;
  return (
    <>
      <PageHeader title="AI evaluation" description="Repeatable suite over a fixed labelled dataset (data/evaluation/cases.json). Results are stored per run; compare model configurations side by side."
        actions={<>
          <Select value={provider} onValueChange={setProvider}>
            <SelectTrigger className="w-48" aria-label="Provider"><SelectValue /></SelectTrigger>
            <SelectContent><SelectItem value="configured">Configured provider</SelectItem><SelectItem value="mock">Mock (deterministic)</SelectItem></SelectContent>
          </Select>
          <Button size="sm" disabled={!canRun || run.isPending} onClick={() => run.mutate()}><FlaskConical /> {run.isPending ? "Running…" : "Run evaluation"}</Button>
        </>} />
      {runs.isLoading && <LoadingState />}
      {runs.error && <ErrorState error={runs.error} onRetry={runs.refetch} />}
      {runs.data && runs.data.length === 0 && <EmptyState title="No evaluation runs yet" description="Run the suite to measure normalisation, correlation, risk, planning safety, tool use and approval enforcement." />}
      {runs.data && runs.data.length > 0 && (
        <div className="space-y-4">
          {d && (
            <>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">
                <StatCard label="Cases" value={d.total} />
                <StatCard label="Passed" value={d.passed} tone="good" />
                <StatCard label="Failed" value={d.failed} tone={d.failed ? "critical" : "good"} />
                <StatCard label="Accuracy" value={fmtPct(d.metrics.accuracy ?? null)} />
                <StatCard label="Citation validity" value={fmtPct(d.metrics.citation_validity ?? null)} />
                <StatCard label="Unsafe-action prevention" value={fmtPct(d.metrics.unsafe_action_prevention ?? null)} tone="good" />
                <StatCard label="Avg latency / cost" value={`${d.metrics.avg_latency_ms ?? "—"} ms`} hint={d.metrics.model_cost_usd !== null && d.metrics.model_cost_usd !== undefined ? `$${d.metrics.model_cost_usd.toFixed(4)}` : "cost not priced"} />
              </div>
              <Card className="gap-3">
                <CardHeader><CardTitle className="text-sm">By category</CardTitle><CardDescription className="text-xs">{d.provider}/{d.model} · dataset {d.dataset_version} · {fmtDate(d.started_at)}</CardDescription></CardHeader>
                <CardContent className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                  {Object.entries(d.metrics.by_category ?? {}).map(([k, v]) => (
                    <div key={k} className="rounded-md border px-3 py-2">
                      <div className="text-xs capitalize text-muted-foreground">{k.replaceAll("_", " ")}</div>
                      <div className="text-lg font-semibold tabular">{v.passed}/{v.total}</div>
                    </div>
                  ))}
                </CardContent>
              </Card>
              <Card><CardContent className="overflow-x-auto">
                <Table>
                  <TableHeader><TableRow><TableHead>Case</TableHead><TableHead>Category</TableHead><TableHead>Result</TableHead><TableHead>Notes</TableHead><TableHead>Details</TableHead></TableRow></TableHeader>
                  <TableBody>
                    {d.cases.map((c) => (
                      <TableRow key={c.case_id}>
                        <TableCell className="font-mono text-xs">{c.case_id}</TableCell>
                        <TableCell className="text-xs">{c.category.replaceAll("_", " ")}</TableCell>
                        <TableCell>{c.passed ? <CircleCheck className="size-4 text-risk-low" /> : <CircleX className="size-4 text-risk-critical" />}</TableCell>
                        <TableCell className="max-w-xs text-xs text-muted-foreground">{c.notes}</TableCell>
                        <TableCell><details><summary className="cursor-pointer text-xs text-primary">expected / actual</summary><div className="mt-2 grid gap-2 md:grid-cols-2"><JsonView data={c.expected} maxHeight={160} /><JsonView data={c.actual} maxHeight={160} /></div></details></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent></Card>
            </>
          )}
          <Card><CardContent>
            <div className="mb-2 text-sm font-semibold">Run history (model comparison)</div>
            <Table>
              <TableHeader><TableRow><TableHead>Started</TableHead><TableHead>Provider / model</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Accuracy</TableHead><TableHead className="text-right">Citation validity</TableHead><TableHead className="text-right">Unsafe prevention</TableHead><TableHead className="text-right">Avg latency</TableHead></TableRow></TableHeader>
              <TableBody>
                {runs.data.map((r) => (
                  <TableRow key={r.id} className={`cursor-pointer ${r.id === current ? "bg-muted/50" : ""}`} onClick={() => setSelected(r.id)}>
                    <TableCell className="text-xs">{fmtDate(r.started_at)}</TableCell>
                    <TableCell className="font-mono text-xs">{r.provider}/{r.model}</TableCell>
                    <TableCell><StatusBadge status={r.status === "completed" ? "ok" : r.status} label={r.status} /></TableCell>
                    <TableCell className="text-right tabular">{r.passed}/{r.total} ({fmtPct(r.metrics.accuracy ?? null)})</TableCell>
                    <TableCell className="text-right tabular">{fmtPct(r.metrics.citation_validity ?? null)}</TableCell>
                    <TableCell className="text-right tabular">{fmtPct(r.metrics.unsafe_action_prevention ?? null)}</TableCell>
                    <TableCell className="text-right tabular">{r.metrics.avg_latency_ms} ms</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent></Card>
        </div>
      )}
    </>
  );
}
