import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, inr, when } from "../api";
import { useAuth } from "../auth";
import { Badge, Button, Card, Empty, ErrorBox, KV, Loading, PageHeader, Status, SyntheticBanner } from "../ui";

const LEDGER = ["created", "approved", "submitting", "submitted", "reconciled"];

export function Orders() {
  const q = useQuery({ queryKey: ["orders"], queryFn: () => api("/api/orders?limit=50"), refetchInterval: 5000 });
  return (
    <div className="space-y-5">
      <PageHeader title="Orders" subtitle="Order ledger entries created only from consumed approvals." />
      <SyntheticBanner />
      <Card>
        {q.isLoading ? <Loading /> : q.error ? <ErrorBox error={q.error} /> : q.data.items.length === 0 ? <Empty>No orders yet.</Empty> : (
          <div className="overflow-x-auto"><table className="w-full text-sm">
            <thead className="text-left text-xs text-muted"><tr><th className="py-2 pr-3">Order</th><th className="pr-3">Supplier</th>
              <th className="pr-3">Ledger</th><th className="pr-3">Supplier ref</th><th className="pr-3 text-right">Total</th><th className="pr-3">Receipt</th><th>Created</th></tr></thead>
            <tbody>{q.data.items.map((o: any) => (
              <tr key={o.id} className="border-t border-line">
                <td className="py-2 pr-3"><Link className="font-mono text-brand hover:underline" to={`/orders/${o.id}`}>{o.intent_key}</Link></td>
                <td className="pr-3">{o.supplier_name}</td><td className="pr-3"><Status value={o.status} /></td>
                <td className="pr-3 font-mono">{o.supplier_order?.supplier_order_ref ?? "—"}</td>
                <td className="pr-3 text-right tabular">{inr(o.supplier_order?.total ?? o.max_amount)}</td>
                <td className="pr-3">{o.supplier_order?.verified ? <Badge kind="good">verified</Badge> : <Badge>not verified</Badge>}</td>
                <td className="text-muted">{when(o.created_at)}</td>
              </tr>))}</tbody>
          </table></div>
        )}
      </Card>
    </div>
  );
}

export function OrderDetail() {
  const { id = "" } = useParams();
  const { has } = useAuth();
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["order", id], queryFn: () => api(`/api/orders/${id}`), refetchInterval: 5000 });
  const reconcile = useMutation({ mutationFn: () => api(`/api/orders/${id}/reconcile`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["order", id] }) });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox error={q.error} />;
  const o = q.data;
  const so = o.supplier_order;
  const reached = LEDGER.indexOf(o.status);
  return (
    <div className="space-y-5">
      <PageHeader title={`Order ${o.intent_key}`} subtitle={<>{o.supplier_name} · <Link className="text-brand" to={`/runs/${o.run_id}`}>run</Link> · <Link className="text-brand" to={`/approvals/${o.approval_request_id}`}>approval</Link></>}
        actions={<Status value={o.status} />} />
      <SyntheticBanner />
      <Card title="Ledger state">
        <ol className="flex flex-wrap items-center gap-2 text-xs" aria-label="Order ledger progress">
          {LEDGER.map((s, i) => (
            <li key={s} className={`rounded-full px-2.5 py-1 ${reached >= i ? "bg-good-soft text-good" : "bg-canvas text-muted"}`}>{s}</li>
          ))}
          {!LEDGER.includes(o.status) && <li><Status value={o.status} /></li>}
        </ol>
        {o.status_reason && <p className="mt-2 text-sm text-muted">{o.status_reason}</p>}
        {["unknown", "cancellation_requested", "submitting"].includes(o.status) && (has("approver") || has("admin")) && (
          <div className="mt-3"><Button variant="secondary" onClick={() => reconcile.mutate()}>Re-check supplier order history</Button>
            <p className="mt-1 text-xs text-muted">Reconciliation only reads order history. It never submits the order again.</p>
            <ErrorBox error={reconcile.error} /></div>
        )}
      </Card>
      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="Supplier order">
          {!so ? <Empty>No supplier order recorded.</Empty> : <KV items={[
            ["Supplier order ref", so.supplier_order_ref], ["SKU", so.sku ?? "—"], ["Quantity", so.quantity ?? "—"],
            ["Total", inr(so.total)], ["Currency", so.currency ?? "—"], ["Delivery date", so.delivery_date ?? "—"],
            ["Recorded via", so.reconciled_via.replaceAll("_", " ")],
            ["Receipt", so.verified ? <Badge key="v" kind="good">verified</Badge> : <Badge key="n" kind="warn">not verified</Badge>],
          ]} />}
          {so?.receipt_evidence_id && <a className="mt-3 inline-block text-sm text-brand hover:underline" href={`/api/evidence/${so.receipt_evidence_id}`}>Download redacted receipt</a>}
        </Card>
        <Card title="Receipt checks">
          {so?.verification?.checks ? (
            <ul className="space-y-1 text-sm">{Object.entries(so.verification.checks).map(([k, v]) => (
              <li key={k} className={v ? "text-good" : "text-bad"}>{v ? "✓" : "✗"} {k.replaceAll("_", " ")}</li>))}</ul>
          ) : <p className="text-sm text-muted">Pending.</p>}
        </Card>
      </div>
      <Card title="Submission attempts">
        {o.attempts.length === 0 ? <Empty>No attempts.</Empty> : (
          <ul className="space-y-2 text-sm">{o.attempts.map((a: any) => (
            <li key={a.attempt_no} className="border-b border-line pb-2">
              Attempt {a.attempt_no} by {a.worker_id}: <Status value={a.outcome} /> <span className="text-muted">{when(a.started_at)}</span>
              {a.detail?.code && <span className="ml-2 font-mono text-xs">{a.detail.code}</span>}
            </li>))}</ul>
        )}
      </Card>
      <Card title="Audit history">
        <ol className="space-y-1 text-sm">{o.history.map((h: any, i: number) => (
          <li key={i} className="flex gap-3"><span className="w-44 shrink-0 text-xs text-muted">{when(h.at)}</span>
            <span>{h.action} {h.data?.reason ? `— ${h.data.reason}` : ""}</span></li>))}</ol>
      </Card>
    </div>
  );
}
