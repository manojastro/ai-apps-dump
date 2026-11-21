"use client";
import { Badge } from "@/components/ui";
import { formatDecimal, formatRatio } from "@/lib/decimal";

export type GridCell = { observation_id: string; display: string | null; raw_text: string; state: string; review_status: string; preferred: boolean;
  version_kind: string; duration: string; confidence: { mapping?: string; ocr?: number | null }; validation: { rule: string; status: string }[];
  corrected: boolean; original_display: string | null };
export type GridRow = { row_id: string; original_label: string; canonical_code: string | null; canonical_label: string | null; order: number;
  is_total: boolean; level: number; unit_type: string; origin: string; document: string | null; statement_title: string | null; scale: string;
  currency: string; mapping: { status: string; confidence: string; rationale: string } | null; cells: Record<string, GridCell> };
export type Grid = { spread_id: string; version: number; currency: string; display_scale: string; scope: string; periods: string[];
  statements: Record<string, GridRow[]>; taxonomy: { code: string; label: string; statement: string }[];
  metrics: { id: string; metric: string; title: string; period_end: string; value: string | null; unit: string; status: string; formula: string;
    explanation: string; limitations: string[]; inputs: string[] }[] };

const STATE_LABEL: Record<string, string> = { unreadable: "unreadable", dash_ambiguous: "dash?", missing: "missing", not_applicable: "n/a" };

function cellTone(c: GridCell): string {
  if (c.state === "unreadable" || c.state === "dash_ambiguous") return "bg-bad-bg text-bad";
  if (c.validation.some((v) => v.status === "fail")) return "bg-bad-bg";
  if (c.corrected) return "bg-warn-bg";
  if (c.confidence?.ocr != null && c.confidence.ocr < 0.8) return "bg-warn-bg/60";
  return "";
}

// Standardised view: one line per canonical item, using the preferred value for each period
// (restated > latest document). Per-document rows remain available via the toggle.
function mergeByCode(rows: GridRow[]): GridRow[] {
  const out: GridRow[] = [];
  const byCode = new Map<string, GridRow>();
  for (const r of rows) {
    if (!r.canonical_code || r.origin === "adjusted") { out.push(r); continue; }
    const m = byCode.get(r.canonical_code);
    if (!m) {
      const copy = { ...r, cells: {} as Record<string, GridCell>, document: r.document };
      for (const [p, c] of Object.entries(r.cells)) if (c.preferred) copy.cells[p] = c;
      byCode.set(r.canonical_code, copy);
      out.push(copy);
      continue;
    }
    if (!m.original_label.split(" / ").includes(r.original_label)) m.original_label += ` / ${r.original_label}`;
    if (r.document && m.document && !m.document.includes(r.document)) m.document += `, ${r.document}`;
    for (const [p, c] of Object.entries(r.cells)) if (c.preferred) m.cells[p] = c;
  }
  return out;
}

