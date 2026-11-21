"use client";
import { useState } from "react";
import { Alert, Badge, Button, Card, Field, inputClass, Spinner, StatusBadge, when } from "@/components/ui";
import { errorText, post } from "@/lib/api";
import { formatDecimal } from "@/lib/decimal";
import { useApi } from "@/lib/hooks";

type Exc = { id: string; category: string; severity: string; title: string; detail: string; status: string; observation_ids: string[];
  suggested_action: string | null; agent_explanation: string | null; resolution_note: string | null; resolved_by: string | null;
  first_seen_version: number; last_seen_version: number; document_level: boolean };

export function ExceptionQueue({ spreadId, onOpen, onChanged, locked }: { spreadId: string; onOpen: (id: string) => void; onChanged: () => void; locked: boolean }) {
  const { data, reload } = useApi<Exc[]>(`/spreads/${spreadId}/exceptions`);
  const [filter, setFilter] = useState<"open" | "all">("open");
  const [explaining, setExplaining] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [msg, setMsg] = useState<string>();
  if (!data) return <Spinner />;
  const items = data.filter((e) => filter === "all" || e.status === "open");
  async function accept(id: string) {
    try {
      await post(`/spreads/${spreadId}/actions`, { action: "accept_exception", exception_id: id, reason: text });
      setExplaining(null); setText(""); setMsg(undefined); reload(); onChanged();
    } catch (e) { setMsg(errorText(e)); }
  }
  const counts = data.reduce<Record<string, number>>((a, e) => { if (e.status === "open") a[e.severity] = (a[e.severity] ?? 0) + 1; return a; }, {});
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span>Open: <Badge tone="bad">{counts.critical ?? 0} critical</Badge> <Badge tone="warn">{counts.warning ?? 0} warning</Badge> <Badge tone="info">{counts.info ?? 0} info</Badge></span>
        <label className="ml-auto flex items-center gap-1">Show <select className="rounded border border-line bg-panel px-1" value={filter} onChange={(e) => setFilter(e.target.value as "open" | "all")}><option value="open">open</option><option value="all">all (incl. resolved)</option></select></label>
      </div>
      {msg && <Alert tone="bad">{msg}</Alert>}
      <ul className="space-y-2">
        {items.map((e) => (
          <li key={e.id} className={`rounded-md border p-3 ${e.severity === "critical" && e.status === "open" ? "border-bad/50" : "border-line"}`}>
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status={e.severity} /><span className="font-medium">{e.title}</span><Badge>{e.category.replace(/_/g, " ")}</Badge><StatusBadge status={e.status} />
              {e.document_level && <Badge tone="info">document-level</Badge>}
              <span className="ml-auto text-xs text-muted">versions {e.first_seen_version}–{e.last_seen_version}</span>
            </div>
            <p className="mt-1 text-sm">{e.detail}</p>
            {e.agent_explanation && <p className="mt-1 text-sm text-info">Reconciliation agent (possible causes, not conclusions): {e.agent_explanation}</p>}
            {e.suggested_action && <p className="mt-1 text-xs text-muted">{e.suggested_action}</p>}
            {e.resolution_note && <p className="mt-1 text-xs">Resolution: {e.resolution_note}{e.resolved_by ? ` — ${e.resolved_by}` : ""}</p>}
            <div className="mt-2 flex flex-wrap gap-2">
              {e.observation_ids.slice(0, 6).map((o, i) => <Button key={o} variant="secondary" onClick={() => onOpen(o)}>Inspect source {i + 1}</Button>)}
              {e.status === "open" && !locked && <Button variant="secondary" onClick={() => { setExplaining(e.id); setText(""); }}>Accept with explanation</Button>}
            </div>
            {explaining === e.id && (
              <div className="mt-2 space-y-2">
                <Field label="Explanation (why this exception is acceptable)"><textarea className={inputClass} rows={2} value={text} onChange={(x) => setText(x.target.value)} /></Field>
                <Button onClick={() => accept(e.id)} disabled={text.trim().length < 5}>Accept exception</Button>
              </div>
            )}
          </li>
        ))}
        {items.length === 0 && <li className="text-sm text-muted">No {filter === "open" ? "open " : ""}exceptions.</li>}
      </ul>
    </div>
  );
}

type Val = { id: string; rule_id: string; rule_version: string; title: string; statement_type: string | null; period_end: string | null; inputs: string[];
  expression: string; expected: string | null; observed: string | null; difference: string | null; tolerance: string | null; tolerance_basis: string | null;
  severity: string; status: string; explanation: string };

