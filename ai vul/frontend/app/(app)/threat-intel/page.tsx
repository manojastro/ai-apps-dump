"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CloudDownload, RefreshCw, Search } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { KevBadge, SeverityBadge, StatusBadge } from "@/components/badges";
import { ErrorState, JsonView, KeyValue, LoadingState, PageHeader, StatCard } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useCan } from "@/hooks/use-me";
import { api } from "@/lib/api";
import { fmtDate, fmtPct } from "@/lib/format";
import type { IntelProvenance } from "@/lib/types";

interface IntelStatus {
  mode: string;
  kev: { mode: string; live: Record<string, unknown> | null; snapshot: Record<string, unknown> };
  snapshot: { generated_at: string | null; cves: number; notice: string; sources: Record<string, string> };
  cache_counts: Record<string, number>;
  coverage: Record<string, number>;
  vulnerabilities: { cve_id: string; severity: string; cvss_score: number | null; kev: boolean | null; kev_date_added: string | null; kev_due_date: string | null; kev_ransomware_use: string | null; epss_score: number | null; epss_percentile: number | null; epss_date: string | null; intel_sources: Record<string, IntelProvenance>; affected_product: string | null }[];
}
interface Lookup { cve_id: string; kev: Record<string, unknown>; epss: Record<string, unknown>; nvd: Record<string, unknown> }

