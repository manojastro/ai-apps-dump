"use client";
import Link from "next/link";
import { use, useState } from "react";
import { Alert, Badge, Button, Card, Kv, Spinner, StatusBadge, inputClass, when } from "@/components/ui";
import { errorText, post } from "@/lib/api";
import { useApi } from "@/lib/hooks";

type Doc = {
  id: string; title: string; company_id: string; filename: string; kind: string; pages: number | null; sha256: string; size: number;
  version_no: number; status: string; integrity: string; integrity_detail: string; duplicate_of: string | null;
  runs: { id: string; kind: string; mode: string; state: string; status: string; error: string | null; usage: Record<string, number>;
    tasks: { id: string; stage: string; status: string; attempts: number; max_attempts: number; duration_ms: number | null; error: string | null }[] }[];
  questions: { id: string; field: string; statement_key: string | null; question: string; options: string[]; evidence: { quote: string; page: number | null }[]; answer: string | null; answered_at: string | null }[];
  statements: { id: string; type: string; title: string; scope: string | null; currency: string | null; scale: string | null; pages: number[]; sheet: string | null;
    columns: { column_index: number; header_raw: string; period_end: string | null; duration: string; restated: boolean }[]; method: string; framework: string }[];
  document_exceptions: { id: string; category: string; severity: string; title: string; detail: string; status: string }[];
};

function Question({ q, onDone }: { q: Doc["questions"][number]; onDone: () => void }) {
  const [value, setValue] = useState(q.options[0] ?? "");
  const [err, setErr] = useState<string>();
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try { await post(`/questions/${q.id}/answer`, { answer: value }); onDone(); } catch (x) { setErr(errorText(x)); }
  }
  return (
    <form onSubmit={submit} className="space-y-2 rounded-md border border-warn/40 bg-warn-bg/40 p-3">
      <div className="text-sm font-medium">{q.question}</div>
      {q.evidence.length > 0 && <ul className="text-xs text-muted">{q.evidence.map((e, i) => <li key={i}>“{e.quote}”{e.page ? ` (page ${e.page})` : ""}</li>)}</ul>}
      <div className="flex flex-wrap items-center gap-2">
        {q.field === "period" ? (
          <input aria-label="Period end date" type="date" className={inputClass + " max-w-48"} value={value} onChange={(e) => setValue(e.target.value)} required />
        ) : q.options.length ? (
          <select aria-label={q.field} className={inputClass + " max-w-48"} value={value} onChange={(e) => setValue(e.target.value)}>
            {q.options.map((o) => <option key={o}>{o}</option>)}
          </select>
        ) : (
          <input aria-label={q.field} className={inputClass + " max-w-72"} value={value} onChange={(e) => setValue(e.target.value)} required />
        )}
        <Button type="submit">Confirm</Button>
      </div>
      {err && <Alert tone="bad">{err}</Alert>}
    </form>
  );
}

export default function DocumentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, error, reload } = useApi<Doc>(`/documents/${id}`, (d) => (d?.runs[0]?.status === "running" ? 1500 : 10000));
  if (error) return <Alert tone="bad">{error}</Alert>;
  if (!data) return <Spinner />;
  const open = data.questions.filter((q) => !q.answer);
  const run = data.runs[0];
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <Link href={`/companies/${data.company_id}`} className="text-sm text-brand hover:underline">← Company</Link>
        <h1 className="text-xl font-semibold">{data.filename}</h1>
        <StatusBadge status={data.status} />
      </div>
      {open.length > 0 && (
        <Card title={`Confirm ${open.length} ambiguous item(s) before normalization`}>
          <p className="mb-3 text-sm text-muted">The Document Understanding Agent could not establish these from the document and does not guess. Processing resumes when all are confirmed.</p>
          <div className="space-y-3">{open.map((q) => <Question key={q.id} q={q} onDone={reload} />)}</div>
        </Card>
      )}
      {data.document_exceptions.map((e) => (
        <Alert key={e.id} tone={e.severity === "critical" ? "bad" : e.severity === "warning" ? "warn" : "info"}><strong>{e.title}.</strong> {e.detail}</Alert>
      ))}
      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="Integrity and file">
          <Kv items={[["Revision", `v${data.version_no}`], ["Type", data.kind.toUpperCase()], ["Pages / sheets", data.pages ?? "—"],
            ["Size", `${(data.size / 1024).toFixed(1)} KB`], ["SHA-256", <span key="s" className="font-mono text-xs">{data.sha256}</span>],
            ["Integrity", <span key="i"><StatusBadge status={data.integrity} /> {data.integrity_detail}</span>],
            ["Duplicate of", data.duplicate_of ?? "—"]]} />
          <a className="mt-3 inline-block text-sm text-brand hover:underline" href={`/api/engine/documents/${id}/file`} target="_blank" rel="noreferrer">Open original file</a>
        </Card>
        <Card title="Processing" actions={run && <Link href={`/runs/${run.id}`} className="text-sm text-brand hover:underline">Workflow trace →</Link>}>
          {run ? (
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2 text-sm"><Badge tone={run.mode === "demo" ? "warn" : "info"}>{run.mode} mode</Badge><StatusBadge status={run.status} /> state: {run.state}</div>
              {run.error && <Alert tone="bad">{run.error}</Alert>}
              <ol className="space-y-1 text-sm">
                {run.tasks.map((t) => (
                  <li key={t.id} className="flex items-center gap-2"><span className="w-32">{t.stage}</span><StatusBadge status={t.status} />
                    <span className="text-xs text-muted">attempt {t.attempts}/{t.max_attempts}{t.duration_ms != null ? ` · ${t.duration_ms} ms` : ""}</span>
                    {t.error && t.status !== "succeeded" && <span className="truncate text-xs text-bad" title={t.error}>{t.error}</span>}</li>
                ))}
              </ol>
            </div>
          ) : <p className="text-sm text-muted">Not started.</p>}
        </Card>
      </div>
      <Card title="Statements identified">
        {data.statements.length === 0 ? <p className="text-sm text-muted">None yet.</p> : (
          <table className="w-full text-sm">
            <thead className="text-left text-xs text-muted"><tr><th className="py-1">Statement</th><th>Scope</th><th>Currency / unit</th><th>Periods</th><th>Location</th><th>Method</th></tr></thead>
            <tbody className="divide-y divide-line">
              {data.statements.map((s) => (
                <tr key={s.id}>
                  <td className="py-2">{s.title}<div className="text-xs text-muted">{s.framework !== "unknown" ? s.framework : "framework not stated"}</div></td>
                  <td>{s.scope ?? <Badge tone="warn">unconfirmed</Badge>}</td>
                  <td>{s.currency ?? <Badge tone="warn">?</Badge>} {s.scale ?? <Badge tone="warn">unit?</Badge>}</td>
                  <td>{s.columns.map((c) => <div key={c.column_index}>{c.period_end ?? <Badge tone="warn">{c.header_raw}?</Badge>} <span className="text-xs text-muted">{c.duration}</span> {c.restated && <Badge tone="info">restated</Badge>}</div>)}</td>
                  <td>{s.sheet ? `sheet ${s.sheet}` : `pages ${s.pages.join(", ")}`}</td>
                  <td><Badge>{s.method}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
      <p className="text-xs text-muted">Answered questions: {data.questions.filter((q) => q.answer).map((q) => `${q.field}=${q.answer} (${when(q.answered_at)})`).join("; ") || "none"}</p>
    </div>
  );
}
