export type Row = Record<string, unknown>;
export type Mapping = { source: string; field: string; confidence: number };
export type QualityFinding = { level: "Critical" | "Warning" | "Info"; problem: string; count: number; impact: string };
export type Analysis = { rows: Row[]; columns: string[]; mappings: Mapping[]; findings: QualityFinding[]; metrics: Record<string, number>; trend: { period: string; created: number; resolved: number }[]; category: { name: string; value: number }[]; dateRange?: string };

const dictionary: Record<string, string[]> = {
  ticket_id: ["ticket", "incident number", "inc number", "case id", "request number", "number", "id"],
  created_at: ["created", "opened", "logged", "open date", "created date"],
  resolved_at: ["resolved", "closed", "resolution date", "resolved date"],
  status: ["status", "state"], priority: ["priority", "severity", "urgency"],
  category: ["category", "issue type", "incident type"], assignment_group: ["assignment group", "resolver group", "support team", "queue"],
  short_description: ["short description", "summary", "subject", "description"], sla_status: ["sla", "breach"],
};
const norm = (v: unknown) => String(v ?? "").trim().toLowerCase();
export function detectSchema(columns: string[]): Mapping[] { return columns.map(source => {
  const clean = source.toLowerCase().replace(/[_-]/g, " "); let best = "unmapped", confidence = 0;
  Object.entries(dictionary).forEach(([field, aliases]) => aliases.forEach(alias => { const score = clean === alias ? 99 : clean.includes(alias) || alias.includes(clean) ? 84 : 0; if (score > confidence) { best = field; confidence = score; } }));
  return { source, field: best, confidence };
}); }
export function analyze(rows: Row[], columns: string[]): Analysis {
  const mappings = detectSchema(columns); const col = (field: string) => mappings.find(m => m.field === field)?.source;
  const ticket = col("ticket_id"), created = col("created_at"), resolved = col("resolved_at"), status = col("status"), category = col("category"), sla = col("sla_status");
  const blank = columns.reduce((sum, c) => sum + rows.filter(r => norm(r[c]) === "").length, 0);
  const ids = ticket ? rows.map(r => norm(r[ticket])).filter(Boolean) : []; const duplicateIds = new Set(ids.filter((id, i) => ids.indexOf(id) !== i)).size;
  const invalidDates = created ? rows.filter(r => r[created] && Number.isNaN(new Date(String(r[created])).getTime())).length : 0;
  const findings: QualityFinding[] = [
    ...(duplicateIds ? [{ level: "Warning" as const, problem: "Duplicate ticket identifiers", count: duplicateIds, impact: "May overstate operational volume." }] : []),
    ...(invalidDates ? [{ level: "Warning" as const, problem: "Invalid created dates", count: invalidDates, impact: "Trend calculations may be incomplete." }] : []),
    ...(blank ? [{ level: "Info" as const, problem: "Blank source values", count: blank, impact: "Some metrics may be unavailable." }] : []),
  ];
  const resolvedRows = resolved ? rows.filter(r => r[resolved]) : status ? rows.filter(r => /resolved|closed|complete/i.test(norm(r[status]))) : [];
  const slaBreaches = sla ? rows.filter(r => /breach|failed|missed/i.test(norm(r[sla]))).length : 0;
  const resolutionHours = created && resolved ? rows.map(r => ({ a: new Date(String(r[created])).getTime(), b: new Date(String(r[resolved])).getTime() })).filter(x => Number.isFinite(x.a) && Number.isFinite(x.b) && x.b >= x.a).map(x => (x.b-x.a)/36e5) : [];
  const metrics: Record<string, number> = { "Total tickets": rows.length, "Resolved tickets": resolvedRows.length, "Resolution rate": rows.length ? Math.round(resolvedRows.length / rows.length * 1000) / 10 : 0, ...(resolutionHours.length ? { "Average resolution (hrs)": Math.round(resolutionHours.reduce((a,b)=>a+b,0)/resolutionHours.length*10)/10 } : {}), ...(sla ? { "SLA breaches": slaBreaches, "SLA compliance": Math.round((1-slaBreaches/rows.length)*1000)/10 } : {}) };
  const periodMap = new Map<string, {created:number;resolved:number}>(); rows.forEach(r => { if (!created) return; const d = new Date(String(r[created])); if (Number.isNaN(d.getTime())) return; const key = d.toLocaleDateString("en-US", { month:"short", year:"2-digit" }); const x = periodMap.get(key) ?? {created:0,resolved:0}; x.created++; if (resolved && r[resolved]) x.resolved++; periodMap.set(key,x); });
  const categories = new Map<string, number>(); if (category) rows.forEach(r => { const v=String(r[category] ?? "Unspecified"); categories.set(v,(categories.get(v)??0)+1); });
  const dates = created ? rows.map(r => new Date(String(r[created])).getTime()).filter(Number.isFinite) : [];
  return { rows, columns, mappings, findings, metrics, trend: [...periodMap].map(([period, v])=>({period,...v})), category: [...categories].map(([name,value])=>({name,value})).sort((a,b)=>b.value-a.value).slice(0,8), dateRange: dates.length ? `${new Date(Math.min(...dates)).toLocaleDateString()} – ${new Date(Math.max(...dates)).toLocaleDateString()}` : undefined };
}
