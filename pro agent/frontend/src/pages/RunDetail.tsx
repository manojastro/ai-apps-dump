import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, inr, seconds, when } from "../api";
import { useAuth } from "../auth";
import { Badge, Button, Card, ErrorBox, KV, Loading, PageHeader, Status, SyntheticBanner } from "../ui";

interface RunEvent { id: number; type: string; data: any; at: string }

// Persisted events streamed over SSE (resumes with Last-Event-ID); falls back to polling.
function useRunEvents(runId: string) {
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [transport, setTransport] = useState<"sse" | "polling" | "connecting">("connecting");
  const last = useRef(0);
  useEffect(() => {
    let es: EventSource | null = null;
    let timer: number | undefined;
    let stopped = false;
    const add = (items: RunEvent[]) => {
      const fresh = items.filter((e) => e.id > last.current);
      if (!fresh.length) return;
      last.current = fresh[fresh.length - 1].id;
      setEvents((prev) => [...prev, ...fresh]);
    };
    const poll = async () => {
      if (stopped) return;
      try { add((await api(`/api/runs/${runId}/events?after=${last.current}`)).items); } catch { /* retry next tick */ }
      timer = window.setTimeout(poll, 2000);
    };
    if ("EventSource" in window) {
      es = new EventSource(`/api/runs/${runId}/events`);
      es.onopen = () => setTransport("sse");
      es.onmessage = (m) => add([JSON.parse(m.data)]);
      const handler = (m: MessageEvent) => add([JSON.parse(m.data)]);
      ["step", "phase", "quote", "model_decision", "recovery", "approval_requested", "approval_invalidated",
        "approval_approved", "approval_rejected", "verifier_rejected_recommendation", "policy_checked", "revalidated",
        "receipt_verified", "receipt_mismatch", "reconciled", "run_finished", "human_handoff", "budget_exhausted",
        "cancel_requested", "pause_requested", "run_queued", "resumed_from_checkpoint", "worker_error",
        "submission_skipped_reconcile", "absence_established", "injection_suspected", "proposal_validated",
        "submission_blocked_terms_changed"].forEach((t) => es!.addEventListener(t, handler as EventListener));
      es.onerror = () => {
        // EventSource reconnects by itself with Last-Event-ID; if it keeps failing, poll instead.
        if (es && es.readyState === EventSource.CLOSED) { setTransport("polling"); poll(); }
      };
    } else {
      setTransport("polling");
      poll();
    }
    return () => { stopped = true; es?.close(); if (timer) clearTimeout(timer); };
  }, [runId]);
  return { events, transport };
}

function describe(e: RunEvent): string {
  const d = e.data ?? {};
  switch (e.type) {
    case "step": return `${d.supplier ?? ""} · ${d.tool}${d.error_code ? ` → ${d.error_code}` : ""}${d.message ? ` (${d.message})` : ""}`;
    case "phase": return `Phase: ${String(d.phase).replaceAll("_", " ")}`;
    case "quote": return `Quote ${d.supplier} ${d.sku}: ${inr(d.total)}${d.arithmetic_ok ? "" : " (arithmetic not verified)"}`;
    case "model_decision": return `${d.simulated ? "Simulated" : "Model"} decision · ${d.what}${d.reason ? `: ${d.reason}` : d.note ? `: ${d.note}` : ""}`;
    case "verifier_rejected_recommendation":
      return `Verifier rejected the recommended quote: ${(d.failed_rules ?? []).map((r: any) => `${r.rule} (expected ${r.expected}, observed ${r.observed})`).join("; ")}`;
    case "approval_invalidated":
      return `Approval invalidated (${d.reason}): ${(d.changes ?? []).map((c: any) => `${c.field} ${c.approved} → ${c.current}`).join(", ") || "no field changes"}`;
    case "recovery": return `Recovery: ${d.kind}`;
    case "human_handoff": return `Needs a person: ${d.detail ?? d.reason}`;
    case "run_finished": return `Finished: ${d.outcome}`;
    default: return e.type.replaceAll("_", " ");
  }
}

const tone = (e: RunEvent) => e.type === "verifier_rejected_recommendation" || e.type === "approval_invalidated" || e.data?.status === "blocked"
  ? "text-bad" : e.type === "receipt_verified" || e.type === "run_finished" ? "text-good" : e.data?.status === "error" ? "text-warn" : "";

