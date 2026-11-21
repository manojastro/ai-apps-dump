"use client";
import Link from "next/link";
import { useSession } from "@/components/shell";
import { Badge, Card, Spinner, StatusBadge, when } from "@/components/ui";
import { useApi } from "@/lib/hooks";

type Row = { id: string; spread_id: string; version: number; status: string; hash: string; render_status: string; created_at: string; stale: boolean; company: string; scope: string };

export default function ExportsPage() {
  const { workspaceId } = useSession();
  const { data } = useApi<Row[]>(workspaceId ? `/workspaces/${workspaceId}/exports` : null);
  return (
    <Card title="Export history">
      {!data ? <Spinner /> : (
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-muted"><tr className="border-b border-line"><th className="py-2">Created</th><th>Company / scope</th><th>Version</th><th>Status</th><th>Snapshot</th><th>Files</th></tr></thead>
          <tbody>{data.map((e) => (
            <tr key={e.id} className="border-b border-line/60">
              <td className="py-1.5 text-xs">{when(e.created_at)}</td>
              <td><Link className="text-brand hover:underline" href={`/spreads/${e.spread_id}`}>{e.company}</Link> <span className="text-muted">{e.scope}</span></td>
              <td>v{e.version} {e.stale && <Badge tone="bad">stale</Badge>}</td>
              <td><Badge tone={e.status === "approved" ? "ok" : "warn"}>{e.status === "approved" ? "approved" : "draft (unreviewed)"}</Badge> <StatusBadge status={e.render_status} /></td>
              <td className="font-mono text-[11px]">{e.hash.slice(0, 16)}…</td>
              <td className="space-x-3">{e.render_status === "ok" && <><a className="text-brand underline" href={`/api/engine/exports/${e.id}/download/xlsx`}>Excel</a><a className="text-brand underline" href={`/api/engine/exports/${e.id}/download/pdf`}>PDF</a></>}</td>
            </tr>))}
            {data.length === 0 && <tr><td colSpan={6} className="py-3 text-muted">No exports yet.</td></tr>}
          </tbody>
        </table>
      )}
    </Card>
  );
}
