"use client";

import { useState } from "react";

import { useUser } from "@/components/app-shell";
import { EmptyNote, ErrorNote, LoadingBlock, PageHeader, Pagination, StatTile, StatusBadge } from "@/components/shared";
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Table, Td, Th } from "@/components/ui/primitives";
import { useApi } from "@/lib/api";
import type { AuditRow, DataHealth, ModelRow, Page } from "@/lib/types";
import { titleCase } from "@/lib/utils";

const TABS = ["models", "data", "audit"] as const;

export default function AdminPage() {
  const user = useUser();
  const [tab, setTab] = useState<(typeof TABS)[number]>("models");
  const canAudit = user?.role === "admin";

  if (user && !["admin", "revops"].includes(user.role)) {
    return <ErrorNote message="This page is only available to admin and RevOps users." />;
  }

  return (
    <>
      <PageHeader title="Admin" description="Model versions, data health and the copilot audit log." />
      <div className="mb-4 flex gap-1" role="tablist">
        {TABS.filter((t) => t !== "audit" || canAudit).map((t) => (
          <Button key={t} role="tab" aria-selected={tab === t} variant={tab === t ? "default" : "outline"} size="sm" onClick={() => setTab(t)}>
            {t === "models" ? "Models" : t === "data" ? "Data health" : "Audit log"}
          </Button>
        ))}
      </div>
      {tab === "models" && <Models />}
      {tab === "data" && <Data />}
      {tab === "audit" && canAudit && <Audit />}
    </>
  );
}

function Models() {
  const { data, error, loading } = useApi<ModelRow[]>("/admin/models");
  if (loading) return <LoadingBlock />;
  if (error) return <ErrorNote message={error.message} />;
  return (
    <Card>
      <Table>
        <thead>
          <tr><Th>Model</Th><Th>Version</Th><Th>Algorithm</Th><Th>Last trained</Th><Th className="text-right">Held-out AUC</Th><Th className="text-right">95% interval</Th><Th>Status</Th></tr>
        </thead>
        <tbody>
          {data?.map((model) => {
            const test = model.metrics.test?.selected;
            return (
              <tr key={`${model.model_name}-${model.version}`}>
                <Td className="font-medium">{titleCase(model.model_name)}</Td>
                <Td className="font-mono text-xs">{model.version}</Td>
                <Td>{titleCase(model.algorithm)}</Td>
                <Td className="whitespace-nowrap">{new Date(model.trained_at).toLocaleString()}</Td>
                <Td className="text-right tabular-nums">{test?.auc.toFixed(3) ?? "-"}</Td>
                <Td className="text-right tabular-nums">{test ? `${test.auc_ci95[0].toFixed(2)} to ${test.auc_ci95[1].toFixed(2)}` : "-"}</Td>
                <Td><StatusBadge tone={model.is_active ? "good" : "neutral"} label={model.is_active ? "Active" : "Retired"} /></Td>
              </tr>
            );
          })}
        </tbody>
      </Table>
      <p className="p-3 text-xs text-muted-foreground">Measured on synthetic data with planted rules. This shows the pipeline works, not real-world accuracy.</p>
    </Card>
  );
}

function Data() {
  const { data, error, loading } = useApi<DataHealth>("/admin/data-quality");
  if (loading) return <LoadingBlock />;
  if (error) return <ErrorNote message={error.message} />;
  if (!data) return null;
  return (
    <>
      <div className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-3">
        {Object.entries(data.summary).map(([key, value]) => (
          <StatTile key={key} label={titleCase(key)} value={value.toLocaleString()} />
        ))}
        <StatTile label="Rows quarantined by loader" value={data.load_rejects.toLocaleString()} />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Row counts</CardTitle>
          <CardDescription>{data.run_at ? `Last checked ${new Date(data.run_at).toLocaleString()}` : "Never checked"}</CardDescription>
        </CardHeader>
        <CardContent className="p-0 pb-2">
          <Table>
            <thead><tr><Th>Table</Th><Th className="text-right">Rows</Th></tr></thead>
            <tbody>
              {Object.entries(data.row_counts).map(([name, count]) => (
                <tr key={name}><Td>{name}</Td><Td className="text-right tabular-nums">{count.toLocaleString()}</Td></tr>
              ))}
            </tbody>
          </Table>
        </CardContent>
      </Card>
    </>
  );
}

function Audit() {
  const [page, setPage] = useState(1);
  const { data, error, loading } = useApi<Page<AuditRow>>(`/admin/audit?page=${page}&page_size=20`);
  if (loading && !data) return <LoadingBlock />;
  if (error) return <ErrorNote message={error.message} />;
  if (data?.items.length === 0) return <Card><EmptyNote message="No copilot questions have been asked yet." /></Card>;
  return (
    <Card>
      <Table>
        <thead><tr><Th>When</Th><Th>User</Th><Th>Question</Th><Th>Tools</Th><Th>Citations</Th></tr></thead>
        <tbody>
          {data?.items.map((row) => (
            <tr key={row.id}>
              <Td className="whitespace-nowrap">{new Date(row.created_at).toLocaleString()}</Td>
              <Td>{row.user_email}</Td>
              <Td className="min-w-64">{row.question}</Td>
              <Td>{row.tools_called.map((t) => t.name).join(", ") || "-"}</Td>
              <Td className="tabular-nums">{row.cited_sources.valid.length}</Td>
            </tr>
          ))}
        </tbody>
      </Table>
      {data && <Pagination page={page} pageSize={20} total={data.total} onPage={setPage} />}
    </Card>
  );
}
