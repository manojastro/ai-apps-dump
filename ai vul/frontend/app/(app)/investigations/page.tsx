"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { RiskBadge, StatusBadge } from "@/components/badges";
import { EmptyState, ErrorState, LoadingState, PageHeader, Pagination } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, qs } from "@/lib/api";
import { fmtDate, fmtRelative } from "@/lib/format";
import type { Page, WorkflowRun } from "@/lib/types";

const FILTERS: Record<string, string | undefined> = {
  all: undefined,
  active: "queued,running,waiting_manual_review,waiting_approval,waiting_sync_retry,waiting_evidence",
  attention: "waiting_manual_review,waiting_approval,waiting_sync_retry",
  closed: "completed,rejected,blocked,failed,cancelled",
};

export default function InvestigationsPage() {
  const [tab, setTab] = useState("all");
  const [page, setPage] = useState(1);
  const query = qs({ status: FILTERS[tab], page, page_size: 20 });
  const { data, error, isLoading, refetch } = useQuery({
    queryKey: ["workflows", query],
    queryFn: () => api.get<Page<WorkflowRun>>(`/workflows${query}`),
    placeholderData: keepPreviousData,
    refetchInterval: 10_000,
  });
  return (
    <>
      <PageHeader
        title="AI investigations"
        description="Each investigation is a durable LangGraph workflow: eight specialised agents, deterministic gates and human interrupts. Start one from any finding."
        actions={<Button size="sm" asChild><Link href="/vulnerabilities">Start from a finding</Link></Button>}
      />
      <Tabs value={tab} onValueChange={(v) => { setTab(v); setPage(1); }} className="mb-3">
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="active">Active</TabsTrigger>
          <TabsTrigger value="attention">Needs a human</TabsTrigger>
          <TabsTrigger value="closed">Closed</TabsTrigger>
        </TabsList>
      </Tabs>
      <Card>
        <CardContent>
          {isLoading && <LoadingState />}
          {error && <ErrorState error={error} onRetry={refetch} />}
          {data && data.items.length === 0 && <EmptyState title="No investigations in this view" />}
          {data && data.items.length > 0 && (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Finding</TableHead><TableHead>Risk</TableHead><TableHead>Status</TableHead>
                      <TableHead>Current step</TableHead><TableHead>Model</TableHead><TableHead>Started</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.items.map((r) => (
                      <TableRow key={r.id}>
                        <TableCell>
                          <Link href={`/investigations/${r.id}`} className="font-mono text-xs font-medium text-primary hover:underline">{r.cve_id}</Link>
                          <div className="text-xs text-muted-foreground">{r.hostname}</div>
                        </TableCell>
                        <TableCell><RiskBadge level={r.risk_level} score={r.risk_score} /></TableCell>
                        <TableCell><StatusBadge status={r.status} /></TableCell>
                        <TableCell className="max-w-72 text-xs">{r.current_node?.replaceAll("_", " ")}<div className="truncate text-muted-foreground">{r.waiting_reason}</div></TableCell>
                        <TableCell className="text-xs text-muted-foreground">{r.provider}/{r.model}</TableCell>
                        <TableCell className="text-xs text-muted-foreground" title={fmtDate(r.started_at)}>{fmtRelative(r.started_at)}</TableCell>
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
    </>
  );
}
