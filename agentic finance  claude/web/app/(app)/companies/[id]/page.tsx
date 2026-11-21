"use client";
import Link from "next/link";
import { use, useRef, useState } from "react";
import { Alert, Badge, Card, Spinner, StatusBadge, when } from "@/components/ui";
import { api, errorText } from "@/lib/api";
import { useApi } from "@/lib/hooks";

type Version = { id: string; version_no: number; filename: string; kind: string; size: number; pages: number | null; sha256: string;
  status: string; duplicate_of: string | null; created_at: string; open_questions: number;
  run: { id: string; status: string; state: string; mode: string; error: string | null } | null };
type Company = { company: { id: string; name: string; supported: boolean; unsupported_reason: string | null }; role: string;
  documents: { id: string; title: string; versions: Version[] }[];
  spreads: { id: string; scope: string; currency: string; version: number; review_status: string; display_scale: string }[] };

const ACTIVE = new Set(["uploaded", "checking", "understanding", "extracting", "mapping", "normalizing", "reconciling"]);

export default function CompanyPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, error, reload } = useApi<Company>(`/companies/${id}`, (d) =>
    d?.documents.some((doc) => doc.versions.some((v) => ACTIVE.has(v.status) || v.run?.status === "running")) ? 1500 : 8000);
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [msg, setMsg] = useState<{ tone: "ok" | "bad"; text: string }>();

  async function upload(files: FileList | null) {
    if (!files?.length) return;
    setUploading(true);
    setMsg(undefined);
    try {
      for (const f of Array.from(files)) {
        const fd = new FormData();
        fd.append("file", f);
        const r = await api<{ duplicate_of: string | null; version_no: number }>(`/companies/${id}/documents`, { method: "POST", body: fd });
        setMsg({ tone: "ok", text: r.duplicate_of ? `${f.name}: duplicate of an earlier upload (not reprocessed).` : `${f.name}: uploaded as revision ${r.version_no}; processing started.` });
      }
    } catch (e) {
      setMsg({ tone: "bad", text: errorText(e) });
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
      reload();
    }
  }

  if (error) return <Alert tone="bad">{error}</Alert>;
  if (!data) return <Spinner />;
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">{data.company.name}</h1>
        {!data.company.supported && <Badge tone="bad">Unsupported for automatic spreading</Badge>}
      </div>
      {!data.company.supported && <Alert tone="bad">{data.company.unsupported_reason}. Banks, insurers and other specialised financial institutions are not supported in this version.</Alert>}

      <Card title="Spreads (one per reporting entity, scope and currency)">
        {data.spreads.length === 0 ? <p className="text-sm text-muted">No spreads yet. Upload statements below.</p> : (
          <div className="flex flex-wrap gap-3">
            {data.spreads.map((s) => (
              <Link key={s.id} href={`/spreads/${s.id}`} className="rounded-lg border border-line px-4 py-3 hover:bg-bg">
                <div className="font-medium capitalize">{s.scope}</div>
                <div className="text-xs text-muted">{s.currency} · display in {s.display_scale} · version {s.version}</div>
                <div className="mt-1"><StatusBadge status={s.review_status} /></div>
              </Link>
            ))}
          </div>
        )}
      </Card>

      <Card title="Documents" actions={
        <div className="flex items-center gap-2">
          <input ref={fileRef} id="upload" type="file" accept=".pdf,.xlsx,application/pdf,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" multiple className="sr-only" onChange={(e) => upload(e.target.files)} />
          <label htmlFor="upload" className={`cursor-pointer rounded-md bg-brand px-3 py-1.5 text-sm font-medium text-brand-ink ${uploading ? "opacity-50" : ""}`}>{uploading ? "Uploading…" : "Upload statements (PDF / XLSX)"}</label>
        </div>}>
        {msg && <div className="mb-3"><Alert tone={msg.tone}>{msg.text}</Alert></div>}
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-muted">
            <tr><th className="py-1.5">Document</th><th>Revision</th><th>Type</th><th>Status</th><th>Run</th><th>Uploaded</th></tr>
          </thead>
          <tbody className="divide-y divide-line">
            {data.documents.flatMap((d) => d.versions.map((v) => (
              <tr key={v.id}>
                <td className="py-2"><Link className="text-brand hover:underline" href={`/documents/${v.id}`}>{v.filename}</Link>
                  <div className="font-mono text-[11px] text-muted" title={v.sha256}>sha256 {v.sha256.slice(0, 12)}…</div></td>
                <td>v{v.version_no}</td>
                <td>{v.kind.toUpperCase()}{v.pages ? ` · ${v.pages} ${v.kind === "pdf" ? "pages" : "sheets"}` : ""}</td>
                <td className="space-x-1">
                  <StatusBadge status={v.status} />
                  {ACTIVE.has(v.status) && <Spinner label="" />}
                  {v.open_questions > 0 && <Link href={`/documents/${v.id}`}><Badge tone="warn">{v.open_questions} question(s) to confirm</Badge></Link>}
                </td>
                <td>{v.run ? <Link className="text-brand hover:underline" href={`/runs/${v.run.id}`}><Badge>{v.run.mode}</Badge> {v.run.state}</Link> : "—"}
                  {v.run?.error && <div className="text-xs text-bad">{v.run.error}</div>}</td>
                <td className="text-xs text-muted">{when(v.created_at)}</td>
              </tr>
            )))}
            {data.documents.length === 0 && <tr><td colSpan={6} className="py-3 text-muted">No documents uploaded.</td></tr>}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
