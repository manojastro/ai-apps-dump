"use client";
import { useSession } from "@/components/shell";
import { Alert, Card, Spinner, StatusBadge, when } from "@/components/ui";
import { useApi } from "@/lib/hooks";

type Ev = { at: string; user: string | null; action: string; target: string | null; target_id: string | null; outcome: string; details: Record<string, unknown>; correlation_id: string | null };

export default function AuditPage() {
  const { workspaceId } = useSession();
  const { data, error } = useApi<Ev[]>(workspaceId ? `/workspaces/${workspaceId}/audit` : null);
  if (error) return <Alert tone="bad">{error}</Alert>;
  return (
    <Card title="Audit log (access, processing and review events; document content is never logged)">
      {!data ? <Spinner /> : (
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-muted"><tr className="border-b border-line"><th className="py-2">When</th><th>User</th><th>Action</th><th>Target</th><th>Outcome</th><th>Details</th><th>Correlation</th></tr></thead>
          <tbody>{data.map((e, i) => (
            <tr key={i} className="border-b border-line/60 align-top">
              <td className="py-1 text-xs">{when(e.at)}</td><td>{e.user ?? "—"}</td><td className="font-mono text-xs">{e.action}</td>
              <td className="text-xs">{e.target} {e.target_id?.slice(0, 8)}</td><td><StatusBadge status={e.outcome === "ok" ? "completed" : e.outcome === "denied" ? "rejected" : e.outcome} /></td>
              <td className="font-mono text-[11px] break-all">{JSON.stringify(e.details)}</td><td className="font-mono text-[11px]">{e.correlation_id}</td>
            </tr>))}
          </tbody>
        </table>
      )}
    </Card>
  );
}
