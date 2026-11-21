"use client";
import Link from "next/link";
import { use, useCallback, useState } from "react";
import { EvidenceDrawer } from "@/components/evidence";
import { type Grid, Ratios, StatementGrid } from "@/components/grid";
import { AdjustmentHistory, ExceptionQueue, ReviewPanel, Validations } from "@/components/review-panels";
import { Alert, Badge, Spinner, StatusBadge, Tabs } from "@/components/ui";
import { useApi } from "@/lib/hooks";

type Detail = Parameters<typeof ReviewPanel>[0]["detail"] & {
  company: { id: string; name: string } | null; entity: { id: string; name: string } | null; scope: string; currency: string; display_scale: string; agent_mode: string;
};
type TabId = "balance_sheet" | "income_statement" | "cash_flow" | "ratios" | "exceptions" | "validations" | "adjustments" | "review";

export default function SpreadPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const detail = useApi<Detail>(`/spreads/${id}`);
  const grid = useApi<Grid>(`/spreads/${id}/grid`);
  const [tab, setTab] = useState<TabId>("balance_sheet");
  const [obs, setObs] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(true);
  const [merged, setMerged] = useState(true);
  const [adjKey, setAdjKey] = useState(0);
  const refresh = useCallback(() => { detail.reload(); grid.reload(); setAdjKey((k) => k + 1); }, [detail, grid]);

  if (detail.error) return <Alert tone="bad">{detail.error}</Alert>;
  if (!detail.data || !grid.data) return <Spinner />;
  const d = detail.data;
  const g = grid.data;
  const locked = d.review_status === "approved";
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        {d.company && <Link href={`/companies/${d.company.id}`} className="text-sm text-brand hover:underline">← {d.company.name}</Link>}
        <h1 className="text-xl font-semibold">{d.entity?.name} <span className="capitalize text-muted">· {d.scope}</span></h1>
        <Badge>{d.currency} · display {d.display_scale}</Badge>
        <Badge>version {d.version}</Badge>
        <StatusBadge status={d.review_status} />
        {d.review_status !== "approved" && <Badge tone="warn">UNREVIEWED — not signed off</Badge>}
        {d.blocking.length > 0 && <Badge tone="bad">{d.blocking.length} blocking issue(s)</Badge>}
      </div>
      <Tabs<TabId> label="Spread sections" value={tab} onChange={setTab} tabs={[
        { id: "balance_sheet", label: "Balance sheet" }, { id: "income_statement", label: "Income statement" }, { id: "cash_flow", label: "Cash flow" },
        { id: "ratios", label: "Ratios & trends" }, { id: "exceptions", label: "Exception queue" }, { id: "validations", label: "Validation results" },
        { id: "adjustments", label: "Adjustment history" }, { id: "review", label: "Review, approval & exports" },
      ]} />
      <div className="rounded-lg border border-line bg-panel p-4">
        {(tab === "balance_sheet" || tab === "income_statement" || tab === "cash_flow") && (
          <>
            <div className="mb-2 flex flex-wrap gap-4 text-xs text-muted">
              <label className="flex items-center gap-2"><input type="checkbox" checked={showAll} onChange={(e) => setShowAll(e.target.checked)} /> Show unmapped source rows</label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={!merged} onChange={(e) => setMerged(!e.target.checked)} /> Show every document&apos;s row separately (including superseded comparatives)</label>
            </div>
            <StatementGrid grid={g} statement={tab} onOpen={setObs} showAll={showAll} merged={merged} />
          </>
        )}
        {tab === "ratios" && <Ratios grid={g} onOpen={setObs} />}
        {tab === "exceptions" && <ExceptionQueue spreadId={id} onOpen={setObs} onChanged={refresh} locked={locked} />}
        {tab === "validations" && <Validations spreadId={id} version={d.version} onOpen={setObs} />}
        {tab === "adjustments" && <SpreadAdjustments key={adjKey} spreadId={id} onOpen={setObs} />}
        {tab === "review" && <ReviewPanel detail={d} onChanged={refresh} />}
      </div>
      <EvidenceDrawer spreadId={id} obsId={obs} onClose={() => setObs(null)} onChanged={refresh} taxonomy={g.taxonomy} locked={locked} />
    </div>
  );
}

type AdjRow = Parameters<typeof AdjustmentHistory>[0]["items"][number];

function SpreadAdjustments({ spreadId, onOpen }: { spreadId: string; onOpen: (id: string) => void }) {
  const { data } = useApi<AdjRow[]>(`/spreads/${spreadId}/adjustments`);
  if (!data) return <Spinner />;
  return <AdjustmentHistory items={data} onOpen={onOpen} />;
}
