"use client";

import Link from "next/link";
import { useState } from "react";

import { DealBand, EmptyNote, ErrorNote, LoadingBlock, Meter, PageHeader, Pagination, ReasonChips } from "@/components/shared";
import { Card, Input, Select, Table, Td, Th } from "@/components/ui/primitives";
import { useApi } from "@/lib/api";
import type { DealRow, Page } from "@/lib/types";
import { formatDate, formatMoney, titleCase } from "@/lib/utils";

const PAGE_SIZE = 25;

export default function DealsPage() {
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [stage, setStage] = useState("");
  const [band, setBand] = useState("");
  const [sort, setSort] = useState("risk");

  const query = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE), sort });
  if (q) query.set("q", q);
  if (stage) query.set("stage", stage);
  if (band) query.set("band", band);
  const { data, error, loading } = useApi<Page<DealRow>>(`/deals?${query}`);

  const change = <T,>(setter: (value: T) => void) => (value: T) => {
    setter(value);
    setPage(1);
  };

  return (
    <>
      <PageHeader title="Deals" description="Open pipeline, sorted by risk. Win probabilities are model estimates." />
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Input className="max-w-xs" placeholder="Search deals or accounts" aria-label="Search deals" value={q} onChange={(e) => change(setQ)(e.target.value)} />
        <Select aria-label="Stage" value={stage} onChange={(e) => change(setStage)(e.target.value)}>
          <option value="">All stages</option>
          {["prospecting", "qualification", "proposal", "negotiation"].map((s) => (
            <option key={s} value={s}>{titleCase(s)}</option>
          ))}
        </Select>
        <Select aria-label="Risk band" value={band} onChange={(e) => change(setBand)(e.target.value)}>
          <option value="">All risk levels</option>
          <option value="at_risk">At risk</option>
          <option value="watch">Watch</option>
          <option value="healthy">Healthy</option>
        </Select>
        <Select aria-label="Sort" value={sort} onChange={(e) => change(setSort)(e.target.value)}>
          <option value="risk">Sort: highest risk</option>
          <option value="value_at_risk">Sort: value at risk</option>
          <option value="amount">Sort: amount</option>
          <option value="close_date">Sort: close date</option>
        </Select>
      </div>
      {error && <ErrorNote message={error.message} />}
      <Card>
        {loading && !data ? (
          <LoadingBlock rows={10} />
        ) : data && data.items.length === 0 ? (
          <EmptyNote message="No deals match these filters." />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Deal</Th>
                <Th className="text-right">Amount</Th>
                <Th>Stage</Th>
                <Th>Close date</Th>
                <Th>Win probability</Th>
                <Th>Risk</Th>
                <Th>Why</Th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((deal) => (
                <tr key={deal.id} data-testid="deal-row" className="hover:bg-muted/40">
                  <Td className="min-w-48">
                    <Link href={`/deals/${deal.id}`} className="font-medium hover:underline">{deal.name}</Link>
                    <p className="text-xs text-muted-foreground">{deal.owner_name}</p>
                  </Td>
                  <Td className="text-right tabular-nums">{formatMoney(deal.amount)}</Td>
                  <Td className="whitespace-nowrap">{titleCase(deal.stage)}</Td>
                  <Td className="whitespace-nowrap">{formatDate(deal.close_date)}</Td>
                  <Td><Meter value={deal.p_win} /></Td>
                  <Td><DealBand band={deal.risk_band} /></Td>
                  <Td className="min-w-72"><ReasonChips reasons={deal.reasons} /></Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
        {data && <Pagination page={page} pageSize={PAGE_SIZE} total={data.total} onPage={setPage} />}
      </Card>
    </>
  );
}
