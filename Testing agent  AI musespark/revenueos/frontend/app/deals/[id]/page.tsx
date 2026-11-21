"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { CitationChip } from "@/components/citations";
import { DealBand, ErrorNote, LoadingBlock, PageHeader, StatTile } from "@/components/shared";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/primitives";
import { useApi } from "@/lib/api";
import type { DealExplain } from "@/lib/types";
import { formatCompact, formatDate, formatPercent, titleCase } from "@/lib/utils";

export default function DealPage() {
  const { id } = useParams<{ id: string }>();
  const { data: deal, error, loading } = useApi<DealExplain>(`/deals/${id}/explain`);

  if (loading) return <LoadingBlock rows={8} />;
  if (error) return <ErrorNote message={error.status === 404 ? "Deal not found, or it belongs to another team." : error.message} />;
  if (!deal) return null;

  const risks = deal.reasons.filter((r) => r.direction === "risk");
  const positives = deal.reasons.filter((r) => r.direction === "positive");

  return (
    <>
      <PageHeader title={deal.name} description={`${titleCase(deal.type)} deal, owned by ${deal.owner_name ?? "nobody"}`}>
        <DealBand band={deal.risk_band} />
      </PageHeader>
      <div className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Amount" value={formatCompact(deal.amount)} />
        <StatTile
          label={deal.outcome ? "Outcome" : "Win probability"}
          value={deal.outcome ? titleCase(deal.outcome) : formatPercent(deal.p_win)}
          detail={deal.outcome ? undefined : "Model estimate"}
        />
        <StatTile label="Stage" value={titleCase(deal.stage)} />
        <StatTile label="Close date" value={formatDate(deal.close_date)} detail={deal.discount_pct !== null ? `Discount ${deal.discount_pct}%` : "Discount not recorded"} />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>What is hurting this deal</CardTitle>
            <CardDescription>Largest SHAP contributions, in plain language</CardDescription>
          </CardHeader>
          <CardContent>
            {risks.length ? (
              <ul className="list-disc space-y-1 pl-4 text-sm">{risks.map((r) => <li key={r.feature}>{r.text}</li>)}</ul>
            ) : (
              <p className="text-sm text-muted-foreground">No major negative factors found.</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>What is helping</CardTitle>
          </CardHeader>
          <CardContent>
            {positives.length ? (
              <ul className="list-disc space-y-1 pl-4 text-sm">{positives.map((r) => <li key={r.feature}>{r.text}</li>)}</ul>
            ) : (
              <p className="text-sm text-muted-foreground">No major positive factors found.</p>
            )}
          </CardContent>
        </Card>
      </div>
      <p className="mt-4 text-xs text-muted-foreground">
        Account: <Link href={`/accounts/${deal.account_id}`} className="underline">{deal.account_name}</Link>
        {" · "}Model {deal.model_algorithm ?? "unknown"}, version {deal.model_version ?? "unknown"}
        {" · "}Source <CitationChip cite={deal.cite} />
      </p>
    </>
  );
}
