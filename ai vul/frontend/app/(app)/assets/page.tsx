"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw, Search } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { toast } from "sonner";

import { RiskBadge, StatusBadge } from "@/components/badges";
import { EmptyState, ErrorState, KeyValue, LoadingState, PageHeader, Pagination } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useCan } from "@/hooks/use-me";
import { api, qs } from "@/lib/api";
import { fmtRelative } from "@/lib/format";
import type { Asset, BusinessService, FindingRow, Page } from "@/lib/types";

function AssetDrawer({ id, onClose }: { id: string | null; onClose: () => void }) {
  const { data, isLoading } = useQuery({
    queryKey: ["asset", id],
    queryFn: () => api.get<{ asset: Asset; findings: FindingRow[]; depends_on: Asset[]; used_by: Asset[] }>(`/assets/${id}`),
    enabled: !!id,
  });
  return (
    <Sheet open={!!id} onOpenChange={(o) => !o && onClose()}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-xl">
        <SheetHeader><SheetTitle>{data?.asset.hostname ?? "Asset"}</SheetTitle><SheetDescription>{data?.asset.id} · CMDB {data?.asset.cmdb_sys_id?.slice(0, 12)}</SheetDescription></SheetHeader>
        <div className="space-y-5 px-4 pb-6">
          {isLoading && <LoadingState />}
          {data && (
            <>
              <KeyValue items={[["FQDN", data.asset.fqdn], ["IP", data.asset.ip_address], ["OS", `${data.asset.operating_system ?? "?"} ${data.asset.os_version ?? ""}`], ["Type", data.asset.asset_type],
                ["Environment", data.asset.environment], ["Criticality", data.asset.business_criticality], ["Internet exposed", data.asset.internet_exposed === null ? "Unknown" : data.asset.internet_exposed ? "Yes" : "No"],
                ["Business service", data.asset.business_service?.name], ["Owner", data.asset.owner ?? "Missing"], ["Support group", data.asset.support_group], ["Location", data.asset.location], ["Operational", data.asset.operational_status],
                ["Defender device", data.asset.defender_device_id ? data.asset.defender_device_id.slice(0, 12) : "not linked"], ["Last CMDB sync", fmtRelative(data.asset.last_sync_at)]]} />
              <div>
                <div className="mb-1.5 text-sm font-semibold">Dependencies</div>
                <div className="grid gap-3 text-xs sm:grid-cols-2">
                  <div><div className="mb-1 text-muted-foreground">Depends on</div>{data.depends_on.map((a) => <div key={a.id}>{a.hostname}</div>)}{data.depends_on.length === 0 && "—"}</div>
                  <div><div className="mb-1 text-muted-foreground">Used by</div>{data.used_by.map((a) => <div key={a.id}>{a.hostname} <span className="text-muted-foreground">({a.business_service?.name ?? "no service"})</span></div>)}{data.used_by.length === 0 && "—"}</div>
                </div>
              </div>
              <div>
                <div className="mb-1.5 text-sm font-semibold">Findings ({data.findings.length})</div>
                <div className="space-y-1">{data.findings.map((f) => (
                  <a key={f.id} href={`/vulnerabilities?finding=${f.id}`} className="flex items-center gap-2 rounded border px-2 py-1.5 text-xs hover:bg-muted/50">
                    <RiskBadge level={f.risk_level} score={f.risk_score} /> <span className="font-mono">{f.cve_id}</span> {f.software} {f.software_version}
                    <StatusBadge status={f.status} className="ml-auto" />
                  </a>
                ))}</div>
              </div>
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

function AssetsContent() {
  const qc = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const canSync = useCan("integrations:manage");
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  const [env, setEnv] = useState("all");
  const [crit, setCrit] = useState("all");
  const [service, setService] = useState("all");
  const [page, setPage] = useState(1);
  useEffect(() => { const t = setTimeout(() => { setDebounced(q); setPage(1); }, 250); return () => clearTimeout(t); }, [q]);
  const query = qs({ q: debounced, environment: env === "all" ? undefined : env, criticality: crit === "all" ? undefined : crit, service: service === "all" ? undefined : service, page, page_size: 20 });
  const { data, error, isLoading, refetch } = useQuery({ queryKey: ["assets", query], queryFn: () => api.get<Page<Asset>>(`/assets${query}`), placeholderData: keepPreviousData });
  const services = useQuery({ queryKey: ["services"], queryFn: () => api.get<BusinessService[]>("/business-services") });
  const sync = useMutation({ mutationFn: () => api.post<Record<string, number>>("/assets/sync"),
    onSuccess: (r) => { toast.success("CMDB synchronised", { description: `${r.assets} CIs, ${r.services} services, ${r.dependencies} relationships` }); qc.invalidateQueries(); },
    onError: (e: Error) => toast.error("CMDB sync failed", { description: e.message }) });
  const assetId = params.get("asset");
  const setAsset = (id: string | null) => { const n = new URLSearchParams(params.toString()); if (id) n.set("asset", id); else n.delete("asset"); router.replace(`${pathname}?${n}`, { scroll: false }); };

  return (
    <>
      <PageHeader title="Assets & CMDB" description="Inventory synchronised from the ServiceNow CMDB through the integration adapter (simulated instance by default)."
        actions={<Button size="sm" variant="outline" disabled={!canSync || sync.isPending} onClick={() => sync.mutate()}><RefreshCw className={sync.isPending ? "animate-spin" : ""} /> Sync from CMDB</Button>} />
      {services.data && (
        <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {services.data.map((s) => (
            <Card key={s.id} className="cursor-pointer gap-1 py-3 hover:bg-muted/30" onClick={() => { setService(s.name); setPage(1); }}>
              <CardHeader className="px-4"><CardTitle className="truncate text-xs">{s.name}</CardTitle></CardHeader>
              <CardContent className="flex items-center justify-between px-4 text-xs text-muted-foreground">
                <span>{s.assets} assets · {s.open_findings} open</span>
                <StatusBadge status={s.criticality === "critical" ? "bad" : s.criticality === "high" ? "warn" : "info"} label={s.criticality} />
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      <Card><CardContent className="space-y-3">
        <div className="flex flex-wrap gap-2">
          <div className="relative min-w-56 flex-1"><Search className="absolute left-2.5 top-2 size-4 text-muted-foreground" /><Input className="pl-8" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search hostname, FQDN or asset ID" aria-label="Search assets" /></div>
          <Select value={env} onValueChange={(v) => { setEnv(v); setPage(1); }}><SelectTrigger className="w-40" aria-label="Environment"><SelectValue /></SelectTrigger>
            <SelectContent><SelectItem value="all">All environments</SelectItem>{["production", "staging", "development", "test"].map((e) => <SelectItem key={e} value={e} className="capitalize">{e}</SelectItem>)}</SelectContent></Select>
          <Select value={crit} onValueChange={(v) => { setCrit(v); setPage(1); }}><SelectTrigger className="w-36" aria-label="Criticality"><SelectValue /></SelectTrigger>
            <SelectContent><SelectItem value="all">Any criticality</SelectItem>{["critical", "high", "medium", "low"].map((e) => <SelectItem key={e} value={e} className="capitalize">{e}</SelectItem>)}</SelectContent></Select>
          <Select value={service} onValueChange={(v) => { setService(v); setPage(1); }}><SelectTrigger className="w-52" aria-label="Business service"><SelectValue /></SelectTrigger>
            <SelectContent><SelectItem value="all">All services</SelectItem>{services.data?.map((s) => <SelectItem key={s.id} value={s.name}>{s.name}</SelectItem>)}</SelectContent></Select>
        </div>
        {isLoading && <LoadingState rows={10} />}
        {error && <ErrorState error={error} onRetry={refetch} />}
        {data && data.items.length === 0 && <EmptyState title="No assets match" />}
        {data && data.items.length > 0 && (
          <>
            <div className="overflow-x-auto"><Table>
              <TableHeader><TableRow><TableHead>Asset</TableHead><TableHead>Environment</TableHead><TableHead>Criticality</TableHead><TableHead>Exposed</TableHead><TableHead>Business service</TableHead><TableHead>Owner</TableHead><TableHead className="text-right">Open findings</TableHead><TableHead>Max risk</TableHead></TableRow></TableHeader>
              <TableBody>
                {data.items.map((a) => (
                  <TableRow key={a.id} className="cursor-pointer" onClick={() => setAsset(a.id)}>
                    <TableCell><div className="text-sm font-medium">{a.hostname}</div><div className="text-[11px] text-muted-foreground">{a.id} · {a.ip_address} · {a.asset_type}{a.cloud_provider && ` · ${a.cloud_provider}`}</div></TableCell>
                    <TableCell className="text-xs capitalize">{a.environment ?? "—"}{a.operational_status && a.operational_status !== "operational" && <div className="text-risk-medium">{a.operational_status}</div>}</TableCell>
                    <TableCell className="text-xs capitalize">{a.business_criticality ?? "—"}</TableCell>
                    <TableCell className="text-xs">{a.internet_exposed === null ? <span className="text-muted-foreground">Unknown</span> : a.internet_exposed ? <span className="text-risk-high">Yes</span> : "No"}</TableCell>
                    <TableCell className="text-xs">{a.business_service?.name ?? "—"}</TableCell>
                    <TableCell className="text-xs">{a.owner ?? <span className="text-risk-medium">Missing</span>}</TableCell>
                    <TableCell className="text-right tabular">{a.open_findings}</TableCell>
                    <TableCell>{a.max_risk_score ? <RiskBadge level={a.max_risk_score >= 85 ? "critical" : a.max_risk_score >= 70 ? "high" : a.max_risk_score >= 40 ? "medium" : "low"} score={a.max_risk_score} /> : "—"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table></div>
            <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPage={setPage} />
          </>
        )}
      </CardContent></Card>
      <AssetDrawer id={assetId} onClose={() => setAsset(null)} />
    </>
  );
}

export default function AssetsPage() {
  return <Suspense fallback={<LoadingState rows={10} />}><AssetsContent /></Suspense>;
}
