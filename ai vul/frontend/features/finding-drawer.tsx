"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BrainCircuit, ExternalLink, RefreshCw, ScanLine } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { KevBadge, RiskBadge, SeverityBadge, SimBadge, StatusBadge } from "@/components/badges";
import { ErrorState, KeyValue, LoadingState, Section } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { EvidenceTimeline } from "@/features/evidence";
import { RiskBreakdown } from "@/features/risk-breakdown";
import { useCan } from "@/hooks/use-me";
import { api } from "@/lib/api";
import { fmtDate, fmtPct } from "@/lib/format";
import type { FindingDetail } from "@/lib/types";

export function FindingDrawer({ findingId, onClose }: { findingId: string | null; onClose: () => void }) {
  const router = useRouter();
  const qc = useQueryClient();
  const canInvestigate = useCan("investigate");
  const canVerify = useCan("verification:submit");
  const { data, error, isLoading, refetch } = useQuery({
    queryKey: ["finding", findingId],
    queryFn: () => api.get<FindingDetail>(`/findings/${findingId}`),
    enabled: !!findingId,
  });

  const investigate = useMutation({
    mutationFn: () => api.post<{ workflow_run_id: string }>(`/findings/${findingId}/investigate`),
    onSuccess: (r) => {
      toast.success("Investigation started", { description: "Agents are running; follow progress live." });
      qc.invalidateQueries();
      router.push(`/investigations/${r.workflow_run_id}`);
    },
    onError: (e: Error) => toast.error("Could not start investigation", { description: e.message }),
  });
  const rescan = useMutation({
    mutationFn: () => api.post(`/findings/${findingId}/rescan`),
    onSuccess: () => {
      toast.success("Rescan evidence collected", { description: "Verification re-evaluated against the new scan." });
      qc.invalidateQueries();
    },
    onError: (e: Error) => toast.error("Rescan failed", { description: e.message }),
  });

  const activeRun = data?.workflow_runs.find((r) => !["completed", "rejected", "failed", "blocked", "cancelled"].includes(r.status));

  return (
    <Sheet open={!!findingId} onOpenChange={(o) => !o && onClose()}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-2xl">
        <SheetHeader>
          <SheetTitle className="flex flex-wrap items-center gap-2">
            {data ? (
              <>
                <span className="font-mono">{data.vulnerability.cve_id}</span>
                <span className="text-muted-foreground">on</span> {data.asset?.hostname ?? data.finding.reported_asset_identifier}
              </>
            ) : (
              "Finding"
            )}
          </SheetTitle>
          <SheetDescription>{data?.vulnerability.title ?? data?.finding.software ?? "Vulnerability finding detail"}</SheetDescription>
        </SheetHeader>
        <div className="space-y-6 px-4 pb-8">
          {isLoading && <LoadingState />}
          {error && <ErrorState error={error} onRetry={refetch} />}
          {data && (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <RiskBadge level={data.finding.risk_level} score={data.finding.risk_score} />
                <SeverityBadge severity={data.vulnerability.severity} />
                <KevBadge kev={data.vulnerability.kev} />
                <StatusBadge status={data.finding.status} />
                <StatusBadge status={data.finding.verification_state} />
                <StatusBadge status={data.finding.correlation_status} label={`CMDB ${data.finding.correlation_status}`} />
                {data.finding.scanner === "mock_defender" && <SimBadge label="Simulated Defender" />}
              </div>
              <div className="flex flex-wrap gap-2">
                {activeRun ? (
                  <Button asChild size="sm">
                    <Link href={`/investigations/${activeRun.id}`}><BrainCircuit /> Open active investigation</Link>
                  </Button>
                ) : (
                  <Button size="sm" disabled={!canInvestigate || investigate.isPending || data.finding.status === "closed"} onClick={() => investigate.mutate()}>
                    <BrainCircuit /> Start AI investigation
                  </Button>
                )}
                {data.finding.scanner === "mock_defender" && (
                  <Button size="sm" variant="outline" disabled={!canVerify || rescan.isPending} onClick={() => rescan.mutate()}>
                    <ScanLine /> Request rescan (verification evidence)
                  </Button>
                )}
                <Button size="sm" variant="ghost" onClick={() => refetch()}><RefreshCw /> Refresh</Button>
              </div>

              {data.risk && (
                <Section title="Why this risk score">
                  <RiskBreakdown risk={data.risk} />
                </Section>
              )}
              <Separator />
              <Section title="Vulnerability intelligence">
                <p className="text-sm leading-relaxed">{data.vulnerability.description ?? "No description available."}</p>
                <KeyValue items={[
                  ["CVSS", data.vulnerability.cvss_score !== null ? `${data.vulnerability.cvss_score} (v${data.vulnerability.cvss_version})` : "—"],
                  ["Vector", <span key="v" className="font-mono text-[11px]">{data.vulnerability.cvss_vector ?? "—"}</span>],
                  ["EPSS", data.vulnerability.epss_score !== null ? `${data.vulnerability.epss_score?.toFixed(4)} (p${fmtPct(data.vulnerability.epss_percentile, 0)})` : "—"],
                  ["KEV", data.vulnerability.kev ? `Added ${data.vulnerability.kev_date_added}, due ${data.vulnerability.kev_due_date}` : data.vulnerability.kev === false ? "Not listed" : "Unknown"],
                  ["Affected product", `${data.vulnerability.affected_vendor ?? "?"} / ${data.vulnerability.affected_product ?? "?"}`],
                  ["Evidence status", <StatusBadge key="e" status={data.vulnerability.evidence_status === "verified" ? "success" : "warn"} label={data.vulnerability.evidence_status} />],
                ]} />
                <div className="space-y-1 text-[11px] text-muted-foreground">
                  {Object.entries(data.vulnerability.intel_sources ?? {}).map(([k, v]) => (
                    <div key={k}><span className="font-medium uppercase">{k}</span>: {v.reference ?? v.origin} ({v.status}{v.fetched_at ? `, ${fmtDate(v.fetched_at)}` : ""})</div>
                  ))}
                </div>
              </Section>
              <Separator />
              <Section title="Affected asset">
                {data.asset ? (
                  <KeyValue items={[
                    ["Asset", <Link key="a" href={`/assets?asset=${data.asset.id}`} className="text-primary hover:underline">{data.asset.id} · {data.asset.hostname}</Link>],
                    ["Environment", data.asset.environment],
                    ["Criticality", data.asset.business_criticality],
                    ["Internet exposed", data.asset.internet_exposed === null ? "Unknown" : data.asset.internet_exposed ? "Yes" : "No"],
                    ["Business service", data.asset.business_service?.name],
                    ["Owner", data.asset.owner ?? <span className="text-risk-medium">Missing in CMDB</span>],
                    ["Installed software", `${data.finding.software} ${data.finding.software_version}`],
                    ["CMDB match", `${data.finding.source_evidence.match_rule ?? "—"} (${data.finding.correlation_confidence ?? "—"})`],
                  ]} />
                ) : (
                  <p className="rounded-md border border-risk-medium/30 bg-risk-medium/10 px-3 py-2 text-sm">
                    Scanner identifier <span className="font-mono">{data.finding.reported_asset_identifier}</span> ({data.finding.reported_ip}) could not be reliably matched to the CMDB ({data.finding.correlation_status}).
                    An investigation will pause for human review before any planning.
                  </p>
                )}
              </Section>
              <Separator />
              <Section title="Scan evidence (before / after)">
                <EvidenceTimeline evidence={data.evidence} />
              </Section>
              {(data.plans.length > 0 || data.workflow_runs.length > 0) && (
                <>
                  <Separator />
                  <Section title="Investigations & remediation">
                    <div className="space-y-2 text-sm">
                      {data.workflow_runs.map((r) => (
                        <Link key={r.id} href={`/investigations/${r.id}`} className="flex items-center gap-2 rounded-md border px-3 py-2 hover:bg-muted/50">
                          <BrainCircuit className="size-4 text-primary" /> Investigation {r.id.slice(0, 8)}
                          <StatusBadge status={r.status} className="ml-auto" /> <span className="text-xs text-muted-foreground">{fmtDate(r.started_at)}</span>
                        </Link>
                      ))}
                      {data.plans.map((p) => (
                        <Link key={p.id} href={`/remediation/${p.id}`} className="flex items-center gap-2 rounded-md border px-3 py-2 hover:bg-muted/50">
                          Plan rev {p.revision}: {p.title}
                          <StatusBadge status={p.lifecycle_stage} className="ml-auto" />
                        </Link>
                      ))}
                      {data.servicenow_records.map((r) => (
                        <div key={r.id} className="flex items-center gap-2 rounded-md border px-3 py-2">
                          <span className="font-mono text-xs">{r.number ?? "pending"}</span> {r.table_name}
                          {r.record_url && <a href={r.record_url} target="_blank" rel="noreferrer" className="text-primary"><ExternalLink className="size-3.5" /></a>}
                          <StatusBadge status={r.sync_state} className="ml-auto" />
                          <span className="text-xs text-muted-foreground">{r.external_state_label}</span>
                        </div>
                      ))}
                    </div>
                  </Section>
                </>
              )}
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
