"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  BrainCircuit,
  CircleCheck,
  CircleDashed,
  CircleX,
  Clock,
  ExternalLink,
  Loader2,
  Radio,
  RefreshCw,
  ScanLine,
  ShieldCheck,
  UserCheck,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { KevBadge, RiskBadge, SimBadge, StatusBadge } from "@/components/badges";
import { ErrorState, KeyValue, LoadingState, PageHeader } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { NodeInspector } from "@/features/node-inspector";
import { RiskBreakdown } from "@/features/risk-breakdown";
import { WorkflowGraph } from "@/features/workflow-graph";
import { useCan } from "@/hooks/use-me";
import { useWorkflow } from "@/hooks/use-workflow";
import { api } from "@/lib/api";
import { fmtDate, fmtNum } from "@/lib/format";
import type { WorkflowDetail } from "@/lib/types";
import { cn } from "@/lib/utils";

const EVENT_ICON: Record<string, React.ReactNode> = {
  agent_completed: <CircleCheck className="size-3.5 text-risk-low" />,
  agent_started: <Loader2 className="size-3.5 text-primary" />,
  agent_failed: <CircleX className="size-3.5 text-risk-critical" />,
  human_input: <UserCheck className="size-3.5 text-primary" />,
  gate: <ShieldCheck className="size-3.5 text-primary" />,
  status: <Clock className="size-3.5 text-risk-medium" />,
};

function AgentChecklist({ detail }: { detail: WorkflowDetail }) {
  return (
    <ul className="space-y-1.5 text-xs">
      {detail.topology.nodes.filter((n) => n.kind !== "system" || n.id === "final_report").map((n) => {
        const s = detail.node_states[n.id]?.status;
        const icon = s === "completed" ? <CircleCheck className="size-3.5 text-risk-low" /> : s === "running" ? <Loader2 className="size-3.5 animate-spin text-primary" />
          : s === "waiting" ? <Clock className="size-3.5 text-risk-medium" /> : s === "failed" ? <CircleX className="size-3.5 text-risk-critical" /> : <CircleDashed className="size-3.5 text-muted-foreground" />;
        return (
          <li key={n.id} className={cn("flex items-center gap-2", !s && "text-muted-foreground")}>
            {icon}<span className="flex-1">{n.agent ?? n.label}</span><span className="capitalize text-muted-foreground">{s ?? "pending"}</span>
          </li>
        );
      })}
    </ul>
  );
}