export default function ThreatIntelPage() {
  const qc = useQueryClient();
  const canManage = useCan("integrations:manage");
  const [cve, setCve] = useState("");
  const [lookup, setLookup] = useState<Lookup | null>(null);
  const { data, error, isLoading, refetch } = useQuery({ queryKey: ["threat-intel"], queryFn: () => api.get<IntelStatus>("/threat-intel/status") });
  const refreshKev = useMutation({ mutationFn: () => api.post<Record<string, unknown>>("/threat-intel/kev/refresh"),
    onSuccess: (r) => { toast.success(`Live KEV catalog ${String(r.catalog_version)} cached`, { description: `${r.count} entries` }); qc.invalidateQueries(); },
    onError: (e: Error) => toast.error("KEV refresh failed", { description: e.message }) });
  const reEnrich = useMutation({ mutationFn: () => api.post<{ vulnerabilities: number; findings_rescored: number; mode: string }>("/threat-intel/re-enrich"),
    onSuccess: (r) => { toast.success(`Re-enriched ${r.vulnerabilities} CVEs, rescored ${r.findings_rescored} findings (${r.mode})`); qc.invalidateQueries(); },
    onError: (e: Error) => toast.error(e.message) });
  const doLookup = useMutation({ mutationFn: (id: string) => api.get<Lookup>(`/threat-intel/lookup/${encodeURIComponent(id)}`),
    onSuccess: setLookup, onError: (e: Error) => toast.error(e.message) });

  return (
    <>
      <PageHeader
        title="Threat intelligence"
        description="Severity (CVSS), exploitation probability (EPSS) and confirmed exploitation (CISA KEV) are separate signals. External feeds are treated as untrusted data and kept with provenance."
        actions={<>
          <Button size="sm" variant="outline" disabled={!canManage || refreshKev.isPending} onClick={() => refreshKev.mutate()}><CloudDownload /> Fetch live KEV catalog</Button>
          <Button size="sm" variant="outline" disabled={!canManage || reEnrich.isPending} onClick={() => reEnrich.mutate()}><RefreshCw /> Re-enrich & rescore</Button>
        </>}
      />
      {isLoading && <LoadingState />}
      {error && <ErrorState error={error} onRetry={refetch} />}
      {data && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <StatCard label="Mode" value={<span className="capitalize">{data.mode}</span>} hint={data.mode === "offline" ? "Snapshot of real public data" : "Official APIs + cache"} />
            <StatCard label="Tracked CVEs" value={data.coverage.vulnerabilities} hint={`${data.coverage.nvd_verified} NVD-verified`} />
            <StatCard label="KEV listed" value={data.coverage.kev_listed} tone="critical" hint={`${data.coverage.kev_known} with known KEV status`} />
            <StatCard label="EPSS known" value={data.coverage.epss_known} />
            <StatCard label="KEV catalog" value={String((data.kev.live?.catalog_version as string) ?? data.kev.snapshot.catalog_version ?? "—")} hint={data.kev.live ? `live · ${fmtDate(String(data.kev.live.fetched_at))}` : `snapshot · ${data.kev.snapshot.age_hours}h old`} />
          </div>
          <Card className="gap-3">
            <CardHeader><CardTitle className="text-sm">CVE lookup</CardTitle><CardDescription className="text-xs">Queries KEV, EPSS and NVD through the same adapters the agents use (live mode calls the official APIs).</CardDescription></CardHeader>
            <CardContent className="space-y-3">
              <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); if (cve.trim()) doLookup.mutate(cve.trim()); }}>
                <Input value={cve} onChange={(e) => setCve(e.target.value)} placeholder="CVE-2021-44228" className="max-w-xs" aria-label="CVE identifier" />
                <Button type="submit" size="sm" disabled={doLookup.isPending}><Search /> Look up</Button>
              </form>
              {lookup && (
                <div className="grid gap-3 md:grid-cols-3">
                  {(["kev", "epss", "nvd"] as const).map((k) => (
                    <div key={k} className="space-y-1">
                      <div className="flex items-center gap-2 text-xs font-semibold uppercase">{k} <StatusBadge status={String(lookup[k].status) === "found" ? "ok" : String(lookup[k].status) === "not_found" ? "neutral" : "warn"} label={String(lookup[k].status)} /></div>
                      <div className="text-[11px] text-muted-foreground">{String(lookup[k].reference)} · {String(lookup[k].origin)}</div>
                      <JsonView data={lookup[k].data ?? lookup[k].notes} maxHeight={220} />
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle className="text-sm">Enriched vulnerabilities</CardTitle><CardDescription className="text-xs">{data.snapshot.notice}</CardDescription></CardHeader>
            <CardContent className="overflow-x-auto">
              <Table>
                <TableHeader><TableRow><TableHead>CVE</TableHead><TableHead>Severity</TableHead><TableHead>EPSS</TableHead><TableHead>KEV</TableHead><TableHead>KEV due</TableHead><TableHead>Ransomware</TableHead><TableHead>Provenance</TableHead></TableRow></TableHeader>
                <TableBody>
                  {data.vulnerabilities.map((v) => (
                    <TableRow key={v.cve_id}>
                      <TableCell><div className="font-mono text-xs">{v.cve_id}</div><div className="text-[11px] text-muted-foreground">{v.affected_product}</div></TableCell>
                      <TableCell><SeverityBadge severity={v.severity} /> <span className="text-xs tabular">{v.cvss_score}</span></TableCell>
                      <TableCell className="text-xs tabular">{v.epss_score?.toFixed(4) ?? "—"}<div className="text-[10px] text-muted-foreground">{v.epss_percentile !== null && `p${fmtPct(v.epss_percentile, 0)} · ${v.epss_date}`}</div></TableCell>
                      <TableCell><KevBadge kev={v.kev} /></TableCell>
                      <TableCell className="text-xs">{v.kev_due_date ?? "—"}</TableCell>
                      <TableCell className="text-xs">{v.kev_ransomware_use ?? "—"}</TableCell>
                      <TableCell className="text-[10px] text-muted-foreground">{Object.entries(v.intel_sources ?? {}).map(([k, p]) => <div key={k}>{k}: {p.origin}</div>)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
          <Card><CardContent><KeyValue cols={3} items={[["Snapshot generated", fmtDate(data.snapshot.generated_at)], ["Snapshot CVEs", data.snapshot.cves], ["Cache rows", Object.entries(data.cache_counts).map(([k, v]) => `${k}: ${v}`).join(" · ") || "none"]]} /></CardContent></Card>
        </div>
      )}
    </>
  );
}
