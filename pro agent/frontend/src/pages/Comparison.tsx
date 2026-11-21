import { Fragment, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, inr } from "../api";
import { Badge, Card, Empty, ErrorBox, Loading, PageHeader, SyntheticBanner } from "../ui";

export function FailedRules({ results }: { results: any[] }) {
  const failed = results.filter((r) => !r.passed);
  if (!failed.length) return <Badge kind="good">all rules pass</Badge>;
  return (
    <ul className="space-y-0.5 text-xs">
      {failed.map((r) => (
        <li key={r.rule} className={r.hard ? "text-bad" : "text-warn"}>
          <span className="font-mono">{r.rule}</span>{r.hard ? "" : " (preference)"}: expected {r.expected}, observed {r.observed}
        </li>
      ))}
    </ul>
  );
}

const age = (s: number | null) => (s === null ? "—" : s < 120 ? `${s}s` : `${Math.round(s / 60)}m`);

export default function Comparison() {
  const { id = "" } = useParams();
  const q = useQuery({ queryKey: ["comparison", id], queryFn: () => api(`/api/runs/${id}/comparison`), refetchInterval: 5000 });
  const [open, setOpen] = useState<string | null>(null);
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox error={q.error} />;
  const { quotes, recommendation, selected_quote_id, ranking_rule } = q.data;
  const latest = quotes.filter((x: any) => !quotes.some((y: any) => y.supersedes_id === x.id));
  return (
    <div className="space-y-5">
      <PageHeader title="Quote comparison" subtitle={`Ranking: ${ranking_rule}.`}
        actions={<>
          <a className="rounded-md border border-line bg-white px-3.5 py-2 text-sm" href={`/api/runs/${id}/comparison.csv`}>Export CSV</a>
          <a className="rounded-md border border-line bg-white px-3.5 py-2 text-sm" href={`/api/runs/${id}/summary.pdf`}>PDF summary</a>
          <Link className="rounded-md border border-line bg-white px-3.5 py-2 text-sm" to={`/runs/${id}`}>Back to run</Link>
        </>} />
      <SyntheticBanner simulated={recommendation?.simulated} />
      {recommendation && (
        <Card title="Recommendation and verification">
          <p className="text-sm">{recommendation.simulated ? "Simulated" : "Model"} recommendation: {recommendation.rationale}</p>
          {recommendation.verifier?.rejected ? (
            <div className="mt-2 rounded-md bg-bad-soft p-3 text-sm text-bad">
              <p className="font-medium">Verifier rejected the recommendation.</p>
              <FailedRules results={recommendation.verifier.failed_rules} />
              <p className="mt-1 text-ink">The top-ranked eligible offer was selected instead.</p>
            </div>
          ) : <p className="mt-1 text-sm text-good">Verifier accepted the recommendation (all hard rules pass).</p>}
        </Card>
      )}
      <Card title={`Offers (${latest.length})`}>
        {latest.length === 0 ? <Empty>No offers have been extracted yet.</Empty> : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[960px] text-sm">
              <thead className="text-left text-xs text-muted">
                <tr><th className="py-2 pr-2">Supplier / product</th><th className="pr-2">Spec</th><th className="pr-2 text-right">Qty</th>
                  <th className="pr-2 text-right">Stock</th><th className="pr-2 text-right">Unit</th><th className="pr-2 text-right">Tax</th>
                  <th className="pr-2 text-right">Shipping</th><th className="pr-2 text-right">Landed total</th><th className="pr-2">Delivery</th>
                  <th className="pr-2">Age</th><th>Eligibility</th></tr>
              </thead>
              <tbody>
                {latest.map((x: any) => (
                  <Fragment key={x.id}>
                    <tr className={`border-t border-line align-top ${x.id === selected_quote_id ? "bg-brand-soft/60" : ""}`}>
                      <td className="py-2 pr-2">
                        <p className="font-medium">{x.supplier.name} {x.supplier.synthetic && <span className="text-xs text-muted">(synthetic)</span>}</p>
                        <p className="text-xs text-muted">{x.sku} · {x.product_name}</p>
                        {x.id === selected_quote_id && <Badge kind="info">selected</Badge>}
                      </td>
                      <td className="pr-2 text-xs">{x.spec.ram_gb ?? "?"} GB RAM · {x.spec.ssd_gb ?? "?"} GB {x.spec.storage_type ?? ""}<br />{x.spec.cpu ?? ""}<br />pack: {x.pack_size ?? "ambiguous"}</td>
                      <td className="pr-2 text-right tabular">{x.quantity}</td>
                      <td className="pr-2 text-right tabular">{x.stock_observed ?? "?"}</td>
                      <td className="pr-2 text-right tabular">{inr(x.unit_price)}<br /><span className="text-xs text-muted">{x.price_basis ?? "basis unknown"}</span></td>
                      <td className="pr-2 text-right tabular">{inr(x.tax)}</td>
                      <td className="pr-2 text-right tabular">{inr(x.shipping)}</td>
                      <td className="pr-2 text-right font-semibold tabular">{inr(x.total)}</td>
                      <td className="pr-2 text-xs">{x.delivery_date ?? "—"}<br /><span className="text-muted">{x.delivery_confidence}</span></td>
                      <td className="pr-2 text-xs">{age(x.age_seconds)}</td>
                      <td>
                        {x.eligible ? <Badge kind="good">eligible</Badge> : <Badge kind="bad">ineligible</Badge>}
                        <div className="mt-1"><FailedRules results={x.policy_results.filter((r: any) => r.hard)} /></div>
                        <button className="mt-1 text-xs text-brand hover:underline" onClick={() => setOpen(open === x.id ? null : x.id)}>
                          {open === x.id ? "Hide" : "Show"} all checks & evidence
                        </button>
                      </td>
                    </tr>
                    {open === x.id && (
                      <tr className="bg-canvas"><td colSpan={11} className="p-3 text-xs">
                        <div className="grid gap-3 md:grid-cols-2">
                          <ul className="space-y-0.5">{x.policy_results.map((r: any) => (
                            <li key={r.rule} className={r.passed ? "text-good" : r.hard ? "text-bad" : "text-warn"}>
                              {r.passed ? "✓" : "✗"} <span className="font-mono">{r.rule}</span> — {r.message} (expected {r.expected}; observed {r.observed})
                            </li>))}</ul>
                          <div className="space-y-1">
                            <p>Supplier quote ref: <span className="font-mono">{x.supplier_quote_ref}</span></p>
                            <p>Canonical hash: <span className="font-mono">{x.canonical_hash.slice(0, 16)}…</span></p>
                            <p>Extraction: {x.extraction_method}</p>
                            {x.issues.length > 0 && <p className="text-warn">Notes: {x.issues.join("; ")}</p>}
                            <p className="flex flex-wrap gap-2">{x.evidence_ids.map((e: string) => (
                              <a key={e} className="text-brand hover:underline" href={`/api/evidence/${e}`} target="_blank" rel="noreferrer">evidence {e.slice(0, 6)}</a>))}</p>
                          </div>
                        </div>
                      </td></tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