export function Validations({ spreadId, version, onOpen }: { spreadId: string; version: number; onOpen: (id: string) => void }) {
  const { data } = useApi<{ version: number; results: Val[] }>(`/spreads/${spreadId}/validations?version=${version}`);
  if (!data) return <Spinner />;
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[1000px] text-sm">
        <thead className="text-left text-xs text-muted"><tr className="border-b border-line"><th className="py-2">Rule</th><th>Period</th><th>Status</th><th>Expression</th><th className="text-right">Expected</th><th className="text-right">Observed</th><th className="text-right">Exact residual</th><th className="text-right">Rounding tolerance</th><th>Inputs</th></tr></thead>
        <tbody>
          {data.results.map((v) => (
            <tr key={v.id} className="border-b border-line/60 align-top">
              <td className="py-1.5"><span className="font-mono text-xs">{v.rule_id} v{v.rule_version}</span><div>{v.title}</div></td>
              <td>{v.period_end}</td>
              <td><StatusBadge status={v.status} /> {v.status === "fail" && <StatusBadge status={v.severity} />}</td>
              <td className="max-w-72 text-xs"><code>{v.expression}</code><div className="text-muted">{v.explanation}</div></td>
              <td className="num text-right">{formatDecimal(v.expected, 2)}</td>
              <td className="num text-right">{formatDecimal(v.observed, 2)}</td>
              <td className={`num text-right ${v.status === "fail" ? "font-semibold text-bad" : ""}`}>{formatDecimal(v.difference, 2)}</td>
              <td className="num text-right" title={v.tolerance_basis ?? ""}>{formatDecimal(v.tolerance, 2)}</td>
              <td className="text-xs">{v.inputs.slice(0, 4).map((i, n) => <button key={i} className="mr-1 text-brand underline" onClick={() => onOpen(i)}>#{n + 1}</button>)}{v.inputs.length > 4 ? `+${v.inputs.length - 4}` : ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-muted">Values in base units ({"exact"}). Tolerance comes only from the source precision of the rounded inputs; it is separate from analyst materiality and never hides a failure. Insufficient data is never turned into a pass or fail.</p>
    </div>
  );
}

type Adj = { id?: string; action: string; field: string | null; before: unknown; after: unknown; reason: string; user: string; at: string; version_before: number; version_after: number | null; observation_id: string | null };

export function AdjustmentHistory({ items, onOpen }: { items: Adj[]; onOpen?: (id: string) => void }) {
  if (items.length === 0) return <p className="text-sm text-muted">No analyst actions yet.</p>;
  return (
    <table className="w-full text-sm">
      <thead className="text-left text-xs text-muted"><tr className="border-b border-line"><th className="py-2">When</th><th>User</th><th>Action</th><th>Before</th><th>After</th><th>Reason</th><th>Version</th></tr></thead>
      <tbody>{items.map((a, i) => (
        <tr key={a.id ?? i} className="border-b border-line/60 align-top">
          <td className="py-1.5 text-xs">{when(a.at)}</td><td>{a.user}</td>
          <td>{a.action.replace(/_/g, " ")}{a.observation_id && onOpen && <button className="ml-1 text-xs text-brand underline" onClick={() => onOpen(a.observation_id!)}>source</button>}</td>
          <td className="font-mono text-xs break-all">{JSON.stringify(a.before)}</td><td className="font-mono text-xs break-all">{JSON.stringify(a.after)}</td>
          <td>{a.reason}</td><td className="text-xs">v{a.version_before} → {a.version_after ? `v${a.version_after}` : "—"}</td>
        </tr>))}
      </tbody>
    </table>
  );
}

type Detail = { id: string; version: number; review_status: string; role: string; blocking: string[];
  versions: { version: number; reason: string; hash: string; by: string | null; at: string }[];
  decisions: { id: string; decision: string; user: string; role: string; version: number; comment: string | null; stale: boolean; stale_reason: string | null; at: string; snapshot_id: string | null }[] };
type Export = { id: string; version: number; status: string; hash: string; render_status: string; error: string | null; created_at: string; by: string; stale: boolean };

export function ReviewPanel({ detail, onChanged }: { detail: Detail; onChanged: () => void }) {
  const { data: exports, reload } = useApi<Export[]>(`/spreads/${detail.id}/exports`);
  const [comment, setComment] = useState("");
  const [msg, setMsg] = useState<{ tone: "ok" | "bad"; text: string }>();
  const [busy, setBusy] = useState(false);
  const isReviewer = detail.role === "reviewer" || detail.role === "admin";
  async function act(path: string, body: unknown, ok: string) {
    setBusy(true); setMsg(undefined);
    try { await post(path, body); setMsg({ tone: "ok", text: ok }); setComment(""); onChanged(); reload(); }
    catch (e) { setMsg({ tone: "bad", text: errorText(e) }); }
    finally { setBusy(false); }
  }
  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Card title="Review and approval">
        <div className="space-y-3 text-sm">
          <div>Current version <strong>v{detail.version}</strong> · status <StatusBadge status={detail.review_status} /></div>
          {detail.blocking.length > 0 && <Alert tone="bad"><strong>Approval blocked:</strong><ul className="list-disc pl-5">{detail.blocking.map((b) => <li key={b}>{b}</li>)}</ul></Alert>}
          <Field label="Comment"><textarea className={inputClass} rows={2} value={comment} onChange={(e) => setComment(e.target.value)} /></Field>
          <div className="flex flex-wrap gap-2">
            {(detail.review_status === "in_preparation" || detail.review_status === "reopened") && (
              <Button disabled={busy} onClick={() => act(`/spreads/${detail.id}/submit`, { comment }, "Submitted for review.")}>Submit v{detail.version} for review (preparer)</Button>
            )}
            {isReviewer && detail.review_status === "submitted_for_review" && (
              <Button disabled={busy || detail.blocking.length > 0} onClick={() => act(`/spreads/${detail.id}/approve`, { comment, version: detail.version }, `Approved v${detail.version}. An immutable snapshot and exports were created.`)}>Approve v{detail.version} (reviewer sign-off)</Button>
            )}
            {isReviewer && (detail.review_status === "approved" || detail.review_status === "submitted_for_review") && (
              <Button variant="secondary" disabled={busy} onClick={() => act(`/spreads/${detail.id}/reopen`, { comment }, "Reopened.")}>Reopen</Button>
            )}
          </div>
          {!isReviewer && detail.review_status === "submitted_for_review" && <p className="text-xs text-muted">Waiting for a reviewer. The reviewer must be a different person from the preparer.</p>}
          {msg && <Alert tone={msg.tone}>{msg.text}</Alert>}
          <div>
            <div className="mb-1 font-medium">Decisions</div>
            <ul className="space-y-1 text-xs">{detail.decisions.map((d) => (
              <li key={d.id} className={d.stale ? "text-muted line-through" : ""}>{when(d.at)} — {d.decision.replace(/_/g, " ")} v{d.version} by {d.user} ({d.role}){d.comment ? `: ${d.comment}` : ""}{d.stale && <span className="no-underline"> · stale: {d.stale_reason}</span>}</li>
            ))}{detail.decisions.length === 0 && <li className="text-muted">None.</li>}</ul>
          </div>
        </div>
      </Card>
      <Card title="Exports (Excel workbook + PDF review pack)" actions={<Button variant="secondary" disabled={busy} onClick={() => act(`/spreads/${detail.id}/exports`, undefined, "Draft export created (labelled UNREVIEWED; includes unresolved exceptions).")}>Create draft export</Button>}>
        {!exports ? <Spinner /> : (
          <ul className="space-y-2 text-sm">
            {exports.map((e) => (
              <li key={e.id} className="rounded border border-line p-2">
                <div className="flex flex-wrap items-center gap-2"><Badge tone={e.status === "approved" ? "ok" : "warn"}>{e.status === "approved" ? "APPROVED" : "DRAFT — unreviewed"}</Badge> v{e.version}
                  {e.stale && <Badge tone="bad">stale: figures changed since</Badge>}<StatusBadge status={e.render_status} /><span className="ml-auto text-xs text-muted">{when(e.created_at)} · {e.by}</span></div>
                <div className="mt-1 font-mono text-[11px] text-muted">snapshot {e.hash.slice(0, 24)}…</div>
                {e.render_status === "ok" ? (
                  <div className="mt-1 flex gap-3"><a className="text-brand underline" href={`/api/engine/exports/${e.id}/download/xlsx`}>Download Excel</a><a className="text-brand underline" href={`/api/engine/exports/${e.id}/download/pdf`}>Download PDF</a></div>
                ) : <Alert tone="bad">Rendering failed: {e.error}</Alert>}
              </li>
            ))}
            {exports.length === 0 && <li className="text-muted">No exports yet.</li>}
          </ul>
        )}
      </Card>
      <Card title="Version history" className="lg:col-span-2">
        <ul className="space-y-1 text-xs">{detail.versions.map((v) => <li key={v.version}><strong>v{v.version}</strong> {when(v.at)} — {v.reason} <span className="font-mono text-muted">{v.hash}</span>{v.by ? ` · ${v.by}` : ""}</li>)}</ul>
      </Card>
    </div>
  );
}
