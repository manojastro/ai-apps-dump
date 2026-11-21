"use client";

import Link from "next/link";
import { useState } from "react";

import { ChurnBand, EmptyNote, ErrorNote, HealthBadge, LoadingBlock, PageHeader, Pagination } from "@/components/shared";
import { Card, Input, Select, Table, Td, Th } from "@/components/ui/primitives";
import { useApi } from "@/lib/api";
import type { AccountRow, Page } from "@/lib/types";
import { formatMoney, titleCase } from "@/lib/utils";

const PAGE_SIZE = 25;

export default function AccountsPage() {
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [region, setRegion] = useState("");
  const [segment, setSegment] = useState("");
  const [status, setStatus] = useState("");

  const query = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
  if (q) query.set("q", q);
  if (region) query.set("region", region);
  if (segment) query.set("segment", segment);
  if (status) query.set("status", status);
  const { data, error, loading } = useApi<Page<AccountRow>>(`/accounts?${query}`);

  const change = (setter: (value: string) => void) => (value: string) => {
    setter(value);
    setPage(1);
  };

  return (
    <>
      <PageHeader title="Accounts" description="CRM, billing, usage and support data in one record." />
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Input className="max-w-xs" placeholder="Search by name or domain" aria-label="Search accounts" value={q} onChange={(e) => change(setQ)(e.target.value)} />
        <Select aria-label="Region" value={region} onChange={(e) => change(setRegion)(e.target.value)}>
          <option value="">All regions</option>
          {["NA", "EMEA", "APAC", "LATAM"].map((r) => <option key={r} value={r}>{r}</option>)}
        </Select>
        <Select aria-label="Segment" value={segment} onChange={(e) => change(setSegment)(e.target.value)}>
          <option value="">All segments</option>
          <option value="enterprise">Enterprise</option>
          <option value="mid_market">Mid market</option>
          <option value="smb">SMB</option>
        </Select>
        <Select aria-label="Status" value={status} onChange={(e) => change(setStatus)(e.target.value)}>
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="churned">Churned</option>
        </Select>
      </div>
      {error && <ErrorNote message={error.message} />}
      <Card>
        {loading && !data ? (
          <LoadingBlock rows={10} />
        ) : data && data.items.length === 0 ? (
          <EmptyNote message="No accounts match these filters." />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Account</Th>
                <Th>Segment</Th>
                <Th>Region</Th>
                <Th className="text-right">ARR</Th>
                <Th>Health</Th>
                <Th>Churn risk</Th>
                <Th>Owner</Th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((account) => (
                <tr key={account.id} data-testid="account-row" className="hover:bg-muted/40">
                  <Td>
                    <Link href={`/accounts/${account.id}`} className="font-medium hover:underline">{account.name}</Link>
                    <p className="text-xs text-muted-foreground">{account.industry ?? "Industry unknown"}</p>
                  </Td>
                  <Td>{titleCase(account.segment)}</Td>
                  <Td>{account.region}</Td>
                  <Td className="text-right tabular-nums">{formatMoney(account.arr)}</Td>
                  <Td><HealthBadge status={account.status === "churned" ? null : account.health_status} /></Td>
                  <Td>{account.status === "churned" ? <span className="text-xs text-muted-foreground">Churned</span> : <ChurnBand band={account.churn_band} />}</Td>
                  <Td className="whitespace-nowrap">{account.owner_name}</Td>
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
