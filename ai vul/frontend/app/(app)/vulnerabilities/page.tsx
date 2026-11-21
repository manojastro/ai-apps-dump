"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, Download, Search } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { toast } from "sonner";

import { KevBadge, RiskBadge, SeverityBadge, StatusBadge } from "@/components/badges";
import { EmptyState, ErrorState, LoadingState, PageHeader, Pagination } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FindingDrawer } from "@/features/finding-drawer";
import { api, downloadFile, qs } from "@/lib/api";
import { fmtDate, fmtPct } from "@/lib/format";
import type { FindingRow, Page, Vulnerability, VulnerabilityRow } from "@/lib/types";

const COLUMNS: { key: string; label: string; sortable?: boolean; className?: string }[] = [
  { key: "cve_id", label: "CVE", sortable: true },
  { key: "severity", label: "Severity", sortable: true },
  { key: "max_risk_score", label: "Risk", sortable: true },
  { key: "epss_score", label: "EPSS", sortable: true },
  { key: "kev", label: "KEV" },
  { key: "affected_assets", label: "Assets", sortable: true, className: "text-right" },
  { key: "business_impact", label: "Business impact" },
  { key: "remediation_status", label: "Status" },
  { key: "last_detected_at", label: "Last detected", sortable: true },
];

function CveDrawer({ cve, onClose, onFinding }: { cve: string | null; onClose: () => void; onFinding: (id: string) => void }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["vulnerability", cve],
    queryFn: () => api.get<{ vulnerability: Vulnerability; findings: FindingRow[] }>(`/vulnerabilities/${cve}`),
    enabled: !!cve,
  });
  return (
    <Sheet open={!!cve} onOpenChange={(o) => !o && onClose()}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-2xl">
        <SheetHeader>
          <SheetTitle className="font-mono">{cve}</SheetTitle>
          <SheetDescription>{data?.vulnerability.title ?? data?.vulnerability.affected_product ?? ""}</SheetDescription>
        </SheetHeader>
        <div className="space-y-4 px-4 pb-8">
          {isLoading && <LoadingState />}
          {error && <ErrorState error={error} />}
          {data && (
            <>
              <div className="flex flex-wrap gap-2">
                <SeverityBadge severity={data.vulnerability.severity} />
                <KevBadge kev={data.vulnerability.kev} />
                <span className="text-xs text-muted-foreground">CVSS {data.vulnerability.cvss_score ?? "—"} · EPSS {data.vulnerability.epss_score?.toFixed(4) ?? "—"}</span>
              </div>
              <p className="text-sm leading-relaxed">{data.vulnerability.description}</p>
              {data.vulnerability.kev_required_action && (
                <p className="rounded-md border border-risk-critical/30 bg-risk-critical/10 px-3 py-2 text-xs">
                  <span className="font-semibold">CISA required action:</span> {data.vulnerability.kev_required_action}
                </p>
              )}
              <div className="text-sm font-semibold">Affected findings ({data.findings.length})</div>
              <div className="divide-y rounded-md border">
                {data.findings.map((f) => (
                  <button key={f.id} onClick={() => onFinding(f.id)} className="flex w-full flex-wrap items-center gap-2 px-3 py-2 text-left text-sm hover:bg-muted/50">
                    <RiskBadge level={f.risk_level} score={f.risk_score} />
                    <span>{f.hostname}</span>
                    <span className="text-xs text-muted-foreground">{f.environment ?? "?"} · {f.business_service ?? "no service"}</span>
                    <StatusBadge status={f.status} className="ml-auto" />
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

function VulnerabilitiesContent() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  const [severity, setSeverity] = useState("all");
  const [kev, setKev] = useState("all");
  const [status, setStatus] = useState("all");
  const [sort, setSort] = useState("max_risk_score");
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const cve = params.get("cve");
  const finding = params.get("finding");

  useEffect(() => {
    const t = setTimeout(() => { setDebounced(q); setPage(1); }, 250);
    return () => clearTimeout(t);
  }, [q]);

  const setParam = (key: string, value: string | null) => {
    const next = new URLSearchParams(params.toString());
    if (value) next.set(key, value); else next.delete(key);
    router.replace(`${pathname}${next.toString() ? `?${next}` : ""}`, { scroll: false });
  };

  const query = qs({
    q: debounced, severity: severity === "all" ? undefined : severity, kev: kev === "all" ? undefined : kev,
    status: status === "all" ? undefined : status, sort, order, page, page_size: 15,
  });
  const { data, error, isLoading, refetch } = useQuery({
    queryKey: ["vulnerabilities", query],
    queryFn: () => api.get<Page<VulnerabilityRow>>(`/vulnerabilities${query}`),
    placeholderData: keepPreviousData,
  });

  const toggleSort = (key: string) => {
    if (sort === key) setOrder(order === "desc" ? "asc" : "desc");
    else { setSort(key); setOrder("desc"); }
  };
  const allOnPage = data?.items.every((r) => selected.has(r.id)) ?? false;
  const exportCsv = async () => {
    const ids = [...selected].join(",");
    try {
      await downloadFile(`/api/vulnerabilities/export.csv${ids ? `?ids=${ids}` : ""}`, "aegis-vulnerabilities.csv");
      toast.success(`Exported ${selected.size || "all"} vulnerabilities`);
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  return (
    <>
      <PageHeader
        title="Vulnerability intelligence"
        description="CVE-level view across all findings. Severity is the vendor/NVD rating; risk is the deterministic, context-aware score of the highest-risk affected asset."
        actions={<Button variant="outline" size="sm" onClick={exportCsv}><Download /> Export {selected.size ? `${selected.size} selected` : "all"} (CSV)</Button>}
      />
      <Card>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative min-w-56 flex-1">
              <Search className="absolute left-2.5 top-2 size-4 text-muted-foreground" />
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search CVE, product or business service" className="pl-8" aria-label="Search vulnerabilities" />
            </div>
            <Select value={severity} onValueChange={(v) => { setSeverity(v); setPage(1); }}>
              <SelectTrigger className="w-36" aria-label="Severity filter"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All severities</SelectItem>
                {["critical", "high", "medium", "low"].map((s) => <SelectItem key={s} value={s} className="capitalize">{s}</SelectItem>)}
              </SelectContent>
            </Select>
            <Select value={kev} onValueChange={(v) => { setKev(v); setPage(1); }}>
              <SelectTrigger className="w-32" aria-label="KEV filter"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">KEV: any</SelectItem>
                <SelectItem value="true">KEV listed</SelectItem>
                <SelectItem value="false">Not in KEV</SelectItem>
              </SelectContent>
            </Select>
            <Select value={status} onValueChange={(v) => { setStatus(v); setPage(1); }}>
              <SelectTrigger className="w-40" aria-label="Status filter"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Any status</SelectItem>
                <SelectItem value="open">Open</SelectItem>
                <SelectItem value="in_remediation">In remediation</SelectItem>
                <SelectItem value="remediated">Remediated</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {isLoading && <LoadingState rows={10} />}
          {error && <ErrorState error={error} onRetry={refetch} />}
          {data && data.items.length === 0 && <EmptyState title="No vulnerabilities match these filters" />}
          {data && data.items.length > 0 && (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-8">
                        <Checkbox aria-label="Select page" checked={allOnPage}
                          onCheckedChange={(v) => setSelected((s) => { const n = new Set(s); data.items.forEach((r) => (v ? n.add(r.id) : n.delete(r.id))); return n; })} />
                      </TableHead>
                      {COLUMNS.map((c) => (
                        <TableHead key={c.key} className={c.className}>
                          {c.sortable ? (
                            <button className="inline-flex items-center gap-1 hover:text-foreground" onClick={() => toggleSort(c.key)}>
                              {c.label}
                              {sort === c.key && (order === "desc" ? <ArrowDown className="size-3" /> : <ArrowUp className="size-3" />)}
                            </button>
                          ) : c.label}
                        </TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.items.map((r) => (
                      <TableRow key={r.id} className="cursor-pointer" onClick={() => setParam("cve", r.cve_id)}>
                        <TableCell onClick={(e) => e.stopPropagation()}>
                          <Checkbox aria-label={`Select ${r.cve_id}`} checked={selected.has(r.id)}
                            onCheckedChange={(v) => setSelected((s) => { const n = new Set(s); if (v) n.add(r.id); else n.delete(r.id); return n; })} />
                        </TableCell>
                        <TableCell>
                          <div className="font-mono text-xs font-medium">{r.cve_id}</div>
                          <div className="max-w-56 truncate text-[11px] text-muted-foreground">{r.title ?? r.affected_product}</div>
                        </TableCell>
                        <TableCell><SeverityBadge severity={r.severity} /></TableCell>
                        <TableCell><RiskBadge level={r.risk_level} score={r.max_risk_score} /></TableCell>
                        <TableCell className="tabular text-xs">{r.epss_score !== null ? `${r.epss_score.toFixed(3)}` : "—"}<div className="text-[10px] text-muted-foreground">{r.epss_percentile !== null ? `p${fmtPct(r.epss_percentile, 0)}` : ""}</div></TableCell>
                        <TableCell><KevBadge kev={r.kev} /></TableCell>
                        <TableCell className="text-right tabular">{r.affected_assets}</TableCell>
                        <TableCell className="text-xs capitalize">{r.business_impact ?? "unknown"}<div className="max-w-40 truncate text-[10px] text-muted-foreground">{r.business_services.join(", ")}</div></TableCell>
                        <TableCell><StatusBadge status={r.remediation_status} /></TableCell>
                        <TableCell className="text-xs text-muted-foreground">{fmtDate(r.last_detected_at, false)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPage={setPage} />
            </>
          )}
        </CardContent>
      </Card>
      <CveDrawer cve={cve} onClose={() => setParam("cve", null)} onFinding={(id) => { const next = new URLSearchParams(params.toString()); next.delete("cve"); next.set("finding", id); router.replace(`${pathname}?${next}`, { scroll: false }); }} />
      <FindingDrawer findingId={finding} onClose={() => setParam("finding", null)} />
    </>
  );
}

export default function VulnerabilitiesPage() {
  return (
    <Suspense fallback={<LoadingState rows={10} />}>
      <VulnerabilitiesContent />
    </Suspense>
  );
}
