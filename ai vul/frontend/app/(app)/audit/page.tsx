"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useEffect, useState } from "react";

import { StatusBadge } from "@/components/badges";
import { EmptyState, ErrorState, JsonView, LoadingState, PageHeader, Pagination } from "@/components/common";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api, qs } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import type { Page } from "@/lib/types";

interface AuditEvent {
  id: string; actor: string; action: string; target_type: string; target_id: string | null; previous_state: unknown; new_state: unknown;
  details: Record<string, unknown>; outcome: string; correlation_id: string | null; ip_address: string | null; created_at: string;
}

const GROUPS: Record<string, string | undefined> = {
  all: undefined,
  approvals: "approval_requested,approval_approve,approval_reject,approval_request_changes,approval_invalidated,approval_cancelled,approval_approve_denied,approval_reject_denied,approval_request_changes_denied",
  servicenow: "servicenow_write_gate,servicenow_record_created,servicenow_record_adopted,servicenow_sync_failed,servicenow_sync_retry_requested,servicenow_test_connection,remediation_state_synced",
  auth: "login,login_failed,logout,permission_denied",
  workflow: "investigation_started,workflow_rejected,asset_match_confirmed,manual_review_override,investigation_dismissed,finding_closed_with_evidence,verification_evaluated",
  changes: "plan_edited,risk_policy_updated,cmdb_sync,findings_imported,kev_refreshed,threat_intel_reenriched",
  simulation: "simulation_failure_mode,simulation_change_advanced,simulation_patch_applied,scan_evidence_collected,scan_evidence_uploaded",
};

export default function AuditPage() {
  const [group, setGroup] = useState("all");
  const [outcome, setOutcome] = useState("all");
  const [actor, setActor] = useState("");
  const [debounced, setDebounced] = useState("");
  const [page, setPage] = useState(1);
  useEffect(() => { const t = setTimeout(() => { setDebounced(actor); setPage(1); }, 300); return () => clearTimeout(t); }, [actor]);
  const query = qs({ action: GROUPS[group], outcome: outcome === "all" ? undefined : outcome, actor: debounced, page, page_size: 25 });
  const { data, error, isLoading, refetch } = useQuery({ queryKey: ["audit", query], queryFn: () => api.get<Page<AuditEvent>>(`/audit${query}`), placeholderData: keepPreviousData });
  return (
    <>
      <PageHeader title="Audit logs" description="Append-only trail of every externally meaningful action: approvals and denied attempts, write-gate decisions, ServiceNow writes, logins, policy changes and simulation controls. Secrets are redacted." />
      <Card><CardContent className="space-y-3">
        <div className="flex flex-wrap gap-2">
          <Select value={group} onValueChange={(v) => { setGroup(v); setPage(1); }}>
            <SelectTrigger className="w-48" aria-label="Event type"><SelectValue /></SelectTrigger>
            <SelectContent>{Object.keys(GROUPS).map((g) => <SelectItem key={g} value={g} className="capitalize">{g === "all" ? "All events" : g}</SelectItem>)}</SelectContent>
          </Select>
          <Select value={outcome} onValueChange={(v) => { setOutcome(v); setPage(1); }}>
            <SelectTrigger className="w-36" aria-label="Outcome"><SelectValue /></SelectTrigger>
            <SelectContent><SelectItem value="all">Any outcome</SelectItem><SelectItem value="success">Success</SelectItem><SelectItem value="denied">Denied</SelectItem><SelectItem value="error">Error</SelectItem></SelectContent>
          </Select>
          <div className="relative min-w-56 flex-1"><Search className="absolute left-2.5 top-2 size-4 text-muted-foreground" /><Input className="pl-8" placeholder="Filter by actor" value={actor} onChange={(e) => setActor(e.target.value)} aria-label="Actor filter" /></div>
        </div>
        {isLoading && <LoadingState rows={10} />}
        {error && <ErrorState error={error} onRetry={refetch} />}
        {data && data.items.length === 0 && <EmptyState title="No audit events match" />}
        {data && data.items.length > 0 && (
          <>
            <div className="overflow-x-auto"><Table>
              <TableHeader><TableRow><TableHead>Time</TableHead><TableHead>Actor</TableHead><TableHead>Action</TableHead><TableHead>Target</TableHead><TableHead>Outcome</TableHead><TableHead>Details</TableHead></TableRow></TableHeader>
              <TableBody>
                {data.items.map((e) => (
                  <TableRow key={e.id}>
                    <TableCell className="whitespace-nowrap text-xs text-muted-foreground">{fmtDate(e.created_at)}</TableCell>
                    <TableCell className="max-w-48 truncate text-xs" title={e.actor}>{e.actor}</TableCell>
                    <TableCell className="font-mono text-xs">{e.action}</TableCell>
                    <TableCell className="text-xs">{e.target_type}<div className="font-mono text-[10px] text-muted-foreground">{e.target_id?.slice(0, 13)}</div></TableCell>
                    <TableCell><StatusBadge status={e.outcome} /></TableCell>
                    <TableCell>
                      <details><summary className="cursor-pointer text-xs text-primary">view</summary>
                        <div className="mt-2 w-[min(560px,70vw)]"><JsonView data={{ previous: e.previous_state, new: e.new_state, details: e.details, correlation_id: e.correlation_id, ip: e.ip_address }} maxHeight={240} /></div>
                      </details>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table></div>
            <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPage={setPage} />
          </>
        )}
      </CardContent></Card>
    </>
  );
}
