"use client";
import { useState } from "react";
import { PdfSource, SheetSource } from "@/components/source-viewer";
import { Alert, Badge, Button, Drawer, Field, inputClass, Kv, Spinner, StatusBadge, when } from "@/components/ui";
import { errorText, post } from "@/lib/api";
import { formatDecimal } from "@/lib/decimal";
import { useApi } from "@/lib/hooks";

type Evidence = {
  observation: { id: string; label: string; code: string | null; period_end: string; duration: string; statement_type: string; scope: string;
    framework: string; raw_text: string; value_state: string; parsed_value: string | null; source_decimals: number | null;
    original_currency: string; original_scale: string; normalized_value: string | null; current_value: string | null; current_state: string;
    origin: string; version_kind: string; preferred: boolean; review_status: string; extraction_method: string;
    confidence: Record<string, unknown>; transformations: Record<string, unknown>[]; source_sha256: string; unit_type: string };
  source: { document_version_id: string; filename: string; kind: string; page: number | null; bbox: number[] | null; row_bbox: number[] | null;
    sheet: string | null; cell_ref: string | null; statement_title: string; parse_notes: string[]; ocr_confidence: number | null };
  row: { id: string; section_path: string[]; note_ref: string | null; is_total: boolean; flags: string[] } | null;
  mapping: { proposed_code: string | null; decided_code: string | null; status: string; confidence: string; rationale: string;
    alternatives: { code: string; score: string; reason: string }[] } | null;
  note: { ref: string; title: string; text: string; page: number | null } | null;
  adjustments: { action: string; before: Record<string, unknown>; after: Record<string, unknown>; reason: string; user: string; at: string; version_after: number | null }[];
  other_sources: { id: string; value: string | null; version_kind: string; preferred: boolean; raw_text: string }[];
};

type Tax = { code: string; label: string; statement: string }[];

