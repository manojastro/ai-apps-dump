"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileUp, PlugZap, RefreshCw } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";

import { StatusBadge } from "@/components/badges";
import { ErrorState, LoadingState, PageHeader } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useCan } from "@/hooks/use-me";
import { api } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import type { Integration } from "@/lib/types";

interface ImportResult { import_id: string; total: number; created: number; duplicates: number; invalid: number; new_vulnerabilities: number; ambiguous_assets: number; unmatched_assets: number; errors: { row: number; reasons: string[] }[] }
interface ImportRow { id: string; filename: string; format: string; scanner: string; uploaded_by: string; total_rows: number; created: number; duplicates: number; invalid: number; created_at: string }

export default function IntegrationsPage() {
  const qc = useQueryClient();
  const canImport = useCan("findings:import");
  const canManage = useCan("integrations:manage");
  const fileRef = useRef<HTMLInputElement>(null);
  const [scanner, setScanner] = useState("csv_import");
  const [result, setResult] = useState<ImportResult | null>(null);
  const { data, error, isLoading, refetch } = useQuery({ queryKey: ["integrations"], queryFn: () => api.get<{ integrations: Integration[] }>("/integrations") });
  const imports = useQuery({ queryKey: ["imports"], queryFn: () => api.get<ImportRow[]>("/findings-imports") });
  const upload = useMutation({
    mutationFn: (file: File) => { const form = new FormData(); form.append("file", file); form.append("scanner", scanner); return api.upload<ImportResult>("/findings/import", form); },
    onSuccess: (r) => { setResult(r); toast.success(`Imported ${r.created} new finding(s)`, { description: `${r.duplicates} duplicate(s), ${r.invalid} invalid row(s)` }); qc.invalidateQueries(); },
    onError: (e: Error) => toast.error("Import failed", { description: e.message }),
  });
  const defender = useMutation({ mutationFn: () => api.post<{ created: number; duplicates: number }>("/scanners/defender/refresh"),
    onSuccess: (r) => { toast.success(`Defender refresh: ${r.created} new, ${r.duplicates} already known`); qc.invalidateQueries(); }, onError: (e: Error) => toast.error(e.message) });
  const testDefender = useMutation({ mutationFn: () => api.post<{ ok: boolean; detail: string }>("/integrations/defender/test"),
    onSuccess: (r) => (r.ok ? toast.success : toast.error)(r.detail), onError: (e: Error) => toast.error(e.message) });

  return (
    <>
      <PageHeader title="Integrations" description="Every connector reports its real status. Mock = simulated adapter; Unverified = configured but not yet proven against a live tenant; Unsupported = documented extension point only." />
      {isLoading && <LoadingState />}
      {error && <ErrorState error={error} onRetry={refetch} />}
      {data && (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {data.integrations.map((i) => (
            <Card key={i.key} className="gap-2">
              <CardHeader className="flex flex-row items-start justify-between gap-2">
                <div><CardTitle className="text-sm">{i.name}</CardTitle><CardDescription className="text-xs">mode: {i.mode}</CardDescription></div>
                <StatusBadge status={i.status} />
              </CardHeader>
              <CardContent className="space-y-3 text-xs text-muted-foreground">
                <p>{i.detail}</p>
                {i.key === "defender_mock" && <Button size="sm" variant="outline" disabled={!canImport || defender.isPending} onClick={() => defender.mutate()}><RefreshCw /> Refresh findings</Button>}
                {i.key === "defender" && i.status !== "Not Configured" && <Button size="sm" variant="outline" disabled={!canManage || testDefender.isPending} onClick={() => testDefender.mutate()}><PlugZap /> Test connection</Button>}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      <Card className="mt-6 gap-3">
        <CardHeader><CardTitle className="text-sm">CSV / JSON vulnerability import</CardTitle><CardDescription className="text-xs">Columns are matched to common aliases (hostname, cve, severity, cvss, software, version, ip, first_seen…). Rows are normalised, de-duplicated, enriched and correlated to the CMDB. Sample: data/synthetic/sample_scanner_export.csv</CardDescription></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap items-end gap-2">
            <div className="space-y-1"><Label htmlFor="scanner">Scanner label</Label><Input id="scanner" value={scanner} onChange={(e) => setScanner(e.target.value)} className="w-48" /></div>
            <input ref={fileRef} type="file" accept=".csv,.json,text/csv,application/json" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) upload.mutate(f); e.target.value = ""; }} />
            <Button disabled={!canImport || upload.isPending} onClick={() => fileRef.current?.click()}><FileUp /> {upload.isPending ? "Importing…" : "Choose file"}</Button>
          </div>
          {result && (
            <div className="rounded-md border p-3 text-sm">
              <div className="flex flex-wrap gap-4 tabular">
                <span>Rows {result.total}</span><span className="text-risk-low">Created {result.created}</span><span>Duplicates {result.duplicates}</span>
                <span className="text-risk-critical">Invalid {result.invalid}</span><span>New CVEs {result.new_vulnerabilities}</span>
                <span className="text-risk-medium">Ambiguous assets {result.ambiguous_assets}</span><span>Unmatched {result.unmatched_assets}</span>
              </div>
              {result.errors.length > 0 && <ul className="mt-2 space-y-0.5 text-xs text-risk-critical">{result.errors.slice(0, 10).map((e) => <li key={e.row}>Row {e.row}: {e.reasons.join("; ")}</li>)}</ul>}
            </div>
          )}
          {imports.data && imports.data.length > 0 && (
            <Table>
              <TableHeader><TableRow><TableHead>File</TableHead><TableHead>Scanner</TableHead><TableHead>By</TableHead><TableHead className="text-right">Rows</TableHead><TableHead className="text-right">Created</TableHead><TableHead className="text-right">Duplicates</TableHead><TableHead className="text-right">Invalid</TableHead><TableHead>When</TableHead></TableRow></TableHeader>
              <TableBody>{imports.data.map((r) => (
                <TableRow key={r.id}><TableCell className="text-xs">{r.filename}</TableCell><TableCell className="text-xs">{r.scanner}</TableCell><TableCell className="text-xs">{r.uploaded_by}</TableCell>
                  <TableCell className="text-right tabular">{r.total_rows}</TableCell><TableCell className="text-right tabular">{r.created}</TableCell><TableCell className="text-right tabular">{r.duplicates}</TableCell><TableCell className="text-right tabular">{r.invalid}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{fmtDate(r.created_at)}</TableCell></TableRow>
              ))}</TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </>
  );
}
