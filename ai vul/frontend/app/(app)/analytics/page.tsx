"use client";

import { useQuery } from "@tanstack/react-query";
import { Info } from "lucide-react";

import { ChartCard, RISK_COLORS, SimpleArea, SimpleBar } from "@/components/charts";
import { ErrorState, LoadingState, PageHeader } from "@/components/common";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { api } from "@/lib/api";
import { fmtNum, fmtPct } from "@/lib/format";
import type { Metric } from "@/lib/types";

interface Analytics {
  metrics: Record<string, Metric>;
  backlog_by_priority: { priority: string; count: number }[];
  critical_exposure_trend: { week: string; open_critical: number }[];
  cost_by_provider: { provider_model: string; runs: number; prompt_tokens: number; completion_tokens: number; cost_usd: number; cost_known: boolean }[];
  agent_performance: { agent: string; completed?: number; failed?: number; avg_latency_ms: number | null }[];
}

const TITLES: Record<string, string> = {
  mean_investigation_duration: "Mean investigation duration",
  mean_time_to_remediation: "Mean time to remediation",
  remediation_backlog: "Remediation backlog",
  approval_turnaround: "Approval turnaround",
  investigation_success_rate: "Investigation success rate",
  verification_completion_rate: "Verification completion rate",
  agent_cost: "Agent cost",
  tool_failure_rate: "AI tool failure rate",
  tool_denials: "Blocked tool calls",
};

function render(m: Metric): string {
  if (m.value === null) return "n/a";
  if (m.unit === "ratio") return fmtPct(m.value, 1);
  if (m.unit === "USD") return `$${m.value.toFixed(4)}`;
  return `${fmtNum(m.value, m.unit === "hours" || m.unit === "days" ? 1 : 0)} ${m.unit}`;
}

export default function AnalyticsPage() {
  const { data, error, isLoading, refetch } = useQuery({ queryKey: ["analytics"], queryFn: () => api.get<Analytics>("/analytics") });
  return (
    <>
      <PageHeader title="Analytics" description="Operational and AI-quality metrics with explicit definitions and sample sizes. Values marked n/a have no qualifying data yet – nothing is estimated." />
      {isLoading && <LoadingState rows={8} />}
      {error && <ErrorState error={error} onRetry={refetch} />}
      {data && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(data.metrics).map(([k, m]) => (
              <Card key={k} className="gap-1 py-4">
                <CardContent className="px-4">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    {TITLES[k] ?? k}
                    <Tooltip>
                      <TooltipTrigger aria-label={`Definition of ${TITLES[k] ?? k}`}><Info className="size-3.5" /></TooltipTrigger>
                      <TooltipContent className="max-w-xs">{m.definition}</TooltipContent>
                    </Tooltip>
                  </div>
                  <div className="mt-1.5 text-2xl font-semibold tabular">{render(m)}</div>
                  <div className="mt-1 text-[11px] text-muted-foreground">{m.definition}{m.sample_size !== null && ` (n=${m.sample_size})`}</div>
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <ChartCard title="Critical exposure trend" description="Open findings with critical contextual risk at each week end">
              <SimpleArea data={data.critical_exposure_trend} x="week" areas={[{ key: "open_critical", label: "Open critical", color: RISK_COLORS.critical }]} />
            </ChartCard>
            <ChartCard title="Remediation backlog by priority" description="Open and in-remediation findings">
              <SimpleBar data={data.backlog_by_priority} x="priority" bars={[{ key: "count", label: "Findings", color: "var(--chart-2)" }]}
                colors={(r) => ({ P1: RISK_COLORS.critical, P2: RISK_COLORS.high, P3: RISK_COLORS.medium, P4: RISK_COLORS.low })[String(r.priority)] ?? "var(--chart-2)"} />
            </ChartCard>
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card><CardContent>
              <div className="mb-2 text-sm font-semibold">Agent performance</div>
              <Table><TableHeader><TableRow><TableHead>Agent</TableHead><TableHead className="text-right">Completed</TableHead><TableHead className="text-right">Failed</TableHead><TableHead className="text-right">Avg latency</TableHead></TableRow></TableHeader>
                <TableBody>{data.agent_performance.map((a) => (
                  <TableRow key={a.agent}><TableCell className="text-xs">{a.agent}</TableCell><TableCell className="text-right tabular">{a.completed ?? 0}</TableCell><TableCell className="text-right tabular">{a.failed ?? 0}</TableCell><TableCell className="text-right tabular">{a.avg_latency_ms ?? "—"} ms</TableCell></TableRow>
                ))}</TableBody></Table>
            </CardContent></Card>
            <Card><CardContent>
              <div className="mb-2 text-sm font-semibold">Model usage & cost</div>
              <Table><TableHeader><TableRow><TableHead>Provider / model</TableHead><TableHead className="text-right">Runs</TableHead><TableHead className="text-right">Tokens</TableHead><TableHead className="text-right">Cost</TableHead></TableRow></TableHeader>
                <TableBody>{data.cost_by_provider.map((p) => (
                  <TableRow key={p.provider_model}><TableCell className="font-mono text-xs">{p.provider_model}</TableCell><TableCell className="text-right tabular">{p.runs}</TableCell>
                    <TableCell className="text-right tabular">{fmtNum(p.prompt_tokens + p.completion_tokens)}</TableCell><TableCell className="text-right tabular">{p.cost_known ? `$${p.cost_usd.toFixed(4)}` : "pricing not configured"}</TableCell></TableRow>
                ))}</TableBody></Table>
            </CardContent></Card>
          </div>
        </div>
      )}
    </>
  );
}