export function EvidenceDrawer({ spreadId, obsId, onClose, onChanged, taxonomy, locked }: {
  spreadId: string; obsId: string | null; onClose: () => void; onChanged: () => void; taxonomy: Tax; locked: boolean;
}) {
  const { data, error, reload } = useApi<Evidence>(obsId ? `/observations/${obsId}` : null);
  const [action, setAction] = useState<string>("correct_value");
  const [value, setValue] = useState("");
  const [code, setCode] = useState("");
  const [reason, setReason] = useState("");
  const [msg, setMsg] = useState<{ tone: "ok" | "bad"; text: string }>();
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!data) return;
    setBusy(true);
    setMsg(undefined);
    try {
      const body: Record<string, unknown> = { action, reason, observation_id: data.observation.id, row_id: data.row?.id };
      if (action === "correct_value") body.value = value;
      if (action === "change_mapping") body.code = code || null;
      const r = await post<{ version: number; run_id?: string }>(`/spreads/${spreadId}/actions`, body);
      setMsg({ tone: "ok", text: r.run_id ? `Targeted re-extraction started (run ${r.run_id.slice(0, 8)}). Results arrive as review items; figures are never overwritten.` : `Saved. Recalculated as spread version ${r.version}; stale review decisions were invalidated.` });
      setReason("");
      setValue("");
      reload();
      onChanged();
    } catch (x) {
      setMsg({ tone: "bad", text: errorText(x) });
    } finally {
      setBusy(false);
    }
  }

  const o = data?.observation;
  return (
    <Drawer open={!!obsId} onClose={onClose} wide title={o ? `${o.label} · ${o.period_end}` : "Source evidence"}>
      {error && <Alert tone="bad">{error}</Alert>}
      {!data ? <Spinner /> : (
        <div className="grid gap-5 lg:grid-cols-[1.25fr_1fr]">
          <div className="space-y-3">
            <div className="text-sm font-medium">Source: {data.source.filename} — {data.source.statement_title}</div>
            {data.source.kind === "pdf" && data.source.page ? (
              <PdfSource dv={data.source.document_version_id} page={data.source.page} bbox={data.source.bbox} rowBbox={data.source.row_bbox} />
            ) : data.source.sheet ? (
              <SheetSource dv={data.source.document_version_id} sheet={data.source.sheet} cell={data.source.cell_ref} />
            ) : <Alert tone="warn">No source location (analyst adjustment).</Alert>}
            {data.note && (
              <details className="rounded border border-line p-2 text-sm">
                <summary className="cursor-pointer font-medium">Note {data.note.ref}: {data.note.title}</summary>
                <p className="mt-2 whitespace-pre-wrap text-xs">{data.note.text}</p>
              </details>
            )}
          </div>
          <div className="space-y-4">
            <Kv items={[
              ["Raw source text", <span key="r" className="num font-semibold">{o!.raw_text || "(blank)"}</span>],
              ["Parse state", <StatusBadge key="p" status={o!.value_state} />],
              ["Parsed value", <span key="pv" className="num">{o!.parsed_value ?? "—"} {o!.unit_type === "monetary" ? `${o!.original_currency} ${o!.original_scale}` : o!.original_scale}</span>],
              ["Source precision", `${o!.source_decimals ?? "?"} decimal places`],
              ["Normalized (base units)", <span key="n" className="num">{o!.normalized_value ?? "—"}</span>],
              ["Current value", <span key="c" className="num">{o!.current_value ?? "—"} {o!.review_status === "corrected" && <Badge tone="warn">corrected</Badge>}</span>],
              ["Canonical item", o!.code ?? <Badge tone="warn">unmapped</Badge>],
              ["Period / duration", `${o!.period_end} · ${o!.duration}`],
              ["Scope / framework", `${o!.scope} · ${o!.framework}`],
              ["Version", <span key="v">{o!.version_kind} {o!.preferred ? <Badge tone="ok">preferred</Badge> : <Badge>not preferred</Badge>}</span>],
              ["Method", <span key="m">{o!.extraction_method}{data.source.ocr_confidence != null ? ` · OCR confidence ${data.source.ocr_confidence.toFixed(2)}` : ""}</span>],
              ["Section path", data.row?.section_path.join(" › ") || "—"],
              ["Location", data.source.sheet ? `${data.source.sheet}!${data.source.cell_ref}` : `page ${data.source.page}`],
              ["Source hash", <span key="h" className="font-mono text-[11px]">{o!.source_sha256.slice(0, 20)}…</span>],
            ]} />
            {data.mapping && (
              <div className="rounded border border-line p-3 text-sm">
                <div className="mb-1 font-medium">Mapping proposal <StatusBadge status={data.mapping.status} /> <Badge tone={data.mapping.confidence === "high" ? "ok" : data.mapping.confidence === "medium" ? "info" : "warn"}>{data.mapping.confidence} confidence</Badge></div>
                <p className="text-xs text-muted">{data.mapping.rationale}</p>
                {data.mapping.alternatives.length > 0 && <p className="mt-1 text-xs">Alternatives: {data.mapping.alternatives.map((a) => `${a.code} (${a.score})`).join(", ")}</p>}
              </div>
            )}
            {data.other_sources.length > 0 && (
              <div className="text-sm"><div className="font-medium">Same item and period in other documents</div>
                <ul className="text-xs">{data.other_sources.map((x) => <li key={x.id} className="num">{x.raw_text} → {x.value} ({x.version_kind}{x.preferred ? ", preferred" : ""})</li>)}</ul></div>
            )}
            <details className="text-sm"><summary className="cursor-pointer font-medium">Transformation history ({o!.transformations.length})</summary>
              <ol className="mt-1 list-decimal space-y-1 pl-5 text-xs">{o!.transformations.map((t, i) => <li key={i} className="font-mono break-all">{JSON.stringify(t)}</li>)}</ol>
            </details>

            <form onSubmit={submit} className="space-y-2 rounded-md border border-line p-3" aria-label="Review action">
              <div className="text-sm font-medium">Review action</div>
              {locked && <Alert tone="warn">This version is approved. A reviewer must reopen it before figures can change.</Alert>}
              <Field label="Action">
                <select className={inputClass} value={action} onChange={(e) => setAction(e.target.value)}>
                  <option value="correct_value">Correct extracted value</option>
                  <option value="accept_mapping">Accept mapping</option>
                  <option value="change_mapping">Change mapping</option>
                  <option value="reject_mapping">Reject mapping (leave unmapped)</option>
                  <option value="mark_unresolved">Mark unresolved</option>
                  <option value="request_reextraction">Request targeted re-extraction</option>
                </select>
              </Field>
              {action === "correct_value" && (
                <Field label={`Value as shown in source (${o!.unit_type === "monetary" ? `${o!.original_currency} ${o!.original_scale}` : o!.unit_type})`} hint="Parentheses or a leading minus for negatives. The original extraction stays visible.">
                  <input className={inputClass + " num"} value={value} onChange={(e) => setValue(e.target.value)} placeholder={o!.raw_text} required />
                </Field>
              )}
              {action === "change_mapping" && (
                <Field label="Canonical item">
                  <select className={inputClass} value={code} onChange={(e) => setCode(e.target.value)} required>
                    <option value="">Choose…</option>
                    {taxonomy.filter((t) => t.statement === o!.statement_type).map((t) => <option key={t.code} value={t.code}>{t.label} ({t.code})</option>)}
                  </select>
                </Field>
              )}
              <Field label="Reason (recorded with user, time, before and after)">
                <textarea className={inputClass} rows={2} value={reason} onChange={(e) => setReason(e.target.value)} required minLength={3} />
              </Field>
              <Button type="submit" disabled={busy || (locked && action !== "request_reextraction")}>{busy ? "Saving…" : "Apply"}</Button>
              {msg && <Alert tone={msg.tone}>{msg.text}</Alert>}
            </form>
            {data.adjustments.length > 0 && (
              <div className="text-sm"><div className="font-medium">History</div>
                <ul className="space-y-1 text-xs">{data.adjustments.map((a, i) => (
                  <li key={i}><strong>{a.action}</strong> by {a.user} {when(a.at)} — {a.reason}. Before {JSON.stringify(a.before)} → after {JSON.stringify(a.after)}{a.version_after ? ` (v${a.version_after})` : ""}</li>
                ))}</ul></div>
            )}
          </div>
        </div>
      )}
    </Drawer>
  );
}

export function fmtCell(display: string | null, unit: string): string {
  if (display === null) return "";
  return unit === "eps" ? formatDecimal(display, 2) : formatDecimal(display, 2);
}
