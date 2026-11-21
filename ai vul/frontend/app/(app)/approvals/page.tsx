"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CircleCheck, CircleX, ExternalLink, MessageSquareWarning, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { toast } from "sonner";

import { RiskBadge, StatusBadge } from "@/components/badges";
import { EmptyState, ErrorState, KeyValue, LoadingState, PageHeader, Pagination } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { useMe } from "@/hooks/use-me";
import { api, qs } from "@/lib/api";
import { fmtDate, fmtRelative } from "@/lib/format";
import type { Approval, Page } from "@/lib/types";
import { cn } from "@/lib/utils";

type Decision = "approve" | "reject" | "request_changes";
const LABEL: Record<Decision, string> = { approve: "Approve", reject: "Reject", request_changes: "Request changes" };

function DecisionDialog({ approval, decision, onClose }: { approval: Approval; decision: Decision | null; onClose: () => void }) {
  const qc = useQueryClient();
  const [comment, setComment] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const decide = useMutation({
    mutationFn: () => api.post<Approval>(`/approvals/${approval.id}/decision`, { decision, comment: comment || null, confirm: confirmed }),
    onSuccess: (r) => {
      toast.success(`Decision recorded: ${r.state}`, {
        description: r.state === "APPROVED" ? "The deterministic write gate will now authorise the ServiceNow change." : "No external record will be created.",
      });
      qc.invalidateQueries();
      onClose();
    },
    onError: (e: Error) => toast.error("Decision refused", { description: e.message }),
  });
  const needsComment = decision !== "approve";
  return (
    <Dialog open={!!decision} onOpenChange={(o) => { if (!o) { onClose(); setComment(""); setConfirmed(false); } }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{decision && LABEL[decision]}: {String(approval.payload_snapshot.context.cve_id)}</DialogTitle>
          <DialogDescription>
            You are deciding on revision {approval.payload_snapshot.revision} (sha256 {approval.payload_hash.slice(0, 12)}…). The decision is permanent and audited.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <Label htmlFor="decision-comment">Comment {needsComment ? "(required)" : "(optional)"}</Label>
          <Textarea id="decision-comment" rows={3} value={comment} onChange={(e) => setComment(e.target.value)} aria-invalid={needsComment && !comment.trim()} />
          <label className="flex items-start gap-2 text-sm">
            <Checkbox checked={confirmed} onCheckedChange={(v) => setConfirmed(v === true)} className="mt-0.5" />
            <span>I reviewed the plan, its evidence, rollback strategy and change impact.</span>
          </label>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button variant={decision === "approve" ? "default" : "destructive"} disabled={!confirmed || (needsComment && !comment.trim()) || decide.isPending} onClick={() => decide.mutate()}>
            Confirm {decision && LABEL[decision].toLowerCase()}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ApprovalCard({ a, focused, canDecide, meId }: { a: Approval; focused: boolean; canDecide: boolean; meId?: string }) {
  const [decision, setDecision] = useState<Decision | null>(null);
  const ctx = a.payload_snapshot.context as Record<string, unknown>;
  const plan = a.payload_snapshot.plan as Record<string, unknown>;
  const impact = (ctx.change_impact ?? {}) as { affected_services?: { name: string; criticality: string }[]; risk_category?: string; summary?: string };
  const asset = (ctx.asset ?? {}) as Record<string, string>;
  const ownRequest = meId === a.requested_by;
  return (
    <Card className={cn("gap-3", focused && "ring-2 ring-ring")}>
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={a.state} />
          <RiskBadge level={String(ctx.risk_level ?? "") || null} score={ctx.risk_score as number | null} />
          <span className="text-xs text-muted-foreground">{String(ctx.priority ?? "")}</span>
          <span className="ml-auto text-xs text-muted-foreground" title={fmtDate(a.created_at)}>requested {fmtRelative(a.created_at)} by {a.requested_by_name}</span>
        </div>
        <CardTitle className="text-base">{String(plan.title)}</CardTitle>
        <CardDescription>{String(plan.recommended_action)}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <KeyValue cols={3} items={[
          ["Asset", `${asset.hostname ?? "?"} (${asset.environment ?? "?"})`],
          ["Business service", asset.business_service ?? "—"],
          ["Change risk", impact.risk_category ?? "—"],
          ["Maintenance window", String(plan.maintenance_window ?? "—")],
          ["Approver", a.assigned_approver_name ?? "Any authorised approver"],
          ["Policy", a.policy_version],
        ]} />
        {impact.affected_services && impact.affected_services.length > 0 && (
          <div className="flex flex-wrap gap-1.5">{impact.affected_services.map((s) => <StatusBadge key={s.name} status={s.criticality === "critical" ? "bad" : "info"} label={s.name} />)}</div>
        )}
        {impact.summary && <p className="text-xs text-muted-foreground">{impact.summary}</p>}
        {a.request_comment && <p className="rounded bg-muted px-3 py-2 text-xs">Requester: “{a.request_comment}”</p>}
        {a.decisions.length > 0 && (
          <ul className="space-y-1 border-t pt-2 text-xs">
            {a.decisions.map((d) => (
              <li key={d.id} className="flex flex-wrap gap-1.5">
                {d.outcome === "accepted" ? <CircleCheck className="size-3.5 text-risk-low" /> : <CircleX className="size-3.5 text-risk-critical" />}
                <span className="font-medium">{d.actor_name}</span> {d.decision.replace("_", " ")} ({d.outcome}) · {fmtDate(d.created_at)}
                {d.comment && <span className="text-muted-foreground">“{d.comment}”</span>}
                {d.reason && <span className="text-risk-critical">{d.reason}</span>}
              </li>
            ))}
          </ul>
        )}
        <div className="flex flex-wrap gap-2">
          {a.state === "PENDING" && (
            <>
              <Button size="sm" disabled={!canDecide} onClick={() => setDecision("approve")}><ShieldCheck /> Approve</Button>
              <Button size="sm" variant="destructive" disabled={!canDecide} onClick={() => setDecision("reject")}><CircleX /> Reject</Button>
              <Button size="sm" variant="outline" disabled={!canDecide} onClick={() => setDecision("request_changes")}><MessageSquareWarning /> Request changes</Button>
            </>
          )}
          <Button size="sm" variant="ghost" asChild><Link href={`/remediation/${a.plan_id}`}><ExternalLink /> View full plan</Link></Button>
        </div>
        {a.state === "PENDING" && !canDecide && <p className="text-xs text-muted-foreground">Your role cannot decide approvals.</p>}
        {a.state === "PENDING" && canDecide && ownRequest && <p className="text-xs text-risk-medium">You requested this approval; separation of duties will block your decision for high-risk plans.</p>}
      </CardContent>
      <DecisionDialog approval={a} decision={decision} onClose={() => setDecision(null)} />
    </Card>
  );
}

function ApprovalsContent() {
  const params = useSearchParams();
  const focus = params.get("focus");
  const { data: me } = useMe();
  const [tab, setTab] = useState("PENDING");
  const [page, setPage] = useState(1);
  const query = qs({ state: tab === "all" ? undefined : tab === "decided" ? "APPROVED,REJECTED,CHANGES_REQUESTED,INVALIDATED,CANCELLED" : tab, page, page_size: 10 });
  const { data, error, isLoading, refetch } = useQuery({
    queryKey: ["approvals", query],
    queryFn: () => api.get<Page<Approval>>(`/approvals${query}`),
    placeholderData: keepPreviousData,
  });
  const canDecide = !!me?.permissions.includes("approval:decide");
  return (
    <>
      <PageHeader title="Approval center" description="Human approval gate. Approved payloads are immutable; any material plan change invalidates the request. Every decision, including denied attempts, is audited." />
      <Tabs value={tab} onValueChange={(v) => { setTab(v); setPage(1); }} className="mb-3">
        <TabsList><TabsTrigger value="PENDING">Pending</TabsTrigger><TabsTrigger value="decided">Decided</TabsTrigger><TabsTrigger value="all">All</TabsTrigger></TabsList>
      </Tabs>
      {isLoading && <LoadingState />}
      {error && <ErrorState error={error} onRetry={refetch} />}
      {data && data.items.length === 0 && <EmptyState title="Nothing waiting for approval" description="Plans appear here once an analyst requests approval." />}
      <div className="space-y-4">
        {data?.items.map((a) => <ApprovalCard key={a.id} a={a} focused={focus === a.id} canDecide={canDecide} meId={me?.id} />)}
      </div>
      {data && data.total > data.page_size && <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPage={setPage} />}
    </>
  );
}

export default function ApprovalsPage() {
  return <Suspense fallback={<LoadingState />}><ApprovalsContent /></Suspense>;
}
