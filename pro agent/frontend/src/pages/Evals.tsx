import { useQuery } from "@tanstack/react-query";
import { api, when } from "../api";
import { Badge, Card, Empty, ErrorBox, Loading, PageHeader } from "../ui";

const pct = (v: unknown) => (typeof v === "number" ? `${(v * 100).toFixed(0)}%` : String(v ?? "—"));

export default function Evals() {
  const q = useQuery({ queryKey: ["evals"], queryFn: () => api("/api/evals") });
  return (
    <div className="space-y-5">
      <PageHeader title="Evaluation results" subtitle="Reproducible scenarios against the controlled mock environment. Run with: python -m procnav.evals.run" />
      {q.isLoading ? <Loading /> : q.error ? <ErrorBox error={q.error} /> : q.data.items.length === 0 ? <Empty>No evaluation runs recorded yet.</Empty> : (
        q.data.items.map((e: any) => (
          <Card key={e.id} title={<>{e.label} <Badge kind={e.mode === "fixture" ? "warn" : "info"}>{e.mode}</Badge></>} actions={<span className="text-xs text-muted">{when(e.created_at)}</span>}>
            <div className="grid gap-4 lg:grid-cols-2">
              <div>
                <h3 className="mb-2 text-xs font-semibold uppercase text-muted">Metrics by workflow</h3>
                <div className="overflow-x-auto"><table className="w-full text-sm">
                  <thead className="text-left text-xs text-muted"><tr><th className="py-1 pr-2">Workflow</th><th className="pr-2">Completion</th>
                    <th className="pr-2">Correct supplier</th><th className="pr-2">Safe blocks</th><th className="pr-2">Incorrect purchases</th><th>Avg actions</th></tr></thead>
                  <tbody>{Object.entries(e.metrics.by_workflow ?? {}).map(([wf, m]: any) => (
                    <tr key={wf} className="border-t border-line">
                      <td className="py-1 pr-2 font-medium">{wf}</td><td className="pr-2">{pct(m.completion_rate)}</td>
                      <td className="pr-2">{pct(m.eligible_selection_rate)}</td><td className="pr-2">{m.blocked_safe_failures}</td>
                      <td className={`pr-2 ${m.incorrect_purchases ? "text-bad" : ""}`}>{m.incorrect_purchases}</td><td>{m.avg_actions}</td>
                    </tr>))}</tbody>
                </table></div>
              </div>
              <div>
                <h3 className="mb-2 text-xs font-semibold uppercase text-muted">Mandatory gates</h3>
                <ul className="space-y-1 text-sm">{Object.entries(e.gates ?? {}).map(([k, v]: any) => (
                  <li key={k} className={v.passed ? "text-good" : "text-bad"}>{v.passed ? "✓" : "✗"} {k.replaceAll("_", " ")} <span className="text-muted">({v.observed})</span></li>))}</ul>
              </div>
            </div>
            <details className="mt-3 text-sm"><summary className="cursor-pointer text-brand">Scenario results ({e.results.length})</summary>
              <div className="mt-2 overflow-x-auto"><table className="w-full text-xs">
                <thead className="text-left text-muted"><tr><th className="py-1 pr-2">Scenario</th><th className="pr-2">Workflow</th><th className="pr-2">Expected</th>
                  <th className="pr-2">Observed</th><th className="pr-2">Pass</th><th className="pr-2">Actions</th><th>Active</th></tr></thead>
                <tbody>{e.results.map((r: any, i: number) => (
                  <tr key={i} className="border-t border-line"><td className="py-1 pr-2">{r.scenario}</td><td className="pr-2">{r.workflow}</td>
                    <td className="pr-2">{r.expected_outcome}</td><td className="pr-2">{r.observed_outcome}</td>
                    <td className="pr-2">{r.passed ? <Badge kind="good">pass</Badge> : <Badge kind="bad">fail</Badge>}</td>
                    <td className="pr-2">{r.actions}</td><td>{(r.active_ms / 1000).toFixed(1)}s</td></tr>))}</tbody>
              </table></div>
            </details>
            <p className="mt-2 text-xs text-muted">Config: {JSON.stringify(e.config)}. Gates apply to the controlled mock environment only.</p>
          </Card>
        ))
      )}
    </div>
  );
}
