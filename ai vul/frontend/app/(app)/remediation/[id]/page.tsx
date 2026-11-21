"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, BrainCircuit, Download, ExternalLink, FileSearch, Pencil, RefreshCw, Send } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { KevBadge, RiskBadge, SeverityBadge, SimBadge, StatusBadge } from "@/components/badges";
import { ErrorState, KeyValue, LoadingState, PageHeader, Section } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { RiskBreakdown } from "@/features/risk-breakdown";
import { SimulationConsole } from "@/features/simulation-console";
import { useCan } from "@/hooks/use-me";
import { api, downloadFile } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import type { Approval, Asset, ChangeImpact, FindingDetail, FindingRow, Plan, RiskAssessment, ServiceNowRecord, Vulnerability } from "@/lib/types";

interface PlanResponse {
  plan: Plan;
  finding: FindingRow | null;
  vulnerability: Vulnerability | null;
  asset: Asset | null;
  risk: RiskAssessment | null;
  approvals: Approval[];
  servicenow_records: ServiceNowRecord[];
}

const lines = (v: string) => v.split("\n").map((s) => s.trim()).filter(Boolean);

function EditDialog({ plan, open, onOpenChange }: { plan: Plan; open: boolean; onOpenChange: (v: boolean) => void }) {
  const qc = useQueryClient();
  const [form, setForm] = useState({
    recommended_action: plan.recommended_action,
    target_version: plan.target_version ?? "",
    maintenance_window: plan.maintenance_window,
    rollback_steps: plan.rollback_steps.join("\n"),
    verification_steps: plan.verification_steps.join("\n"),
    edit_reason: "",
  });
  const save = useMutation({
    mutationFn: () => api.patch<{ changed: boolean; approvals_invalidated?: number }>(`/plans/${plan.id}`, {
      recommended_action: form.recommended_action,
      target_version: form.target_version || null,
      maintenance_window: form.maintenance_window,
      rollback_steps: lines(form.rollback_steps),
      verification_steps: lines(form.verification_steps),
      edit_reason: form.edit_reason,
    }),
    onSuccess: (r) => {
      toast.success(r.changed ? "Plan updated – new revision created" : "No material change", {
        description: r.approvals_invalidated ? `${r.approvals_invalidated} approval(s) invalidated by this change` : "Validation re-run on the edited plan.",
      });
      qc.invalidateQueries();
      onOpenChange(false);
    },
    onError: (e: Error) => toast.error("Edit rejected", { description: e.message }),
  });
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setForm({ ...form, [k]: e.target.value });
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Edit draft</DialogTitle>
          <DialogDescription>Material changes create a new revision, re-run validation and invalidate any pending or unsynchronised approval.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1"><Label htmlFor="ra">Recommended action</Label><Textarea id="ra" rows={3} value={form.recommended_action} onChange={set("recommended_action")} /></div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1"><Label htmlFor="tv">Target version</Label><Input id="tv" value={form.target_version} onChange={set("target_version")} placeholder="Only versions supported by evidence" /></div>
            <div className="space-y-1"><Label htmlFor="mw">Maintenance window</Label><Input id="mw" value={form.maintenance_window} onChange={set("maintenance_window")} /></div>
          </div>
          <div className="space-y-1"><Label htmlFor="rb">Rollback steps (one per line)</Label><Textarea id="rb" rows={4} value={form.rollback_steps} onChange={set("rollback_steps")} /></div>
          <div className="space-y-1"><Label htmlFor="vs">Verification steps (one per line)</Label><Textarea id="vs" rows={3} value={form.verification_steps} onChange={set("verification_steps")} /></div>
          <div className="space-y-1"><Label htmlFor="er">Reason for change (audited)</Label><Input id="er" value={form.edit_reason} onChange={set("edit_reason")} aria-invalid={form.edit_reason.length > 0 && form.edit_reason.length < 3} /></div>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={() => save.mutate()} disabled={form.edit_reason.trim().length < 3 || save.isPending}>Save revision</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ChangeImpactView({ impact }: { impact: ChangeImpact }) {
  return (
    <div className="space-y-4 text-sm">
      <p>{impact.summary}</p>
      <KeyValue cols={3} items={[
        ["Change risk", <StatusBadge key="r" status={impact.risk_category === "high" ? "bad" : impact.risk_category === "medium" ? "warn" : "good"} label={impact.risk_category} />],
        ["Business impact", impact.business_impact],
        ["Confidence", impact.confidence],
        ["Maintenance window", impact.maintenance_window_required ? "Required" : "Not required"],
        ["Known dependents", impact.known_dependencies],
        ["Change history", impact.historical_changes.available ? `${impact.historical_changes.total} prior (${impact.historical_changes.closed} closed)` : "Unavailable"],
      ]} />
      <div>
        <div className="mb-1.5 text-xs font-medium text-muted-foreground">Affected business services</div>
        <div className="flex flex-wrap gap-1.5">
          {impact.affected_services.map((s) => <StatusBadge key={s.name} status={s.criticality === "critical" ? "bad" : s.criticality === "high" ? "warn" : "info"} label={`${s.name} · ${s.relation}`} />)}
          {impact.affected_services.length === 0 && <span className="text-xs text-muted-foreground">None mapped</span>}
        </div>
      </div>
      {impact.impacted_assets.length > 0 && (
        <div>
          <div className="mb-1.5 text-xs font-medium text-muted-foreground">Dependent systems (CMDB, up to 3 hops)</div>
          <div className="grid gap-1 sm:grid-cols-2">
            {impact.impacted_assets.map((a) => <div key={a.asset_id} className="rounded border px-2 py-1 text-xs">{a.hostname} <span className="text-muted-foreground">· depth {a.depth} · {a.service ?? "no service"}</span></div>)}
          </div>
        </div>
      )}
      {impact.unknown_dependencies.length > 0 && (
        <ul className="space-y-1 rounded-md border border-risk-medium/30 bg-risk-medium/10 p-3 text-xs">
          {impact.unknown_dependencies.map((u) => <li key={u} className="flex gap-1.5"><AlertTriangle className="size-3.5 text-risk-medium" />{u}</li>)}
        </ul>
      )}
      <div>
        <div className="mb-1.5 text-xs font-medium text-muted-foreground">Recommended review steps</div>
        <ol className="list-decimal space-y-1 pl-5 text-sm">{impact.recommended_review_steps.map((s) => <li key={s}>{s}</li>)}</ol>
      </div>
      <p className="text-xs text-muted-foreground">Downtime: {impact.downtime_estimate}</p>
    </div>
  );
}

export default function PlanPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const canEdit = useCan("plan:edit");
  const canRequest = useCan("approval:request");
  const canSync = useCan("servicenow:sync");
  const [editOpen, setEditOpen] = useState(false);
  const [requestOpen, setRequestOpen] = useState(false);
  const [comment, setComment] = useState("");
  const [tab, setTab] = useState("plan");
  const [checked, setChecked] = useState<Set<number>>(new Set());

  const { data, error, isLoading, refetch } = useQuery({ queryKey: ["plan", id], queryFn: () => api.get<PlanResponse>(`/plans/${id}`) });
  const findingId = data?.plan.finding_id;
  const finding = useQuery({ queryKey: ["finding", findingId], queryFn: () => api.get<FindingDetail>(`/findings/${findingId}`), enabled: !!findingId });

  const request = useMutation({
    mutationFn: () => api.post(`/plans/${id}/request-approval`, { comment: comment || null }),
    onSuccess: () => { toast.success("Approval requested", { description: "The plan snapshot is now immutable for this request." }); setRequestOpen(false); qc.invalidateQueries(); },
    onError: (e: Error) => toast.error("Request rejected", { description: e.message }),
  });
  const refresh = useMutation({
    mutationFn: () => api.post(`/plans/${id}/refresh-status`),
    onSuccess: () => { toast.success("ServiceNow status refreshed"); qc.invalidateQueries(); },
    onError: (e: Error) => toast.error(e.message),
  });
  const exportReport = async () => {
    try { await downloadFile(`/api/plans/${id}/export`, `remediation-plan-${id.slice(0, 8)}.md`); } catch (e) { toast.error((e as Error).message); }
  };

  if (isLoading) return <LoadingState rows={12} />;
  if (error || !data) return <ErrorState error={error} onRetry={refetch} />;
  const { plan, vulnerability, asset, risk } = data;
  const editable = !["REJECTED", "SUPERSEDED"].includes(plan.status) && !data.servicenow_records.length;
  const requestable = ["DRAFT", "ASSESSMENT_COMPLETE", "CHANGES_REQUESTED"].includes(plan.status);
  const issues = plan.validation.issues ?? [];
  const impact = plan.change_impact as ChangeImpact;

  return (
    <>
      <PageHeader
        title={plan.title}
        description={`Revision ${plan.revision} · generated by ${plan.generated_by} · updated ${fmtDate(plan.updated_at)}`}
        badge={<StatusBadge status={plan.lifecycle_stage} />}
        actions={
          <>
            <Button size="sm" disabled={!requestable || !canRequest} onClick={() => setRequestOpen(true)}><Send /> Request approval</Button>
            <Button size="sm" variant="outline" disabled={!editable || !canEdit} onClick={() => setEditOpen(true)}><Pencil /> Edit draft</Button>
            <Button size="sm" variant="outline" onClick={exportReport}><Download /> Export report</Button>
            <Button size="sm" variant="outline" onClick={() => setTab("evidence")}><FileSearch /> View evidence</Button>
            {plan.workflow_run_id && <Button size="sm" variant="ghost" asChild><Link href={`/investigations/${plan.workflow_run_id}`}><BrainCircuit /> Investigation</Link></Button>}
          </>
        }
      />
      {plan.requires_expert_validation && (
        <div className="mb-4 flex gap-2 rounded-md border border-risk-medium/40 bg-risk-medium/10 px-4 py-3 text-sm">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-risk-medium" />
          <span>Requires expert validation: the evidence does not fully establish the fix (for example, no fixed version is stated) or some claims are unverified. Confirm against the vendor advisory before approving.</span>
        </div>
      )}
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.6fr)_minmax(320px,1fr)]">
        <div className="space-y-4">
          <Card className="gap-3">
            <CardHeader><CardTitle className="text-sm">Vulnerability overview</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-sm">{vulnerability?.cve_id}</span>
                <SeverityBadge severity={vulnerability?.severity} /> <KevBadge kev={vulnerability?.kev} />
                <RiskBadge level={plan.risk_level} score={plan.risk_score} />
              </div>
              <p className="text-sm text-muted-foreground">{plan.summary}</p>
              {asset && <KeyValue cols={3} items={[["Affected asset", `${asset.hostname} (${asset.id})`], ["Environment", asset.environment], ["Business service", asset.business_service?.name], ["Criticality", asset.business_criticality], ["Owner", asset.owner ?? "Missing"], ["Installed", `${data.finding?.software} ${data.finding?.software_version}`]]} />}
            </CardContent>
          </Card>
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="flex-wrap">
              <TabsTrigger value="plan">Plan</TabsTrigger>
              <TabsTrigger value="impact">Change impact</TabsTrigger>
              <TabsTrigger value="evidence">Evidence ({plan.evidence_refs.length})</TabsTrigger>
              <TabsTrigger value="validation">Validation ({issues.length})</TabsTrigger>
            </TabsList>
            <TabsContent value="plan">
              <Card><CardContent className="space-y-5">
                <Section title="Recommended remediation">
                  <p className="text-sm">{plan.recommended_action}</p>
                  <KeyValue items={[["Target version", plan.target_version ?? <span className="text-risk-medium">Not established by evidence</span>], ["Maintenance window", plan.maintenance_window], ["Required approvers", plan.required_approvers.join(", ")], ["Expected impact", plan.expected_impact]]} />
                </Section>
                <Section title="Prerequisites"><ul className="list-disc space-y-1 pl-5 text-sm">{plan.prerequisites.map((p) => <li key={p}>{p}</li>)}</ul></Section>
                <Section title="Implementation checklist">
                  <ul className="space-y-2">
                    {plan.implementation_steps.map((s, i) => (
                      <li key={i} className="flex items-start gap-2.5 text-sm">
                        <Checkbox className="mt-0.5" checked={checked.has(i)} aria-label={`Step ${i + 1}`}
                          onCheckedChange={(v) => setChecked((c) => { const n = new Set(c); if (v) n.add(i); else n.delete(i); return n; })} />
                        <span className={checked.has(i) ? "text-muted-foreground line-through" : ""}>{i + 1}. {s.step}
                          {s.evidence_refs.map((r) => <button key={r} onClick={() => setTab("evidence")} className="ml-1 rounded bg-primary/10 px-1 font-mono text-[10px] text-primary">{r}</button>)}
                        </span>
                      </li>
                    ))}
                  </ul>
                  <p className="text-[11px] text-muted-foreground">Checklist is a local working aid; execution happens in ServiceNow by authorised implementers.</p>
                </Section>
                <Section title="Rollback plan (proposed, not tested)"><ol className="list-decimal space-y-1 pl-5 text-sm">{plan.rollback_steps.map((p) => <li key={p}>{p}</li>)}</ol></Section>
                <Section title="Verification plan"><ol className="list-decimal space-y-1 pl-5 text-sm">{plan.verification_steps.map((p) => <li key={p}>{p}</li>)}</ol></Section>
                <Section title="Testing requirements"><ul className="list-disc space-y-1 pl-5 text-sm">{plan.testing_requirements.map((p) => <li key={p}>{p}</li>)}</ul></Section>
                {plan.assumptions.length > 0 && <Section title="Assumptions & caveats"><ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">{plan.assumptions.map((p) => <li key={p}>{p}</li>)}</ul></Section>}
              </CardContent></Card>
            </TabsContent>
            <TabsContent value="impact"><Card><CardContent>{impact && "summary" in impact ? <ChangeImpactView impact={impact} /> : <p className="text-sm text-muted-foreground">Change impact not analysed.</p>}</CardContent></Card></TabsContent>
            <TabsContent value="evidence">
              <Card><CardContent className="space-y-2">
                {plan.evidence_refs.map((e) => (
                  <div key={e.id} className={`rounded-md border px-3 py-2 text-sm ${e.invalid ? "border-risk-critical/50" : ""}`}>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded bg-primary/10 px-1.5 font-mono text-xs text-primary">{e.id}</span>
                      <span className="font-medium">{e.title}</span>
                      <span className="text-xs text-muted-foreground">{e.type}</span>
                      {e.cited ? <StatusBadge status="ok" label="cited" /> : <StatusBadge status="neutral" label="not cited" />}
                      {e.invalid && <StatusBadge status="bad" label="invalid citation" />}
                    </div>
                    {e.content !== undefined && (
                      <div className="mt-1 text-xs text-muted-foreground">
                        {Array.isArray(e.content) ? (e.content as string[]).map((u) => <a key={u} href={u} target="_blank" rel="noreferrer" className="block truncate text-primary hover:underline">{u}</a>)
                          : typeof e.content === "string" ? e.content : <pre className="whitespace-pre-wrap font-mono text-[11px]">{JSON.stringify(e.content, null, 1)}</pre>}
                      </div>
                    )}
                    <div className="mt-1 text-[11px] text-muted-foreground">source: {e.source}{e.reference && <> · <a className="text-primary hover:underline" href={e.reference} target="_blank" rel="noreferrer">reference <ExternalLink className="inline size-3" /></a></>}</div>
                  </div>
                ))}
              </CardContent></Card>
            </TabsContent>
            <TabsContent value="validation">
              <Card><CardContent className="space-y-3">
                <div className="flex flex-wrap gap-2 text-xs">
                  <StatusBadge status={plan.validation.status === "passed" ? "success" : plan.validation.status === "insufficient" ? "error" : "warn"} label={`validation: ${plan.validation.status}`} />
                  {plan.validation.citation_validity !== undefined && <span className="text-muted-foreground">citation validity {Math.round((plan.validation.citation_validity ?? 0) * 100)}%</span>}
                </div>
                {Object.entries(plan.validation.checks ?? {}).map(([k, v]) => <div key={k} className="flex items-center gap-2 text-sm"><StatusBadge status={v ? "ok" : "error"} label={v ? "pass" : "fail"} />{k.replaceAll("_", " ")}</div>)}
                {issues.map((i) => (
                  <div key={i.code} className="rounded-md border px-3 py-2 text-sm">
                    <StatusBadge status={i.blocking ? "error" : i.severity === "acknowledged" ? "neutral" : "warn"} label={i.severity} /> <span className="font-mono text-xs">{i.code}</span>
                    <p className="mt-1 text-muted-foreground">{i.message}{i.acknowledged_by && ` (acknowledged by ${i.acknowledged_by})`}</p>
                  </div>
                ))}
              </CardContent></Card>
            </TabsContent>
          </Tabs>
          {finding.data && <SimulationConsole finding={finding.data} records={data.servicenow_records} targetVersion={plan.target_version} />}
        </div>
        <div className="space-y-4">
          {risk && <Card className="gap-3"><CardHeader><CardTitle className="text-sm">Business risk</CardTitle></CardHeader><CardContent><RiskBreakdown risk={risk} compact /></CardContent></Card>}
          <Card className="gap-3">
            <CardHeader><CardTitle className="text-sm">Approval history</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm">
              {data.approvals.length === 0 && <p className="text-muted-foreground">Not yet submitted for approval.</p>}
              {data.approvals.map((a) => (
                <div key={a.id} className="space-y-1 rounded-md border px-3 py-2">
                  <div className="flex items-center gap-2"><StatusBadge status={a.state} /><span className="text-xs text-muted-foreground">{fmtDate(a.created_at)}</span></div>
                  <div className="text-xs">Requested by {a.requested_by_name}{a.decided_by_name && ` · decided by ${a.decided_by_name} ${fmtDate(a.decided_at)}`}</div>
                  {a.decision_comment && <p className="text-xs text-muted-foreground">“{a.decision_comment}”</p>}
                  {a.decisions.filter((d) => d.outcome === "denied").map((d) => <p key={d.id} className="text-[11px] text-risk-critical">Denied attempt by {d.actor_name}: {d.reason}</p>)}
                  <p className="font-mono text-[10px] text-muted-foreground">payload sha256 {a.payload_hash.slice(0, 16)}…</p>
                </div>
              ))}
            </CardContent>
          </Card>
          <Card className="gap-3">
            <CardHeader className="flex flex-row items-center justify-between">
              <div><CardTitle className="text-sm">ServiceNow records</CardTitle><CardDescription className="text-xs">Created only after approval via the write gate</CardDescription></div>
              <Button size="icon-sm" variant="ghost" aria-label="Refresh status" disabled={!canSync || !data.servicenow_records.length || refresh.isPending} onClick={() => refresh.mutate()}><RefreshCw /></Button>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {data.servicenow_records.length === 0 && <p className="text-muted-foreground">No records. Rejected or unapproved plans never reach ServiceNow.</p>}
              {data.servicenow_records.map((r) => (
                <div key={r.id} className="rounded-md border px-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-medium">{r.number ?? "pending"}</span>
                    <span className="text-xs text-muted-foreground">{r.table_name}</span>
                    {r.mode === "mock" && <SimBadge />}
                    {r.record_url && <a href={r.record_url} target="_blank" rel="noreferrer" className="text-primary" aria-label="Open in ServiceNow"><ExternalLink className="size-3.5" /></a>}
                    <StatusBadge status={r.sync_state} className="ml-auto" />
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">State {r.external_state_label ?? "—"} {r.external_close_code && `(${r.external_close_code})`} · attempts {r.attempts}</div>
                  {r.last_error && <p className="mt-1 text-xs text-risk-critical">{r.last_error}</p>}
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
      <EditDialog key={plan.content_hash} plan={plan} open={editOpen} onOpenChange={setEditOpen} />
      <Dialog open={requestOpen} onOpenChange={setRequestOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Request approval</DialogTitle><DialogDescription>The approver will see an immutable, hashed snapshot of this revision. Separation of duties prevents you from approving your own high-risk request.</DialogDescription></DialogHeader>
          <Label htmlFor="cmt">Comment</Label>
          <Textarea id="cmt" rows={3} value={comment} onChange={(e) => setComment(e.target.value)} />
          <DialogFooter><Button onClick={() => request.mutate()} disabled={request.isPending}>Submit for approval</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