export function StatementGrid({ grid, statement, onOpen, showAll, merged = true }: { grid: Grid; statement: string; onOpen: (obsId: string) => void; showAll: boolean; merged?: boolean }) {
  const all = grid.statements[statement] ?? [];
  const rows = merged ? mergeByCode(all) : all;
  const visible = rows.filter((r) => showAll || r.canonical_code !== null || Object.values(r.cells).some((c) => c.state !== "value" && c.state !== "zero"));
  if (rows.length === 0) return <p className="py-6 text-sm text-muted">No {statement.replace(/_/g, " ")} was provided for this entity and scope. Dependent checks report insufficient data.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[900px] border-collapse text-sm" aria-label={`${statement.replace(/_/g, " ")} grid`}>
        <caption className="sr-only">Standardised figures in {grid.currency} {grid.display_scale}. Click a figure to open its exact source.</caption>
        <thead className="sticky top-0 bg-panel text-left text-xs text-muted">
          <tr className="border-b border-line">
            <th scope="col" className="py-2 pr-2">Standardised line</th>
            <th scope="col" className="pr-2">Original label (source)</th>
            {grid.periods.map((p) => <th scope="col" key={p} className="pr-3 text-right">{p}<div className="font-normal">{grid.currency} {grid.display_scale}</div></th>)}
            <th scope="col" className="pr-2">Mapping</th>
            <th scope="col">Checks</th>
          </tr>
        </thead>
        <tbody>
          {visible.map((r) => {
            const checks = Object.values(r.cells).flatMap((c) => c.validation);
            const failed = checks.filter((c) => c.status === "fail").length;
            return (
              <tr key={r.row_id + r.document} className={`border-b border-line/60 ${r.is_total ? "font-semibold" : ""} ${!r.canonical_code ? "text-muted" : ""}`}>
                <td className="py-1.5 pr-2">{r.canonical_label ?? <Badge tone="warn">unmapped</Badge>}{r.origin === "adjusted" && <Badge tone="warn">adjustment</Badge>}</td>
                <td className="pr-2" style={{ paddingLeft: r.level * 8 }} title={`${r.document ?? ""} — ${r.statement_title ?? ""}`}>{r.original_label}
                  <div className="text-[10px] text-muted">{r.document}</div></td>
                {grid.periods.map((p) => {
                  const c = r.cells[p];
                  if (!c) return <td key={p} className="pr-3 text-right text-muted">·</td>;
                  return (
                    <td key={p} className="pr-1 text-right">
                      <button onClick={() => onOpen(c.observation_id)}
                        aria-label={`${r.original_label} ${p}: ${c.display ?? STATE_LABEL[c.state] ?? c.state}. Open source evidence.`}
                        className={`num w-full rounded px-1.5 py-0.5 text-right hover:outline hover:outline-1 hover:outline-brand ${cellTone(c)} ${!c.preferred ? "opacity-60 line-through decoration-muted/40" : ""}`}
                        title={`Raw: ${c.raw_text}${c.corrected ? ` · corrected (was ${c.original_display})` : ""}${!c.preferred ? " · not preferred (another document's value is used)" : ""}${c.version_kind === "restated" ? " · restated" : ""}`}>
                        {c.display !== null ? (r.unit_type === "eps" ? formatDecimal(c.display, 2) : formatDecimal(c.display, 2)) : <span className="text-xs">{STATE_LABEL[c.state] ?? c.state}</span>}
                        {c.version_kind === "restated" && <sup className="ml-0.5 text-info">R</sup>}
                        {c.corrected && <sup className="ml-0.5 text-warn">A</sup>}
                      </button>
                    </td>
                  );
                })}
                <td className="pr-2 text-xs">{r.mapping ? <Badge tone={r.mapping.status === "accepted" || r.mapping.status === "changed" ? "ok" : r.mapping.confidence === "high" ? "info" : r.mapping.confidence === "none" ? "muted" : "warn"} title={r.mapping.rationale}>{r.mapping.status === "proposed" ? r.mapping.confidence : r.mapping.status}</Badge> : null}</td>
                <td className="text-xs">{checks.length === 0 ? "" : failed ? <Badge tone="bad">{failed} failing</Badge> : <Badge tone="ok">{checks.length} ok</Badge>}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-muted">Legend: <sup className="text-info">R</sup> restated · <sup className="text-warn">A</sup> analyst-corrected (original kept) · struck-through = superseded by another document · red = unreadable, ambiguous or failing a check. Derived metrics are on the Ratios tab and never mixed with reported figures.</p>
    </div>
  );
}

export function Ratios({ grid, onOpen }: { grid: Grid; onOpen: (id: string) => void }) {
  const ids = Array.from(new Set(grid.metrics.map((m) => m.metric)));
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[800px] text-sm">
        <thead className="text-left text-xs text-muted"><tr className="border-b border-line"><th className="py-2">Derived metric</th>{grid.periods.map((p) => <th key={p} className="text-right">{p}</th>)}<th className="pl-4">Formula and limitations</th></tr></thead>
        <tbody>
          {ids.map((id) => {
            const ms = grid.metrics.filter((m) => m.metric === id);
            return (
              <tr key={id} className="border-b border-line/60 align-top">
                <td className="py-2 font-medium">{ms[0].title}</td>
                {grid.periods.map((p) => {
                  const m = ms.find((x) => x.period_end === p);
                  if (!m) return <td key={p} className="text-right text-muted">·</td>;
                  return (
                    <td key={p} className="text-right" title={m.explanation}>
                      {m.status === "computed" ? <button className="num hover:underline" onClick={() => m.inputs[0] && onOpen(m.inputs[0])}>{formatRatio(m.value, m.unit === "monetary" ? null : m.unit)}{m.unit === "monetary" ? ` (${formatDecimal(m.value, 0)} units)` : ""}</button>
                        : <Badge tone={m.status === "special_interpretation" ? "warn" : "muted"}>{m.status.replace(/_/g, " ")}</Badge>}
                    </td>
                  );
                })}
                <td className="pl-4 text-xs text-muted"><code>{ms[0].formula}</code>{ms[0].limitations.length > 0 && <div>{ms[0].limitations.join(" ")}</div>}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-muted">Growth with a zero or negative prior base, and ratios with a zero or negative denominator, are flagged for special interpretation instead of shown as ordinary numbers. EBITDA and debt service coverage are not computed.</p>
    </div>
  );
}
