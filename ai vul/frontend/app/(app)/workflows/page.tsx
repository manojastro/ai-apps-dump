"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { StatusBadge } from "@/components/badges";
import { ErrorState, LoadingState, PageHeader } from "@/components/common";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { NodeInspector } from "@/features/node-inspector";
import { WorkflowGraph } from "@/features/workflow-graph";
import { useWorkflow } from "@/hooks/use-workflow";
import { api } from "@/lib/api";
import { fmtNum } from "@/lib/format";
import type { Page, Topology, WorkflowRun } from "@/lib/types";

interface AgentInfo { name: string; node: string; description: string; tools: string[]; boundary: string; retry_policy: string; uses_llm: boolean; evaluation_criteria: string[] }

function RunTrace({ runId }: { runId: string }) {
  const { data, error, isLoading, refetch } = useWorkflow(runId);
  const [node, setNode] = useState<string | null>(null);
  if (isLoading) return <LoadingState rows={8} />;
  if (error || !data) return <ErrorState error={error} onRetry={refetch} />;
  const failures = data.executions.filter((e) => e.status === "failed").length;
  const retries = data.executions.length - new Set(data.executions.map((e) => e.node_name)).size;
  const selected = node ?? data.executions.at(-1)?.node_name ?? "ingest";
  return (
    <div className="space-y-4">
      <Card className="gap-2">
        <CardHeader>
          <CardTitle className="flex flex-wrap items-center gap-2 text-sm">
            <Link className="text-primary hover:underline" href={`/investigations/${runId}`}>{data.run.cve_id} · {data.run.hostname}</Link>
            <StatusBadge status={data.run.status} />
          </CardTitle>
          <CardDescription className="text-xs">
            {data.executions.length} agent executions · {data.tool_calls.length} tool calls · {failures} failures · {retries} retries ·
            {" "}{fmtNum(data.run.prompt_tokens + data.run.completion_tokens)} tokens · {data.run.provider}/{data.run.model}
          </CardDescription>
        </CardHeader>
        <CardContent><WorkflowGraph topology={data.topology} states={data.node_states} selected={selected} onSelect={setNode} horizontal className="h-[340px]" /></CardContent>
      </Card>
      <Card><CardContent><NodeInspector detail={data} node={selected} /></CardContent></Card>
    </div>
  );
}

function WorkflowsContent() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const runs = useQuery({ queryKey: ["workflows", "picker"], queryFn: () => api.get<Page<WorkflowRun>>("/workflows?page_size=100") });
  const agents = useQuery({ queryKey: ["agents"], queryFn: () => api.get<{ agents: AgentInfo[]; topology: Topology }>("/agents") });
  const runId = params.get("run") ?? runs.data?.items[0]?.id ?? null;
  return (
    <>
      <PageHeader title="Agent workflow visualizer" description="The real LangGraph topology with execution state from persisted traces: inputs, outputs, tool calls, latency, validation failures, approval pauses and retries."
        actions={runs.data && (
          <Select value={runId ?? undefined} onValueChange={(v) => router.replace(`${pathname}?run=${v}`)}>
            <SelectTrigger className="w-80" aria-label="Workflow run"><SelectValue placeholder="Select a run" /></SelectTrigger>
            <SelectContent>{runs.data.items.map((r) => <SelectItem key={r.id} value={r.id}>{r.cve_id} · {r.hostname} · {r.status}</SelectItem>)}</SelectContent>
          </Select>
        )} />
      {runId ? <RunTrace key={runId} runId={runId} /> : runs.isLoading ? <LoadingState /> : <p className="text-sm text-muted-foreground">No workflow runs yet.</p>}
      {agents.data && (
        <div className="mt-6">
          <h2 className="mb-3 text-sm font-semibold">Agent catalogue</h2>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {agents.data.agents.map((a) => (
              <Card key={a.name} className="gap-2">
                <CardHeader><CardTitle className="text-sm">{a.name}</CardTitle><CardDescription className="text-xs">{a.description}</CardDescription></CardHeader>
                <CardContent className="space-y-1.5 text-xs">
                  <div><span className="text-muted-foreground">Tools:</span> {a.tools.length ? a.tools.map((t) => <code key={t} className="mr-1 rounded bg-muted px-1">{t}</code>) : "none (deterministic)"}</div>
                  <div><span className="text-muted-foreground">LLM:</span> {a.uses_llm ? "structured output, schema-validated" : "no"}</div>
                  <div><span className="text-muted-foreground">Boundary:</span> {a.boundary}</div>
                  <div><span className="text-muted-foreground">Retry:</span> {a.retry_policy}</div>
                  <div><span className="text-muted-foreground">Evaluated on:</span> {a.evaluation_criteria.join("; ")}</div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

export default function WorkflowsPage() {
  return <Suspense fallback={<LoadingState />}><WorkflowsContent /></Suspense>;
}
