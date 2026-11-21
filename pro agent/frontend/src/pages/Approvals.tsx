import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, inr, when } from "../api";
import { useAuth } from "../auth";
import { Badge, Button, Card, Empty, ErrorBox, Field, Input, KV, Loading, PageHeader, Select, Status, SyntheticBanner } from "../ui";
import { FailedRules } from "./Comparison";

export function ApprovalInbox() {
  const [status, setStatus] = useState("pending");
  const q = useQuery({ queryKey: ["approvals", status], queryFn: () => api(`/api/approvals?status=${status}`), refetchInterval: 5000 });
  return (
    <div className="space-y-5">
      <PageHeader title="Approval inbox" subtitle="Each approval binds to one exact cart fingerprint. A changed offer invalidates it."
        actions={<Select aria-label="Filter by status" value={status} onChange={(e) => setStatus(e.target.value)} className="w-44">
          {["pending", "approved", "consumed", "invalidated", "rejected", "expired", "all"].map((s) => <option key={s}>{s}</option>)}
        </Select>} />
      <Card>
        {q.isLoading ? <Loading /> : q.error ? <ErrorBox error={q.error} /> : q.data.items.length === 0 ? <Empty>No {status} approvals.</Empty> : (
          <ul className="divide-y divide-line">
            {q.data.items.map((a: any) => (
              <li key={a.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div>
                  <Link to={`/approvals/${a.id}`} className="font-medium text-brand hover:underline">{a.request_title}</Link>
                  <p className="text-xs text-muted">{a.supplier_name} · {a.quantity} units · expires {when(a.expires_at)}</p>
                  {a.supersedes_id && <p className="text-xs text-warn">Replaces an earlier approval that was invalidated.</p>}
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-semibold tabular">{inr(a.max_amount)}</span>
                  <Status value={a.status} />
                  {!a.can_decide && a.status === "pending" && <Badge>view only</Badge>}
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

export function ApprovalDetail() {
  const { id = "" } = useParams();
  const { has } = useAuth();
  const nav = useNavigate();
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["approval", id], queryFn: () => api(`/api/approvals/${id}`), refetchInterval: 5000 });
  const [reason, setReason] = useState("Within budget and specification; lowest verified landed cost.");
  const [reviewed, setReviewed] = useState(false);
  const decide = useMutation({
    mutationFn: (decision: string) => api(`/api/approvals/${id}/decision`, {
      method: "POST", idempotent: true, json: { decision, reason, acknowledged_fingerprint: q.data.fingerprint },
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["approval", id] }); qc.invalidateQueries({ queryKey: ["approvals"] }); },
  });
  const alt = useMutation({
    mutationFn: (quote_id: string) => api(`/api/approvals/${id}/select-alternative`, { method: "POST", json: { quote_id, reason } }),
    onSuccess: (res: any) => nav(`/approvals/${res.approval_request_id}`),
  });
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorBox error={q.error} />;
  const a = q.data;
  const quote = a.quote;
  const changes = a.invalidation?.changes ?? a.previous?.invalidation?.changes ?? [];
  return (
    <div className="space-y-5">
      <PageHeader title="Approve purchase" subtitle={<>{a.request.title} · <Link className="text-brand" to={`/runs/${a.run_id}`}>run {a.run_id.slice(0, 8)}</Link></>}
        actions={<Status value={a.status} />} />
      <SyntheticBanner simulated={a.simulated_model} />
      {a.status === "invalidated" && (
        <div role="alert" className="rounded-md border border-bad/30 bg-bad-soft p-3 text-sm text-bad">
          <p className="font-medium">This approval is no longer valid ({a.invalidation?.reason?.replaceAll("_", " ")}).</p>
          {changes.length > 0 && <ul className="mt-1 list-disc pl-5">{changes.map((c: any) => <li key={c.field}>{c.field}: {c.approved} → {c.current}</li>)}</ul>}
          <p className="mt-1 text-ink">A fresh approval request is created for the new terms; check the inbox.</p>
        </div>
      )}
      {a.previous && a.status === "pending" && (
        <div role="status" className="rounded-md border border-warn/40 bg-warn-soft p-3 text-sm">
          <p className="font-medium text-warn">The offer changed after an earlier approval request; review the new terms.</p>
          {changes.length > 0 && <ul className="mt-1 list-disc pl-5">{changes.map((c: any) => <li key={c.field}>{c.field}: {c.approved} → <strong>{c.current}</strong></li>)}</ul>}
        </div>
      )}
      <div className="grid gap-5 lg:grid-cols-3">
        <Card title="Intended purchase" className="lg:col-span-2">
          <KV items={[
            ["Supplier", `${quote.supplier.name}${quote.supplier.synthetic ? " (synthetic)" : ""}`],
            ["Product", `${quote.sku} · ${quote.product_name}`],
            ["Specification", `${quote.spec.ram_gb} GB RAM · ${quote.spec.ssd_gb} GB ${quote.spec.storage_type ?? ""} · ${quote.spec.cpu ?? ""}`],
            ["Quantity", `${a.quantity} individual laptops`],
            ["Unit price", `${inr(quote.unit_price)} (${quote.price_basis})`],
            ["Subtotal", inr(quote.subtotal)], ["Discount", inr(quote.discount)],
            ["Tax", inr(quote.tax)], ["Shipping", inr(quote.shipping)],
            ["Landed total (max permitted)", <strong key="t">{inr(a.max_amount)}</strong>],
            ["Budget", inr(a.request.budget_total)],
            ["Delivery", `${quote.delivery_date} (${quote.delivery_confidence}); deadline ${a.delivery_deadline}`],
            ["Destination", a.address_ref], ["Supplier quote ref", quote.supplier_quote_ref],
            ["Policy version", a.binding.policy_version], ["Expires", when(a.expires_at)],
          ]} />
          <p className="mt-3 break-all text-xs text-muted">Purchase fingerprint: <span className="font-mono">{a.fingerprint}</span></p>
        </Card>
        <Card title="Policy checks">
          <FailedRules results={quote.policy_results} />
          <ul className="mt-2 space-y-0.5 text-xs">{quote.policy_results.filter((r: any) => r.passed).map((r: any) => (
            <li key={r.rule} className="text-good">✓ {r.rule}</li>))}</ul>
          <div className="mt-3 flex flex-wrap gap-2 text-xs">{quote.evidence_ids.map((e: string) => (
            <a key={e} className="text-brand hover:underline" href={`/api/evidence/${e}`} target="_blank" rel="noreferrer">evidence {e.slice(0, 6)}</a>))}</div>
        </Card>
      </div>
      {a.status === "pending" && (
        <Card title="Decision">
          {!has("approver") ? <p className="text-sm text-muted">Only users with the approver role can decide.</p> :
            !a.can_decide ? <p className="text-sm text-muted">You requested this purchase; a different approver must decide.</p> : (
              <div className="space-y-3">
                <Field id="reason" label="Reason (recorded in the audit trail)">
                  <Input id="reason" value={reason} onChange={(e) => setReason(e.target.value)} minLength={3} />
                </Field>
                <label className="flex items-start gap-2 text-sm">
                  <input type="checkbox" checked={reviewed} onChange={(e) => setReviewed(e.target.checked)} className="mt-1" />
                  I reviewed the supplier, product, quantity, landed total, delivery, destination and evidence above.
                </label>
                <div className="flex flex-wrap gap-2">
                  <Button disabled={!reviewed || decide.isPending} onClick={() => decide.mutate("approved")}>Approve exactly this purchase</Button>
                  <Button variant="secondary" disabled={!reviewed || decide.isPending} onClick={() => decide.mutate("rejected")}>Reject</Button>
                </div>
                <ErrorBox error={decide.error} />
                {a.alternatives.length > 0 && (
                  <div className="border-t border-line pt-3">
                    <p className="mb-2 text-sm font-medium">Or choose another eligible supplier</p>
                    <ul className="space-y-1 text-sm">{a.alternatives.map((x: any) => (
                      <li key={x.id} className="flex flex-wrap items-center justify-between gap-2">
                        <span>{x.supplier.name} · {x.sku} · {inr(x.total)} · delivery {x.delivery_date}</span>
                        <Button variant="ghost" onClick={() => alt.mutate(x.id)}>Select instead</Button>
                      </li>))}</ul>
                    <ErrorBox error={alt.error} />
                  </div>
                )}
              </div>
            )}
        </Card>
      )}
    </div>
  );
}