function ActionPanel({ detail, refetch }: { detail: WorkflowDetail; refetch: () => void }) {
  const qc = useQueryClient();
  const canInvestigate = useCan("investigate");
  const canRequest = useCan("approval:request");
  const canSync = useCan("servicenow:sync");
  const canVerify = useCan("verification:submit");
  const [note, setNote] = useState("");
  const [candidate, setCandidate] = useState<string>("");
  const [requestOpen, setRequestOpen] = useState(false);
  const run = detail.run;
  const done = (msg: string) => () => { toast.success(msg); qc.invalidateQueries(); refetch(); };
  const fail = (e: Error) => toast.error(e.message);

  const review = useMutation({
    mutationFn: (action: string) => api.post(`/workflows/${run.id}/manual-review`, { action, asset_id: candidate || null, note: note || null }),
    onSuccess: done("Manual review decision recorded; workflow resumed"), onError: fail,
  });
  const requestApproval = useMutation({
    mutationFn: () => api.post(`/plans/${run.plan_id}/request-approval`, { comment: note || null }),
    onSuccess: () => { setRequestOpen(false); setNote(""); done("Approval requested")(); }, onError: fail,
  });
  const retry = useMutation({
    mutationFn: () => api.post(`/approvals/${detail.approval?.id}/retry-sync`),
    onSuccess: done("ServiceNow synchronisation retried"), onError: fail,
  });
  const rescan = useMutation({
    mutationFn: () => api.post(`/findings/${run.finding_id}/rescan`),
    onSuccess: done("Rescan evidence collected; verification agent evaluated it"), onError: fail,
  });

  const box = (title: string, body: React.ReactNode, tone: "warn" | "info" | "good" | "bad" = "info") => (
    <Card className={cn("gap-3 border-l-4", { warn: "border-l-risk-medium", info: "border-l-primary", good: "border-l-risk-low", bad: "border-l-risk-critical" }[tone])}>
      <CardHeader><CardTitle className="text-sm">{title}</CardTitle>{run.waiting_reason && <CardDescription className="text-xs">{run.waiting_reason}</CardDescription>}</CardHeader>
      <CardContent className="space-y-3">{body}</CardContent>
    </Card>
  );

  if (run.status === "waiting_manual_review") {
    return box("Human review required", (
      <>
        {detail.correlation_candidates.length > 0 && (
          <fieldset className="space-y-1.5">
            <legend className="mb-1 text-xs text-muted-foreground">Ambiguous CMDB match – choose the correct configuration item:</legend>
            {detail.correlation_candidates.map((c) => (
              <label key={c.asset_id} className="flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-xs has-[:checked]:border-primary">
                <input type="radio" name="candidate" value={c.asset_id} checked={candidate === c.asset_id} onChange={() => setCandidate(c.asset_id)} />
                <span className="font-medium">{c.asset_id}</span> {c.fqdn ?? c.hostname} · {c.ip_address} · {c.environment} · status {c.operational_status}
              </label>
            ))}
          </fieldset>
        )}
        <Textarea placeholder="Reviewer note (recorded in the audit log)" value={note} onChange={(e) => setNote(e.target.value)} rows={2} />
        <div className="flex flex-wrap gap-2">
          {detail.correlation_candidates.length > 0 && (
            <Button size="sm" disabled={!candidate || !canInvestigate || review.isPending} onClick={() => review.mutate("asset_resolved")}>Confirm asset match</Button>
          )}
          {run.plan_id && <Button size="sm" variant="outline" disabled={!canInvestigate || review.isPending} onClick={() => review.mutate("proceed")}>Acknowledge gaps & proceed</Button>}
          <Button size="sm" variant="ghost" disabled={!canInvestigate || review.isPending} onClick={() => review.mutate("dismiss")}>Dismiss investigation</Button>
        </div>
      </>
    ), "warn");
  }
  if (run.status === "waiting_approval") {
    const pending = detail.approval?.state === "PENDING";
    return box(pending ? "Awaiting approver decision" : "Plan ready for approval", (
      <>
        <p className="text-sm">{pending ? `Requested by ${detail.approval?.requested_by_name} ${fmtDate(detail.approval?.created_at)}. An authorised approver must decide in the Approval Center.`
          : "Review the evidence-linked plan, edit it if needed, then submit it for human approval. Nothing is written to ServiceNow before approval."}</p>
        <div className="flex flex-wrap gap-2">
          {!pending && <Button size="sm" disabled={!canRequest || !run.plan_id} onClick={() => setRequestOpen(true)}>Request approval</Button>}
          {run.plan_id && <Button size="sm" variant="outline" asChild><Link href={`/remediation/${run.plan_id}`}>Open remediation plan</Link></Button>}
          {pending && <Button size="sm" variant="outline" asChild><Link href={`/approvals?focus=${detail.approval?.id}`}>Open Approval Center</Link></Button>}
        </div>
        <Dialog open={requestOpen} onOpenChange={setRequestOpen}>
          <DialogContent>
            <DialogHeader><DialogTitle>Request approval</DialogTitle><DialogDescription>The current plan content is snapshotted and hashed. Any later edit invalidates this request.</DialogDescription></DialogHeader>
            <Label htmlFor="req-note">Comment for the approver</Label>
            <Textarea id="req-note" value={note} onChange={(e) => setNote(e.target.value)} rows={3} />
            <DialogFooter><Button onClick={() => requestApproval.mutate()} disabled={requestApproval.isPending}>Submit for approval</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </>
    ), "warn");
  }
  if (run.status === "waiting_sync_retry") {
    return box("ServiceNow synchronisation failed", (
      <>
        <p className="text-sm">The approved change could not be confirmed in ServiceNow. Retrying is safe: the sync service reconciles by correlation ID before creating, so no duplicate record can be created.</p>
        <Button size="sm" disabled={!canSync || retry.isPending} onClick={() => retry.mutate()}><RefreshCw /> Retry synchronisation</Button>
      </>
    ), "bad");
  }
  if (run.status === "waiting_evidence") {
    return box("Tracking remediation – awaiting scan evidence", (
      <>
        <p className="text-sm">Closing the ServiceNow task does not verify remediation. Collect a fresh scan of the asset; the Verification Agent compares it with the baseline.</p>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" disabled={!canVerify || rescan.isPending} onClick={() => rescan.mutate()}><ScanLine /> Request rescan</Button>
          {run.plan_id && <Button size="sm" variant="outline" asChild><Link href={`/remediation/${run.plan_id}#simulation`}>Simulation console</Link></Button>}
        </div>
      </>
    ));
  }
  if (run.status === "completed") return box("Investigation closed with evidence", <p className="text-sm">{String(run.summary?.outcome ?? "completed").replace("_", " ")} · closed {fmtDate(run.completed_at)}</p>, "good");
  if (run.status === "rejected") return box("Plan rejected – no external write performed", <p className="text-sm">{detail.approval?.decision_comment}</p>, "bad");
  if (run.status === "blocked" || run.status === "failed") return box(`Workflow ${run.status}`, <p className="text-sm text-risk-critical">{run.error ?? run.waiting_reason}</p>, "bad");
  return box("Agents running", <p className="flex items-center gap-2 text-sm"><Loader2 className="size-4 animate-spin" /> The multi-agent investigation is executing…</p>);
}

