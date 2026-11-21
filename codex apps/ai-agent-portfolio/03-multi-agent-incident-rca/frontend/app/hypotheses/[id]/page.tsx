import Link from "next/link";
import { api } from "../../api";
import type { Investigation } from "../../types";

export default async function HypothesesPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const investigation = await api<Investigation>(`/api/v1/incidents/${id}/investigation`);
  return <><header className="page-head"><div><div className="eyebrow">Ranker + devil&apos;s advocate</div><h1>Hypothesis comparison</h1><p>Support, contradiction, and concise decision rationale.</p></div><Link href={`/investigations/${id}`}>Back to investigation</Link></header><section className="grid">{investigation.hypotheses.map((hypothesis) => <article className={`card span-6 hypothesis ${hypothesis.rank === 1 ? "leader" : ""}`} key={hypothesis.id}><div className="eyebrow">Rank {hypothesis.rank} · {hypothesis.category}</div><div className="confidence">{(hypothesis.confidence * 100).toFixed(0)}%</div><h2>{hypothesis.statement}</h2><p>{hypothesis.rationale}</p><small>Supports: {hypothesis.supporting_evidence_ids.join(", ") || "none"}</small><br/><small>Contradicts: {hypothesis.contradicting_evidence_ids.join(", ") || "none"}</small></article>)}<article className="card span-12 critic"><h2>Critic finding</h2><strong>{investigation.critic.overturned ? "Original leader overturned" : "Original leader sustained"}</strong><p>{investigation.critic.challenge}</p><span className="evidence-id">{investigation.critic.evidence_ids.join(" · ")}</span></article></section></>;
}

