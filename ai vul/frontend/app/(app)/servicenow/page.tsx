"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, PlugZap, RefreshCw, Zap } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

import { SimBadge, StatusBadge } from "@/components/badges";
import { ErrorState, JsonView, KeyValue, LoadingState, PageHeader, Pagination } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useCan } from "@/hooks/use-me";
import { api, qs } from "@/lib/api";
import { fmtDate, fmtRelative } from "@/lib/format";
import type { Page, ServiceNowRecord } from "@/lib/types";

interface Status {
  mode: string;
  configured: boolean;
  instance: string | null;
  writes_enabled: boolean;
  tables: Record<string, string | null>;
  write_allowlist: string[];
  cmdb_field_map: Record<string, string>;
  auth_method: string;
  record_counts: Record<string, number>;
  last_successful_sync: string | null;
  last_error: { error: string; at: string; operation: string } | null;
  simulator_failure_mode: { mode: string; remaining: number } | null;
}
interface Attempt { id: string; record_number: string | null; operation: string; table: string | null; outcome: string; error: string | null; http_status: number | null; latency_ms: number | null; actor: string | null; at: string }
interface Activity { record: ServiceNowRecord; remote_activity: { action: string; changes: Record<string, unknown>; actor: string; at: string }[]; attempts: Omit<Attempt, "id" | "record_number" | "table">[] }

