import Link from "next/link";
import { api } from "../../api";
import type { Investigation } from "../../types";

export default async function TimelinePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const investigation = await api<Investigation>(`/api/v1/incidents/${id}/investigation`);
  return <><header className="page-head"><div><div className="eyebrow">Cross-source correlation</div><h1>Incident timeline</h1><p>{investigation.timeline.length} normalized observations in causal order.</p></div><Link href={`/investigations/${id}`}>Back to investigation</Link></header><section className="card timeline">{investigation.timeline.map((event) => <article key={`${event.timestamp}-${event.title}`}><small>{new Date(event.timestamp).toLocaleString()}</small><h2>{event.title}</h2><p>{event.detail}</p>{event.evidence_ids.map((evidenceId) => <span className="evidence-id" key={evidenceId}>{evidenceId}</span>)}</article>)}</section></>;
}

