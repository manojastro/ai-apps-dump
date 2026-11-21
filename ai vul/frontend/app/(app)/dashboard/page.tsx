"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Clock, Flame, RefreshCw, Server, ShieldAlert, Wrench } from "lucide-react";
import Link from "next/link";

import { KevBadge, RiskBadge } from "@/components/badges";
import { ChartCard, Donut, RISK_COLORS, SimpleArea, SimpleBar } from "@/components/charts";
import { ErrorState, LoadingState, PageHeader, StatCard } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { fmtDate } from "@/lib/format";

interface Dashboard {
  kpis: Record<string, number>;
  by_severity: { severity: string; count: number }[];
  risk_distribution: { bucket: string; count: number }[];
  discovery_trend: { week: string; discovered: number; remediated: number }[];
  by_business_service: { service: string; total: number; critical: number; high: number }[];
  sla_exposure: { priority: string; overdue: number; due_7d: number; within_sla: number }[];
  top_risks: { finding_id: string; cve_id: string; hostname: string; risk_score: number; risk_level: string; kev: boolean | null; business_service: string | null }[];
  generated_at: string;
}

function bucketColor(row: Record<string, unknown>): string {
  const start = Number(String(row.bucket).split("-")[0]);
  return start >= 85 ? RISK_COLORS.critical : start >= 70 ? RISK_COLORS.high : start >= 40 ? RISK_COLORS.medium : RISK_COLORS.low;
}

export default function DashboardPage() {
  const { data, error, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.get<Dashboard>("/dashboard"),
    refetchInterval: 30_000,
  });

  return (
    <>
      <PageHeader
        title="Executive dashboard"
        description="Contextual risk across Northstar Global Technologies. Every metric is computed live from persisted findings, approvals and ServiceNow records."
        actions={
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={isFetching ? "animate-spin" : ""} /> Refresh
          </Button>
        }
      />
      {isLoading && <LoadingState rows={8} />}
      {error && <ErrorState error={error} onRetry={refetch} />}
      {data && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <StatCard label="Open findings" value={data.kpis.open_findings} hint={`${data.kpis.open_vulnerabilities} distinct CVEs`} icon={<ShieldAlert className="size-4" />} />
            <StatCard label="Critical findings" value={data.kpis.critical_findings} tone="critical" hint="Deterministic risk ≥ 85" icon={<Flame className="size-4" />} />
            <StatCard label="High-risk assets" value={data.kpis.high_risk_assets} tone="warn" hint="Assets with critical/high findings" icon={<Server className="size-4" />} />
            <StatCard label="Known exploited (KEV)" value={data.kpis.known_exploited_findings} tone="critical" hint={`${data.kpis.known_exploited_cves} CVEs confirmed by CISA`} icon={<AlertTriangle className="size-4" />} />
            <StatCard label="Pending approvals" value={data.kpis.pending_approvals} tone="warn" hint="Awaiting human decision" icon={<Clock className="size-4" />} />
            <StatCard label="Plans in progress" value={data.kpis.plans_in_progress} hint="Approved, not yet verified" icon={<Wrench className="size-4" />} />
            <StatCard label="Verified remediations" value={data.kpis.verified_remediations} tone="good" hint="Confirmed by fresh scan evidence" icon={<CheckCircle2 className="size-4" />} />
            <StatCard label="ServiceNow sync failures" value={data.kpis.sync_failures} tone={data.kpis.sync_failures ? "critical" : "good"} hint={`${data.kpis.unresolved_asset_matches} unresolved asset match(es)`} icon={<RefreshCw className="size-4" />} />
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <ChartCard title="Open findings by severity" description="Vendor/NVD severity, before business context">
              <Donut data={data.by_severity} nameKey="severity" valueKey="count" colorOf={(n) => RISK_COLORS[n] ?? RISK_COLORS.unknown} />
            </ChartCard>
            <ChartCard title="Contextual risk distribution" description="Deterministic policy score (0–100)">
              <SimpleBar data={data.risk_distribution} x="bucket" bars={[{ key: "count", label: "Findings", color: "var(--chart-1)" }]} colors={bucketColor} />
            </ChartCard>
            <ChartCard title="SLA exposure by priority" description="Open findings vs. policy SLA due dates">
              <SimpleBar data={data.sla_exposure} x="priority" stacked bars={[
                { key: "overdue", label: "Overdue", color: RISK_COLORS.critical },
                { key: "due_7d", label: "Due ≤ 7d", color: RISK_COLORS.medium },
                { key: "within_sla", label: "Within SLA", color: RISK_COLORS.low },
              ]} />
            </ChartCard>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <ChartCard title="Discovery vs. remediation trend" description="Weekly first-seen and verified-remediated findings (12 weeks)">
              <SimpleArea data={data.discovery_trend} x="week" areas={[
                { key: "discovered", label: "Discovered", color: "var(--chart-2)" },
                { key: "remediated", label: "Verified remediated", color: "var(--chart-5)" },
              ]} />
            </ChartCard>
            <ChartCard title="Open findings by business service" description="Critical and high contextual risk highlighted" height={280}>
              <SimpleBar data={data.by_business_service} x="service" layout="vertical" stacked bars={[
                { key: "critical", label: "Critical", color: RISK_COLORS.critical },
                { key: "high", label: "High", color: RISK_COLORS.high },
              ]} />
            </ChartCard>
          </div>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-sm">Highest contextual risk</CardTitle>
              <Button variant="ghost" size="sm" asChild><Link href="/vulnerabilities">View all</Link></Button>
            </CardHeader>
            <CardContent className="divide-y">
              {data.top_risks.map((r) => (
                <Link key={r.finding_id} href={`/vulnerabilities?finding=${r.finding_id}`} className="flex flex-wrap items-center gap-3 py-2.5 text-sm hover:bg-muted/40">
                  <RiskBadge level={r.risk_level} score={r.risk_score} />
                  <span className="font-mono text-xs">{r.cve_id}</span>
                  <span className="text-muted-foreground">{r.hostname}</span>
                  <span className="ml-auto flex items-center gap-3 text-xs text-muted-foreground">
                    {r.business_service ?? "No business service"} <KevBadge kev={r.kev} />
                  </span>
                </Link>
              ))}
            </CardContent>
          </Card>
          <p className="text-right text-[11px] text-muted-foreground">Generated {fmtDate(data.generated_at)}</p>
        </div>
      )}
    </>
  );
}
