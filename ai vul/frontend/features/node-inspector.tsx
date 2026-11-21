"use client";

import { StatusBadge } from "@/components/badges";
import { JsonView, KeyValue } from "@/components/common";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { fmtDate } from "@/lib/format";
import type { AgentExecution, ToolCall, WorkflowDetail } from "@/lib/types";

export function NodeInspector({ detail, node }: { detail: WorkflowDetail; node: string }) {
  const topo = detail.topology.nodes.find((n) => n.id === node);
  const executions = detail.executions.filter((e) => e.node_name === node);
  const execIds = new Set(executions.map((e) => e.id));
  const tools = detail.tool_calls.filter((t) => t.agent_execution_id && execIds.has(t.agent_execution_id));
  const events = detail.events.filter((e) => e.node === node);
  const latest: AgentExecution | undefined = executions[executions.length - 1];

  return (
    <div className="space-y-4">
      <div>
        <div className="text-sm font-semibold">{topo?.label ?? node}</div>
        <div className="text-xs text-muted-foreground">
          {topo?.agent ?? (topo?.kind === "human" ? "Human-in-the-loop interrupt" : topo?.kind === "gate" ? "Deterministic authorisation gate" : "System step")}
        </div>
      </div>
      {latest ? (
        <KeyValue cols={3} items={[
          ["Status", <StatusBadge key="s" status={latest.status === "completed" ? "success" : latest.status === "failed" ? "error" : latest.status} label={latest.status} />],
          ["Attempts", executions.length],
          ["Latency", latest.latency_ms !== null ? `${latest.latency_ms} ms` : "—"],
          ["Model", latest.model_provider ? `${latest.model_provider} / ${latest.model_name}` : "Deterministic (no LLM)"],
          ["Tokens", latest.prompt_tokens !== null ? `${latest.prompt_tokens} in / ${latest.completion_tokens} out` : "—"],
          ["Cost", latest.estimated_cost_usd !== null ? `$${latest.estimated_cost_usd.toFixed(5)}` : "not priced"],
        ]} />
      ) : (
        <p className="text-sm text-muted-foreground">No agent execution recorded for this step{events.length ? "; see events below." : " yet."}</p>
      )}
      <Tabs defaultValue="output">
        <TabsList>
          <TabsTrigger value="output">Output</TabsTrigger>
          <TabsTrigger value="input">Input</TabsTrigger>
          <TabsTrigger value="tools">Tool calls ({tools.length})</TabsTrigger>
          <TabsTrigger value="attempts">Attempts ({executions.length})</TabsTrigger>
          <TabsTrigger value="events">Events ({events.length})</TabsTrigger>
        </TabsList>
        <TabsContent value="output">{latest ? <JsonView data={latest.output} maxHeight={420} /> : <p className="text-sm text-muted-foreground">—</p>}</TabsContent>
        <TabsContent value="input">{latest ? <JsonView data={latest.input_summary} /> : <p className="text-sm text-muted-foreground">—</p>}</TabsContent>
        <TabsContent value="tools">
          <div className="space-y-2">
            {tools.length === 0 && <p className="text-sm text-muted-foreground">No tool calls (deterministic step or no tools permitted).</p>}
            {tools.map((t: ToolCall) => (
              <details key={t.id} className="rounded-md border px-3 py-2 text-xs">
                <summary className="flex cursor-pointer items-center gap-2">
                  <span className="font-mono font-medium">{t.tool_name}</span>
                  <StatusBadge status={t.status} />
                  {t.mutating && <StatusBadge status="warn" label="mutating" />}
                  <span className="ml-auto text-muted-foreground">{t.latency_ms} ms</span>
                </summary>
                <div className="mt-2 grid gap-2 md:grid-cols-2">
                  <div><div className="mb-1 text-muted-foreground">Arguments</div><JsonView data={t.arguments} maxHeight={200} /></div>
                  <div><div className="mb-1 text-muted-foreground">Result (redacted, truncated)</div><JsonView data={t.error ? { error: t.error } : t.result_summary} maxHeight={200} /></div>
                </div>
              </details>
            ))}
          </div>
        </TabsContent>
        <TabsContent value="attempts">
          <div className="space-y-2 text-xs">
            {executions.map((e) => (
              <div key={e.id} className="rounded-md border px-3 py-2">
                <div className="flex items-center gap-2">
                  Attempt {e.attempt} <StatusBadge status={e.status === "completed" ? "success" : "error"} label={e.status} />
                  <span className="ml-auto text-muted-foreground">{fmtDate(e.started_at)}</span>
                </div>
                {e.error && <p className="mt-1 text-risk-critical">{e.error}</p>}
                {e.validation_errors.length > 0 && (
                  <ul className="mt-1 list-disc pl-4 text-risk-medium">{e.validation_errors.map((v, i) => <li key={i}>{v}</li>)}</ul>
                )}
              </div>
            ))}
          </div>
        </TabsContent>
        <TabsContent value="events">
          <ul className="space-y-1 text-xs">
            {events.map((e) => (
              <li key={e.id} className="flex gap-2"><span className="tabular text-muted-foreground">{fmtDate(e.created_at)}</span>{e.message}</li>
            ))}
          </ul>
        </TabsContent>
      </Tabs>
    </div>
  );
}
