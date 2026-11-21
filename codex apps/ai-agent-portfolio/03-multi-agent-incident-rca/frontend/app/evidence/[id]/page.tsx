import Link from "next/link";
import { api } from "../../api";
import type { Investigation } from "../../types";

export default async function EvidencePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const investigation = await api<Investigation>(`/api/v1/incidents/${id}/investigation`);
  return <><header className="page-head"><div><div className="eyebrow">Immutable source records</div><h1>Evidence explorer</h1><p>{investigation.incident.title}</p></div><Link href={`/investigations/${id}`}>Back to investigation</Link></header><section className="grid">{["metrics","logs","changes","tickets"].map((source) => <div className="card span-6" key={source}><h2>{source.toUpperCase()}</h2>{investigation.evidence.filter((item) => item.source === source).map((item) => <article className="evidence-row" key={item.id}><span className="evidence-id">{item.id}</span><span className="source">{item.service}</span><p>{item.summary}</p><small>{new Date(item.observed_at).toLocaleString()} · {item.source_ref}</small></article>)}</div>)}</section></>;
}

