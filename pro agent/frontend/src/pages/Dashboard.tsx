import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, inr, seconds, when } from "../api";
import { useAuth } from "../auth";
import { Badge, Card, Empty, ErrorBox, Loading, PageHeader, Status, SyntheticBanner } from "../ui";

export default function Dashboard() {
  const { has } = useAuth();
  const runs = useQuery({ queryKey: ["runs"], queryFn: () => api("/api/runs?limit=50"), refetchInterval: 5000 });
  const approvals = useQuery({ queryKey: ["approvals", "pending"], queryFn: () => api("/api/approvals?status=pending") });
  const health = useQuery({ queryKey: ["health"], queryFn: () => api("/api/health"), refetchInterval: 15000 });

  return (
    <div className="space-y-5">
      <PageHeader title="Procurement dashboard" subtitle="Runs, pending approvals and worker health for your tenant."
        actions={has("requester") ? <Link to="/requests/new" className="rounded-md bg-brand px-3.5 py-2 text-sm font-medium text-white">New request</Link> : undefined} />
      <SyntheticBanner />
      <div className="grid gap-4 sm:grid-cols-3">
        <Card title="Pending approvals">
          <p className="text-3xl font-semibold tabular">{approvals.data?.items.length ?? "—"}</p>
          <Link to="/approvals" className="text-sm text-brand hover:underline">Open inbox</Link>
        </Card>
        <Card title="Worker">
          <p className="text-sm">{health.data ? (health.data.workers_alive > 0
            ? <Badge kind="good">{health.data.workers_alive} alive</Badge> : <Badge kind="bad">no live worker</Badge>) : "—"}</p>
          <p className="mt-2 text-xs text-muted">Mode: {health.data?.mode} · Dry run: {String(health.data?.dry_run ?? "")}</p>
        </Card>
        <Card title="Runs">
          <p className="text-3xl font-semibold tabular">{runs.data?.items.length ?? "—"}</p>
          <p className="text-xs text-muted">most recent 50</p>
        </Card>
      </div>
      <Card title="Recent runs">
        {runs.isLoading ? <Loading /> : runs.error ? <ErrorBox error={runs.error} /> : runs.data.items.length === 0 ? (
          <Empty>No runs yet. {has("requester") ? <Link className="text-brand" to="/requests/new">Create a request</Link> : "A requester can create one."}</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs text-muted">
                <tr><th className="py-2 pr-3">Request</th><th className="pr-3">Status</th><th className="pr-3">Phase</th>
                  <th className="pr-3">Mode</th><th className="pr-3 text-right">Actions</th><th className="pr-3 text-right">Active</th>
                  <th className="pr-3">Outcome</th><th>Started</th></tr>
              </thead>
              <tbody>
                {runs.data.items.map((r: any) => (
                  <tr key={r.id} className="border-t border-line">
                    <td className="py-2 pr-3"><Link className="text-brand hover:underline" to={`/runs/${r.id}`}>{r.request_title ?? r.id.slice(0, 8)}</Link></td>
                    <td className="pr-3"><Status value={r.status} /></td>
                    <td className="pr-3 text-muted">{r.phase.replaceAll("_", " ")}</td>
                    <td className="pr-3">{r.simulated_model ? <Badge kind="warn">simulated</Badge> : <Badge kind="info">{r.model_name}</Badge>}</td>
                    <td className="pr-3 text-right tabular">{r.action_count}</td>
                    <td className="pr-3 text-right tabular">{seconds(r.active_ms)}</td>
                    <td className="pr-3">{r.outcome ? <Status value={r.outcome} /> : "—"}</td>
                    <td className="text-muted">{when(r.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      <p className="text-xs text-muted">Budget per run defaults to {inr(500000)} in the demo request; totals include synthetic tax and shipping.</p>
    </div>
  );
}
