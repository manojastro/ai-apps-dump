import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, when } from "../api";
import { Badge, Card, Empty, ErrorBox, Input, Loading, PageHeader } from "../ui";

export default function Audit() {
  const [runId, setRunId] = useState("");
  const q = useQuery({
    queryKey: ["audit", runId],
    queryFn: () => api(`/api/audit?limit=200${/^[0-9a-f-]{36}$/.test(runId) ? `&run_id=${runId}` : ""}`),
  });
  return (
    <div className="space-y-5">
      <PageHeader title="Audit timeline" subtitle="Append-only, redacted record of user, agent and worker actions."
        actions={<Input aria-label="Filter by run ID" placeholder="Filter by run ID" value={runId} onChange={(e) => setRunId(e.target.value.trim())} className="w-80" />} />
      <Card>
        {q.isLoading ? <Loading /> : q.error ? <ErrorBox error={q.error} /> : q.data.items.length === 0 ? <Empty>No audit events.</Empty> : (
          <ol className="space-y-1 text-sm">
            {q.data.items.map((a: any) => (
              <li key={a.id} className="grid grid-cols-1 gap-1 border-b border-line py-1.5 md:grid-cols-[11rem_6rem_1fr]">
                <span className="text-xs text-muted">{when(a.at)}</span>
                <span><Badge kind={a.actor_type === "user" ? "info" : a.actor_type === "agent" ? "warn" : "muted"}>{a.actor_type}</Badge></span>
                <span className="min-w-0 break-words"><span className="font-medium">{a.action}</span>
                  <span className="text-muted"> · {a.entity_type} {a.entity_id?.slice(0, 8)}</span>
                  {a.data && Object.keys(a.data).length > 0 && <span className="block text-xs text-muted">{JSON.stringify(a.data).slice(0, 240)}</span>}
                </span>
              </li>
            ))}
          </ol>
        )}
      </Card>
    </div>
  );
}