export default function InvestigationPage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, isLoading, refetch, live } = useWorkflow(id);
  const [selected, setSelected] = useState<string | null>(null);

  if (isLoading) return <LoadingState rows={12} />;
  if (error || !data) return <ErrorState error={error} onRetry={refetch} />;
  const { run, finding } = data;
  const threat = data.executions.findLast((e) => e.node_name === "enrich_threat" && e.status === "completed")?.output as Record<string, unknown> | undefined;
  const vuln = data.executions.findLast((e) => e.node_name === "normalize" && e.status === "completed")?.output as Record<string, unknown> | undefined;

  return (
    <>
      <PageHeader
        title={`${run.cve_id} · ${run.hostname}`}
        description={`Investigation ${run.id.slice(0, 8)} started ${fmtDate(run.started_at)}`}
        badge={<StatusBadge status={run.status} />}
        actions={
          <>
            <span className={cn("flex items-center gap-1.5 text-xs", live === "streaming" ? "text-risk-low" : "text-muted-foreground")}>
              <Radio className="size-3.5" /> {live === "streaming" ? "Live (SSE)" : live === "polling" ? "Live (polling)" : "Idle"}
            </span>
            <Button variant="outline" size="sm" asChild><Link href={`/workflows?run=${run.id}`}><BrainCircuit /> Trace view</Link></Button>
          </>
        }
      />
      <div className="grid gap-4 xl:grid-cols-[minmax(300px,0.9fr)_minmax(0,1.3fr)_minmax(300px,1fr)]">
        <div className="space-y-4">
          <Card className="gap-2">
            <CardHeader><CardTitle className="text-sm">Agent workflow</CardTitle><CardDescription className="text-xs">Click a node to inspect inputs, outputs and tool calls.</CardDescription></CardHeader>
            <CardContent><WorkflowGraph topology={data.topology} states={data.node_states} selected={selected} onSelect={setSelected} className="h-[560px]" /></CardContent>
          </Card>
          <Card><CardContent><AgentChecklist detail={data} /></CardContent></Card>
        </div>

        <div className="space-y-4">
          <ActionPanel detail={data} refetch={refetch} />
          <Card className="gap-2">
            <CardHeader><CardTitle className="text-sm">Investigation timeline</CardTitle><CardDescription className="text-xs">Durable event log – survives refreshes and restarts.</CardDescription></CardHeader>
            <CardContent>
              <ol className="max-h-[640px] space-y-2 overflow-y-auto pr-1">
                {[...data.events].reverse().map((e) => (
                  <li key={e.id} className="flex gap-2.5 text-sm">
                    <span className="mt-0.5">{EVENT_ICON[e.event_type] ?? <CircleDashed className="size-3.5 text-muted-foreground" />}</span>
                    <div className="min-w-0 flex-1">
                      <button className="text-left hover:underline" onClick={() => e.node && setSelected(e.node)}>{e.message}</button>
                      {e.event_type === "agent_completed" && e.payload.summary !== undefined && (
                        <div className="mt-0.5 font-mono text-[10px] text-muted-foreground">{JSON.stringify(e.payload.summary).slice(0, 160)}</div>
                      )}
                      {e.event_type === "gate" && Array.isArray(e.payload.reasons) && e.payload.reasons.length > 0 && (
                        <div className="mt-0.5 text-[11px] text-risk-critical">{(e.payload.reasons as string[]).join("; ")}</div>
                      )}
                    </div>
                    <span className="shrink-0 text-[10px] tabular text-muted-foreground">{new Date(e.created_at).toLocaleTimeString()}</span>
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          {data.risk ? (
            <Card className="gap-3"><CardHeader><CardTitle className="text-sm">Deterministic risk assessment</CardTitle></CardHeader><CardContent><RiskBreakdown risk={data.risk} compact /></CardContent></Card>
          ) : finding && (
            <Card><CardContent className="flex items-center gap-2 text-sm"><RiskBadge level={finding.risk_level} score={finding.risk_score} /> preliminary score (ingestion)</CardContent></Card>
          )}
          {threat && (
            <Card className="gap-3">
              <CardHeader><CardTitle className="text-sm">Threat context</CardTitle></CardHeader>
              <CardContent className="space-y-2 text-xs">
                <div className="flex items-center gap-2"><KevBadge kev={threat.known_exploited as boolean | null} /> EPSS {String(threat.epss_probability ?? "n/a")}</div>
                <ul className="list-disc space-y-1 pl-4 text-muted-foreground">{(threat.risk_notes as string[]).map((n) => <li key={n}>{n}</li>)}</ul>
              </CardContent>
            </Card>
          )}
          {vuln && (
            <Card className="gap-3">
              <CardHeader><CardTitle className="text-sm">Vulnerability intelligence</CardTitle></CardHeader>
              <CardContent className="space-y-2 text-xs">
                <KeyValue items={[["Data quality", `${vuln.data_quality} (${vuln.confidence})`], ["Verified source", vuln.verified ? "Yes" : "No"], ["Installed", `${vuln.affected_product} ${vuln.affected_version}`], ["NVD fixed version", String(vuln.fixed_version_per_nvd ?? "not stated")]]} />
                <p className="text-muted-foreground">{String(vuln.range_evidence ?? "")}</p>
              </CardContent>
            </Card>
          )}
          {data.asset && (
            <Card className="gap-3">
              <CardHeader><CardTitle className="text-sm">Asset context <SimBadge label="CMDB" /></CardTitle></CardHeader>
              <CardContent><KeyValue items={[["Host", data.asset.hostname], ["Environment", data.asset.environment], ["Criticality", data.asset.business_criticality], ["Exposed", data.asset.internet_exposed === null ? "Unknown" : data.asset.internet_exposed ? "Yes" : "No"], ["Service", data.asset.business_service?.name], ["Owner", data.asset.owner ?? "Missing"]]} /></CardContent>
            </Card>
          )}
          {data.plan && (
            <Card className="gap-3">
              <CardHeader><CardTitle className="text-sm">Remediation plan</CardTitle><CardDescription className="text-xs">rev {data.plan.revision} · {data.plan.generated_by}</CardDescription></CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>{data.plan.recommended_action}</p>
                <div className="flex flex-wrap gap-2"><StatusBadge status={data.plan.lifecycle_stage} />{data.plan.requires_expert_validation && <StatusBadge status="warn" label="Expert validation required" />}</div>
                <Button size="sm" variant="outline" asChild><Link href={`/remediation/${data.plan.id}`}><ExternalLink /> Full plan, change impact & evidence</Link></Button>
              </CardContent>
            </Card>
          )}
          <Card><CardContent className="text-xs text-muted-foreground">
            Model {run.provider}/{run.model ?? "—"} · tokens {fmtNum(run.prompt_tokens + run.completion_tokens)} · cost {run.estimated_cost_usd !== null ? `$${run.estimated_cost_usd.toFixed(5)}` : "not priced"} · resumes {run.resume_count}
          </CardContent></Card>
        </div>
      </div>
      <Dialog open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-3xl">
          <DialogHeader><DialogTitle>Step inspector</DialogTitle><DialogDescription>Secrets are redacted before storage.</DialogDescription></DialogHeader>
          {selected && <NodeInspector detail={data} node={selected} />}
        </DialogContent>
      </Dialog>
    </>
  );
}