export default function RunDetail() {
  const { id = "" } = useParams();
  const { has } = useAuth();
  const qc = useQueryClient();
  const run = useQuery({ queryKey: ["run", id], queryFn: () => api(`/api/runs/${id}`), refetchInterval: 3000 });
  const evidence = useQuery({ queryKey: ["evidence", id], queryFn: () => api(`/api/runs/${id}/evidence`), refetchInterval: 6000 });
  const { events, transport } = useRunEvents(id);
  const action = useMutation({
    mutationFn: ({ path, json }: { path: string; json?: unknown }) => api(`/api/runs/${id}/${path}`, { method: "POST", json: json ?? {} }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["run", id] }),
  });

  if (run.isLoading) return <Loading />;
  if (run.error) return <ErrorBox error={run.error} />;
  const r = run.data;
  const active = ["queued", "running", "awaiting_approval", "submitting", "reconciling", "paused_for_human"].includes(r.status);
  const shots = (evidence.data?.items ?? []).filter((e: any) => e.kind === "screenshot");
  const blocked = events.filter((e) => e.type === "step" && e.data.status === "blocked").length;

  return (
    <div className="space-y-5">
      <PageHeader title={r.request.title} subtitle={<>Run {r.id.slice(0, 8)} · created {when(r.created_at)}</>}
        actions={<>
          <Link to={`/runs/${id}/comparison`} className="rounded-md border border-line bg-white px-3.5 py-2 text-sm">Quote comparison</Link>
          {r.approval_request_id && <Link to={`/approvals/${r.approval_request_id}`} className="rounded-md border border-line bg-white px-3.5 py-2 text-sm">Approval</Link>}
          {r.order_intent_id && <Link to={`/orders/${r.order_intent_id}`} className="rounded-md border border-line bg-white px-3.5 py-2 text-sm">Order</Link>}
        </>} />
      <SyntheticBanner simulated={r.simulated_model} />
      <div className="grid gap-5 lg:grid-cols-3">
        <Card title="Status" className="lg:col-span-2" actions={<span className="text-xs text-muted">live: {transport}</span>}>
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <Status value={r.status} /> <span className="text-sm text-muted">phase: {r.phase.replaceAll("_", " ")}</span>
            {r.current_supplier && <Badge kind="info">supplier: {r.current_supplier}</Badge>}
            {r.outcome && <Status value={r.outcome} />}
            {blocked > 0 && <Badge kind="bad">{blocked} blocked action{blocked > 1 ? "s" : ""}</Badge>}
          </div>
          <KV items={[
            ["Browser actions", `${r.action_count} / ${r.budgets.max_browser_actions}`],
            ["Active browsing", `${seconds(r.active_ms)} / ${r.budgets.active_run_timeout_seconds}s`],
            ["Human waiting (not counted)", seconds(r.waiting_ms)],
            ["Retries / recoveries", r.retries],
            ["Model cost", `$${Number(r.model_cost).toFixed(4)} / $${r.budgets.max_run_cost}`],
            ["Mode", r.simulated_model ? "fixture (simulated model)" : r.model_name],
          ]} />
          {r.handoff && (
            <div className="mt-4 rounded-md border border-warn/40 bg-warn-soft p-3 text-sm" role="status">
              <p className="font-medium text-warn">Human handoff: {String(r.handoff.reason).replaceAll("_", " ")}</p>
              <p className="mt-1">{r.handoff.detail}</p>
              {(has("requester") || has("admin")) && r.status === "paused_for_human" && (
                <div className="mt-2 flex flex-wrap gap-2">
                  <Button variant="secondary" onClick={() => action.mutate({ path: "resume", json: { action: "retry" } })}>Retry after resolving</Button>
                  <Button variant="secondary" onClick={() => action.mutate({ path: "resume", json: { action: "skip" } })}>Skip and continue</Button>
                </div>
              )}
            </div>
          )}
          {active && (
            <div className="mt-4 flex flex-wrap gap-2">
              {["queued", "running"].includes(r.status) && <Button variant="secondary" onClick={() => action.mutate({ path: "pause" })}>Pause</Button>}
              <Button variant="danger" onClick={() => { if (confirm("Cancel this run? An order already submitted is not cancelled by this.")) action.mutate({ path: "cancel" }); }}>Cancel run</Button>
            </div>
          )}
          <p className="mt-2 text-xs text-muted">Pause takes effect before the next browser action. Cancelling during submission becomes "cancellation requested" until the supplier outcome is known; closing the browser never cancels an order.</p>
          <ErrorBox error={action.error} />
        </Card>
        <Card title="Request">
          <KV items={[
            ["Product", r.request.canonical_product_id], ["Quantity", r.request.quantity],
            ["Min RAM / SSD", `${r.request.spec_requirements.min_ram_gb} / ${r.request.spec_requirements.min_ssd_gb} GB`],
            ["Budget (landed)", inr(r.request.budget_total)], ["Deliver by", r.request.delivery_deadline],
            ["Destination", r.request.address_ref],
          ]} />
        </Card>
      </div>
      <Card title={`Activity (${events.length})`}>
        <ol className="max-h-[28rem] space-y-1 overflow-y-auto text-sm" aria-live="polite">
          {events.map((e) => (
            <li key={e.id} className={`flex gap-3 border-b border-line/60 py-1 ${tone(e)}`}>
              <span className="w-20 shrink-0 text-xs text-muted tabular">{new Date(e.at).toLocaleTimeString()}</span>
              <span className="min-w-0 break-words">{describe(e)}</span>
            </li>
          ))}
          {events.length === 0 && <li className="text-muted">Waiting for the worker…</li>}
        </ol>
      </Card>
      <Card title={`Redacted browser evidence (${shots.length})`}>
        {shots.length === 0 ? <p className="text-sm text-muted">Screenshots appear at key observations.</p> : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {shots.slice(-9).map((s: any) => (
              <a key={s.id} href={`/api/evidence/${s.id}`} target="_blank" rel="noreferrer" className="block rounded border border-line bg-canvas p-1">
                <img src={`/api/evidence/${s.id}`} alt={s.label} loading="lazy" className="h-40 w-full object-cover object-top" />
                <span className="block truncate px-1 pt-1 text-xs text-muted">{s.label}</span>
              </a>
            ))}
          </div>
        )}
        <p className="mt-2 text-xs text-muted">Password fields and address lines are masked. Screenshots can still contain business data and follow the retention policy.</p>
      </Card>
    </div>
  );
}