function RecordDrawer({ id, onClose }: { id: string | null; onClose: () => void }) {
  const { data, isLoading } = useQuery({ queryKey: ["sn-activity", id], queryFn: () => api.get<Activity>(`/servicenow/records/${id}/activity`), enabled: !!id });
  return (
    <Sheet open={!!id} onOpenChange={(o) => !o && onClose()}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-xl">
        <SheetHeader><SheetTitle>{data?.record.number ?? "Record"}</SheetTitle><SheetDescription>{data?.record.table_name} · {data?.record.instance}</SheetDescription></SheetHeader>
        <div className="space-y-4 px-4 pb-6">
          {isLoading && <LoadingState />}
          {data && (
            <>
              <KeyValue items={[["sys_id", <span key="s" className="font-mono text-xs">{data.record.sys_id}</span>], ["Sync", <StatusBadge key="y" status={data.record.sync_state} />], ["Remote state", data.record.external_state_label], ["Attempts", data.record.attempts]]} />
              <div className="text-sm font-semibold">Payload sent (from approved snapshot)</div>
              <JsonView data={data.record.payload} />
              <div className="text-sm font-semibold">Integration attempts</div>
              <ul className="space-y-1 text-xs">{data.attempts.map((a, i) => <li key={i} className="flex gap-2"><StatusBadge status={a.outcome} /> {a.operation} · {a.latency_ms}ms · {fmtDate(a.at)} {a.error && <span className="text-risk-critical">{a.error}</span>}</li>)}</ul>
              {data.remote_activity.length > 0 && (
                <>
                  <div className="text-sm font-semibold">Remote activity stream <SimBadge /></div>
                  <ul className="space-y-1 text-xs">{data.remote_activity.map((a, i) => <li key={i}><span className="font-medium">{a.action}</span> by {a.actor} · {fmtDate(a.at)}<div className="font-mono text-[10px] text-muted-foreground">{JSON.stringify(a.changes).slice(0, 200)}</div></li>)}</ul>
                </>
              )}
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

export default function ServiceNowPage() {
  const qc = useQueryClient();
  const canSync = useCan("servicenow:sync");
  const canSim = useCan("simulation:control");
  const [page, setPage] = useState(1);
  const [logPage, setLogPage] = useState(1);
  const [drawer, setDrawer] = useState<string | null>(null);
  const [failMode, setFailMode] = useState("timeout");
  const status = useQuery({ queryKey: ["sn-status"], queryFn: () => api.get<Status>("/servicenow/status"), refetchInterval: 15_000 });
  const records = useQuery({ queryKey: ["sn-records", page], queryFn: () => api.get<Page<ServiceNowRecord>>(`/servicenow/records${qs({ page, page_size: 15 })}`) });
  const attempts = useQuery({ queryKey: ["sn-attempts", logPage], queryFn: () => api.get<Page<Attempt>>(`/servicenow/attempts${qs({ page: logPage, page_size: 15 })}`) });

  const refreshAll = () => qc.invalidateQueries();
  const test = useMutation({ mutationFn: () => api.post<{ ok: boolean; detail: string }>("/servicenow/test-connection"),
    onSuccess: (r) => { (r.ok ? toast.success : toast.error)(r.ok ? "Connection OK" : "Connection failed", { description: r.detail }); refreshAll(); }, onError: (e: Error) => toast.error(e.message) });
  const refresh = useMutation({ mutationFn: () => api.post<{ refreshed: number }>("/servicenow/refresh"),
    onSuccess: (r) => { toast.success(`Refreshed ${r.refreshed} record(s) from ServiceNow`); refreshAll(); }, onError: (e: Error) => toast.error(e.message) });
  const inject = useMutation({ mutationFn: (mode: string) => api.post("/simulation/servicenow/failure", { mode, remaining: mode === "none" ? 0 : 1 }),
    onSuccess: (_, mode) => { toast.success(mode === "none" ? "Failure injection cleared" : `Next ServiceNow call will fail: ${mode}`); refreshAll(); }, onError: (e: Error) => toast.error(e.message) });

  const s = status.data;
  return (
    <>
      <PageHeader
        title="ServiceNow integration"
        description="All writes pass through structured validation, permission checks, the deterministic approval gate and an idempotent sync service. Reads and connection tests never write."
        badge={s?.mode === "mock" ? <SimBadge label="Simulation mode" /> : undefined}
        actions={<>
          <Button size="sm" variant="outline" disabled={!canSync || test.isPending} onClick={() => test.mutate()}><PlugZap /> Test connection</Button>
          <Button size="sm" variant="outline" disabled={!canSync || refresh.isPending} onClick={() => refresh.mutate()}><RefreshCw /> Sync record status</Button>
        </>}
      />
      {status.error && <ErrorState error={status.error} onRetry={status.refetch} />}
      {s && (
        <div className="mb-4 grid gap-4 lg:grid-cols-3">
          <Card className="gap-3 lg:col-span-2">
            <CardHeader><CardTitle className="text-sm">Integration health</CardTitle></CardHeader>
            <CardContent>
              <KeyValue cols={3} items={[
                ["Mode", <StatusBadge key="m" status={s.mode === "mock" ? "Mock" : s.configured ? "Configured" : "Not Configured"} label={s.mode} />],
                ["Instance", s.instance ?? "Not configured"],
                ["Authentication", s.auth_method],
                ["Writes", s.writes_enabled ? "Enabled (approval-gated)" : "Disabled"],
                ["Last successful sync", s.last_successful_sync ? fmtRelative(s.last_successful_sync) : "Never"],
                ["Records", Object.entries(s.record_counts).map(([k, v]) => `${k}: ${v}`).join(" · ") || "0"],
                ["Change table", s.tables.change], ["Remediation table", s.tables.remediation ?? "not configured"], ["CMDB table", s.tables.cmdb],
              ]} />
              {s.last_error && <p className="mt-3 rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">Last error ({s.last_error.operation}, {fmtRelative(s.last_error.at)}): {s.last_error.error}</p>}
            </CardContent>
          </Card>
          {s.simulator_failure_mode && (
            <Card className="gap-3 border-dashed">
              <CardHeader><CardTitle className="flex items-center gap-2 text-sm">Failure injection <SimBadge /></CardTitle><CardDescription className="text-xs">Demonstrate recovery: auth failure, timeout, HTTP 500, or a lost response after the record was created.</CardDescription></CardHeader>
              <CardContent className="space-y-3">
                <div className="text-xs">Current: <StatusBadge status={s.simulator_failure_mode.mode === "none" ? "ok" : "error"} label={`${s.simulator_failure_mode.mode}${s.simulator_failure_mode.remaining ? ` (${s.simulator_failure_mode.remaining} left)` : ""}`} /></div>
                <div className="flex gap-2">
                  <Select value={failMode} onValueChange={setFailMode}>
                    <SelectTrigger className="flex-1" aria-label="Failure mode"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="auth_failure">Auth failure (401)</SelectItem>
                      <SelectItem value="timeout">Timeout</SelectItem>
                      <SelectItem value="server_error">Server error (500)</SelectItem>
                      <SelectItem value="lost_response">Lost response (partial success)</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button size="sm" disabled={!canSim || inject.isPending} onClick={() => inject.mutate(failMode)}><Zap /> Arm</Button>
                </div>
                <Button size="sm" variant="ghost" disabled={!canSim} onClick={() => inject.mutate("none")}>Clear</Button>
              </CardContent>
            </Card>
          )}
        </div>
      )}
      <Tabs defaultValue="records">
        <TabsList><TabsTrigger value="records">Linked records</TabsTrigger><TabsTrigger value="logs">Integration logs</TabsTrigger><TabsTrigger value="mapping">Table & field mapping</TabsTrigger></TabsList>
        <TabsContent value="records">
          <Card><CardContent>
            {records.isLoading && <LoadingState />}
            {records.data && (
              <>
                <div className="overflow-x-auto"><Table>
                  <TableHeader><TableRow><TableHead>Number</TableHead><TableHead>Table</TableHead><TableHead>Sync</TableHead><TableHead>Remote state</TableHead><TableHead>Attempts</TableHead><TableHead>Plan</TableHead><TableHead>Last sync</TableHead></TableRow></TableHeader>
                  <TableBody>
                    {records.data.items.map((r) => (
                      <TableRow key={r.id} className="cursor-pointer" onClick={() => setDrawer(r.id)}>
                        <TableCell className="font-mono text-xs">{r.number ?? "—"} {r.record_url && <a href={r.record_url} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()} className="text-primary"><ExternalLink className="inline size-3" /></a>}</TableCell>
                        <TableCell className="text-xs">{r.table_name}</TableCell>
                        <TableCell><StatusBadge status={r.sync_state} /></TableCell>
                        <TableCell className="text-xs">{r.external_state_label ?? "—"}{r.external_close_code && ` (${r.external_close_code})`}</TableCell>
                        <TableCell className="tabular text-xs">{r.attempts}</TableCell>
                        <TableCell><Link href={`/remediation/${r.plan_id}`} onClick={(e) => e.stopPropagation()} className="text-xs text-primary hover:underline">open</Link></TableCell>
                        <TableCell className="text-xs text-muted-foreground">{fmtRelative(r.last_sync_at)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table></div>
                <Pagination page={records.data.page} pageSize={records.data.page_size} total={records.data.total} onPage={setPage} />
              </>
            )}
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="logs">
          <Card><CardContent>
            {attempts.data && (
              <>
                <div className="overflow-x-auto"><Table>
                  <TableHeader><TableRow><TableHead>When</TableHead><TableHead>Operation</TableHead><TableHead>Record</TableHead><TableHead>Outcome</TableHead><TableHead>Latency</TableHead><TableHead>Actor</TableHead><TableHead>Error</TableHead></TableRow></TableHeader>
                  <TableBody>
                    {attempts.data.items.map((a) => (
                      <TableRow key={a.id}>
                        <TableCell className="text-xs text-muted-foreground">{fmtDate(a.at)}</TableCell>
                        <TableCell className="text-xs">{a.operation} <span className="text-muted-foreground">{a.table}</span></TableCell>
                        <TableCell className="font-mono text-xs">{a.record_number ?? "—"}</TableCell>
                        <TableCell><StatusBadge status={a.outcome} /></TableCell>
                        <TableCell className="tabular text-xs">{a.latency_ms ?? "—"} ms</TableCell>
                        <TableCell className="text-xs">{a.actor}</TableCell>
                        <TableCell className="max-w-xs truncate text-xs text-risk-critical" title={a.error ?? ""}>{a.error}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table></div>
                <Pagination page={attempts.data.page} pageSize={attempts.data.page_size} total={attempts.data.total} onPage={setLogPage} />
              </>
            )}
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="mapping">
          {s && <Card><CardContent className="space-y-4">
            <KeyValue items={[["Write allowlist", s.write_allowlist.join(", ")], ["Change table", s.tables.change], ["Remediation table", s.tables.remediation ?? "—"], ["Business service table", s.tables.service]]} />
            <div className="text-sm font-semibold">CMDB → asset field mapping</div>
            <div className="grid gap-1 text-xs sm:grid-cols-2">{Object.entries(s.cmdb_field_map).map(([k, v]) => <div key={k} className="flex justify-between rounded border px-2 py-1"><span>{k}</span><span className="font-mono text-muted-foreground">{v}</span></div>)}</div>
          </CardContent></Card>}
        </TabsContent>
      </Tabs>
      <RecordDrawer id={drawer} onClose={() => setDrawer(null)} />
    </>
  );
}
