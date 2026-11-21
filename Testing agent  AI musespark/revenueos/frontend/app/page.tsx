"use client";

import Link from "next/link";

import { CitationChip } from "@/components/citations";
import { ForecastByTeamChart } from "@/components/charts";
import { EmptyNote, ErrorNote, LoadingBlock, PageHeader, StatTile, StatusBadge } from "@/components/shared";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Table, Td, Th } from "@/components/ui/primitives";
import { useApi } from "@/lib/api";
import type { Backtest, Brief, Forecast, ForecastChanges, RetentionSummary } from "@/lib/types";
import { formatCompact, formatDate, formatMoney, formatPercent, titleCase } from "@/lib/utils";

function signedMoney(value: number) {
  return `${value >= 0 ? "+" : "-"}${formatCompact(Math.abs(value))}`;
}

export default function DashboardPage() {
  const forecast = useApi<Forecast>("/forecast");
  const churn = useApi<RetentionSummary>("/churn/summary");
  const brief = useApi<Brief | null>("/brief");
  const changes = useApi<ForecastChanges>("/forecast/changes");
  const backtest = useApi<Backtest>("/forecast/backtest");
  const f = forecast.data;

  return (
    <>
      <PageHeader
        title="Dashboard"
        description={f ? `${f.quarter} forecast as of ${formatDate(f.as_of)}. Synthetic data.` : "Synthetic data."}
      />
      {forecast.error && <ErrorNote message={forecast.error.message} />}
      <div className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {f ? (
          <>
            <StatTile
              label="Expected revenue"
              value={formatCompact(f.expected)}
              detail={`Range ${formatCompact(f.low)} to ${formatCompact(f.high)} (P10 to P90)`}
            />
            <StatTile label="Rep commit" value={formatCompact(f.rep_commit)} detail="Closed won plus deals in negotiation" />
            <StatTile label="Closed won this quarter" value={formatCompact(f.closed_won_to_date)} detail={`${f.open_deals} open deals still expected`} />
          </>
        ) : (
          <div className="col-span-3"><LoadingBlock rows={2} /></div>
        )}
        <StatTile
          label="At-risk ARR"
          value={churn.data ? formatCompact(churn.data.at_risk_arr) : "..."}
          detail={churn.data ? <Link href="/retention" className="underline">{churn.data.at_risk_accounts} high-risk accounts</Link> : undefined}
        />
      </div>

      <div className="mb-4 grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Forecast vs. rep commit by team</CardTitle>
            <CardDescription>From {f?.simulations.toLocaleString() ?? "5,000"} simulated quarters</CardDescription>
          </CardHeader>
          <CardContent>{f ? <ForecastByTeamChart teams={f.by_team} /> : <LoadingBlock />}</CardContent>
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>What changed this week</CardTitle>
            <CardDescription>
              {changes.data?.available
                ? `${formatDate(changes.data.previous_date)} to ${formatDate(changes.data.current_date)}`
                : "Needs two weekly snapshots"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {changes.loading && <LoadingBlock rows={3} />}
            {changes.data?.available && (
              <>
                <p className="mb-3 text-2xl font-semibold tracking-tight">{signedMoney(changes.data.total_change ?? 0)}</p>
                <ul className="space-y-1.5 text-sm">
                  {Object.entries(changes.data.categories)
                    .filter(([key]) => key !== "minor_changes")
                    .map(([key, value]) => (
                      <li key={key} className="flex justify-between gap-3">
                        <span className="text-muted-foreground">{titleCase(key)} ({value.count})</span>
                        <span className="tabular-nums">{signedMoney(value.delta_expected)}</span>
                      </li>
                    ))}
                </ul>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="mb-4 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Daily brief: top deal risks</CardTitle>
            <CardDescription>{brief.data ? `Generated for ${formatDate(brief.data.brief_date)}` : "Not generated yet"}</CardDescription>
          </CardHeader>
          <CardContent>
            {brief.loading && <LoadingBlock rows={4} />}
            {brief.data?.content.top_risks.length === 0 && <EmptyNote message="No open deals in your scope." />}
            <ul className="divide-y">
              {brief.data?.content.top_risks.map((risk) => (
                <li key={risk.deal_id} className="py-2 text-sm">
                  <div className="flex justify-between gap-3">
                    <Link href={`/deals/${risk.deal_id}`} className="font-medium hover:underline">{risk.name}</Link>
                    <span className="whitespace-nowrap tabular-nums">{formatPercent(risk.p_win)} win</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {formatMoney(risk.amount)}{risk.reason ? ` · ${risk.reason}` : ""} <CitationChip cite={risk.cite} />
                  </p>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Daily brief: accounts needing attention</CardTitle>
            <CardDescription>Ordered by expected ARR loss</CardDescription>
          </CardHeader>
          <CardContent>
            {brief.loading && <LoadingBlock rows={4} />}
            {brief.data?.content.accounts_needing_attention.length === 0 && <EmptyNote message="No accounts in your scope." />}
            <ul className="divide-y">
              {brief.data?.content.accounts_needing_attention.map((account) => (
                <li key={account.account_id} className="py-2 text-sm">
                  <div className="flex justify-between gap-3">
                    <Link href={`/accounts/${account.account_id}`} className="font-medium hover:underline">{account.name}</Link>
                    <span className="whitespace-nowrap tabular-nums">{formatPercent(account.p_churn)} churn</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {formatMoney(account.arr)} ARR{account.reason ? ` · ${account.reason}` : ""} <CitationChip cite={account.cite} />
                  </p>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Forecast back-test</CardTitle>
          <CardDescription>
            Each quarter was forecast using only data available 14 days into it. These results prove the pipeline on planted rules, not real-world accuracy.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {backtest.loading && <LoadingBlock rows={4} />}
          {backtest.data && (
            <Table>
              <thead>
                <tr>
                  <Th>Quarter</Th>
                  <Th className="text-right">Actual</Th>
                  <Th className="text-right">Model</Th>
                  <Th className="text-right">Model error</Th>
                  <Th className="text-right">Stage-weighted error</Th>
                  <Th className="text-right">Rep commit error</Th>
                  <Th>In P10 to P90</Th>
                </tr>
              </thead>
              <tbody>
                {backtest.data.quarters.map((q) => (
                  <tr key={q.quarter}>
                    <Td>{q.quarter}</Td>
                    <Td className="text-right tabular-nums">{formatCompact(q.actual_from_pipeline)}</Td>
                    <Td className="text-right tabular-nums">{formatCompact(q.expected)}</Td>
                    <Td className="text-right tabular-nums">{formatPercent(q.abs_pct_error_model, 1)}</Td>
                    <Td className="text-right tabular-nums">{formatPercent(q.abs_pct_error_stage_weighted, 1)}</Td>
                    <Td className="text-right tabular-nums">{formatPercent(q.abs_pct_error_rep_commit, 1)}</Td>
                    <Td><StatusBadge tone={q.within_p10_p90 ? "good" : "serious"} label={q.within_p10_p90 ? "Yes" : "No"} /></Td>
                  </tr>
                ))}
                <tr className="font-medium">
                  <Td>Average</Td>
                  <Td />
                  <Td />
                  <Td className="text-right tabular-nums">{formatPercent(backtest.data.mape_model, 1)}</Td>
                  <Td className="text-right tabular-nums">{formatPercent(backtest.data.mape_stage_weighted, 1)}</Td>
                  <Td className="text-right tabular-nums">{formatPercent(backtest.data.mape_rep_commit, 1)}</Td>
                  <Td />
                </tr>
              </tbody>
            </Table>
          )}
        </CardContent>
      </Card>
    </>
  );
}
