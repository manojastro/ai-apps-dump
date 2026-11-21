"use client";

import Link from "next/link";
import { useState } from "react";

import { ChurnBand, EmptyNote, ErrorNote, LoadingBlock, Meter, PageHeader, Pagination, ReasonChips, StatTile } from "@/components/shared";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Select, Table, Td, Th } from "@/components/ui/primitives";
import { useApi } from "@/lib/api";
import type { ExpansionRow, Page, RetentionRow, RetentionSummary } from "@/lib/types";
import { formatCompact, formatDate, formatMoney, formatPercent } from "@/lib/utils";

const PAGE_SIZE = 20;

export default function RetentionPage() {
  const [page, setPage] = useState(1);
  const [band, setBand] = useState("high");
  const query = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
  if (band) query.set("band", band);

  const summary = useApi<RetentionSummary>("/churn/summary");
  const rows = useApi<Page<RetentionRow>>(`/churn/at-risk?${query}`);
  const expansion = useApi<Page<ExpansionRow>>("/expansion?page_size=10");
  const s = summary.data;

  return (
    <>
      <PageHeader title="Retention" description="Chance of cancelling or not renewing within 90 days. These are model estimates." />
      {summary.error && <ErrorNote message={summary.error.message} />}
      <div className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="At-risk ARR" value={s ? formatCompact(s.at_risk_arr) : "..."} detail={s ? `${s.at_risk_accounts} high-risk accounts` : undefined} />
        <StatTile label="Watch-list ARR" value={s ? formatCompact(s.watch_arr) : "..."} detail={s ? `${s.watch_accounts} medium-risk accounts` : undefined} />
        <StatTile label="Expected ARR loss" value={s ? formatCompact(s.expected_arr_loss) : "..."} detail="Sum of ARR x churn probability" />
        <StatTile label="ARR scored" value={s ? formatCompact(s.total_arr) : "..."} detail={s ? `${s.scored_accounts} accounts` : undefined} />
      </div>

      <Card className="mb-4">
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Accounts at risk</CardTitle>
            <CardDescription>Ordered by expected ARR loss</CardDescription>
          </div>
          <Select
            aria-label="Risk band"
            value={band}
            onChange={(e) => {
              setBand(e.target.value);
              setPage(1);
            }}
          >
            <option value="high">High risk</option>
            <option value="medium">Medium risk</option>
            <option value="low">Low risk</option>
            <option value="">All accounts</option>
          </Select>
        </CardHeader>
        {rows.loading && !rows.data ? (
          <LoadingBlock rows={8} />
        ) : rows.data && rows.data.items.length === 0 ? (
          <EmptyNote message="No accounts in this band." />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Account</Th><Th className="text-right">ARR</Th><Th>Churn probability</Th><Th>Band</Th><Th>Renewal</Th><Th className="text-right">Expected loss</Th><Th>Why</Th>
              </tr>
            </thead>
            <tbody>
              {rows.data?.items.map((row) => (
                <tr key={row.account_id} data-testid="retention-row" className="hover:bg-muted/40">
                  <Td className="min-w-44">
                    <Link href={`/accounts/${row.account_id}`} className="font-medium hover:underline">{row.name}</Link>
                    <p className="text-xs text-muted-foreground">{row.owner_name}</p>
                  </Td>
                  <Td className="text-right tabular-nums">{formatMoney(row.arr)}</Td>
                  <Td><Meter value={row.p_churn} /></Td>
                  <Td><ChurnBand band={row.band} /></Td>
                  <Td className="whitespace-nowrap">{formatDate(row.renewal_date)}</Td>
                  <Td className="text-right tabular-nums">{formatMoney(row.expected_arr_loss)}</Td>
                  <Td className="min-w-72"><ReasonChips reasons={row.reasons} /></Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
        {rows.data && <Pagination page={page} pageSize={PAGE_SIZE} total={rows.data.total} onPage={setPage} />}
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Expansion triggers</CardTitle>
          <CardDescription>Rule-based: usage near the seat limit, or fast growth in active users</CardDescription>
        </CardHeader>
        <CardContent className="p-0 pb-2">
          {expansion.loading && <LoadingBlock rows={4} />}
          {expansion.data?.items.length === 0 && <EmptyNote message="No expansion triggers right now." />}
          {expansion.data && expansion.data.items.length > 0 && (
            <Table>
              <thead><tr><Th>Account</Th><Th className="text-right">ARR</Th><Th className="text-right">Seats used</Th><Th className="text-right">User growth</Th><Th>Trigger</Th></tr></thead>
              <tbody>
                {expansion.data.items.map((row) => (
                  <tr key={row.account_id}>
                    <Td><Link href={`/accounts/${row.account_id}`} className="font-medium hover:underline">{row.name}</Link></Td>
                    <Td className="text-right tabular-nums">{formatMoney(row.arr)}</Td>
                    <Td className="text-right tabular-nums">{formatPercent(row.seat_utilization)}</Td>
                    <Td className="text-right tabular-nums">{formatPercent(row.user_growth)}</Td>
                    <Td>{row.triggers.join("; ")}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </CardContent>
      </Card>
    </>
  );
}
