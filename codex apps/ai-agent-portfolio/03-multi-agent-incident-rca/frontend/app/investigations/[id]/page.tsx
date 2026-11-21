import Link from "next/link";
import { api } from "../../api";
import { InvestigateButton } from "../../components";
import type { Incident, Investigation } from "../../types";

export default async function InvestigationPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const incident = await api<Incident>(`/api/v1/incidents/${id}`);
  let investigation: Investigation | null = null;
  try { investigation = await api<Investigation>(`/api/v1/incidents/${id}/investigation`); } catch { /* open incident */ }
  return (
    <>
      <header className="page-head"><div><div className="eyebrow">{incident.id} · {incident.severity}</div><h1>{incident.title}</h1><p>{incident.service} · {incident.scenario}</p></div>{!investigation && <InvestigateButton incidentId={id} />}</header>
      {investigation ? <>
        <div className="tabs">
          <Link href={`/evidence/${id}`}>Evidence explorer</Link><Link href={`/timeline/${id}`}>Timeline</Link><Link href={`/hypotheses/${id}`}>Hypotheses</Link><Link href="/graph">Dependency graph</Link><Link href={`/rca/${id}`}>Final RCA</Link>
        </div>
        <section className="grid">
          <div className="card span-8"><h2>Supervisor plan</h2><ol>{investigation.plan.map((step) => <li key={step}>{step}</li>)}</ol></div>
          <div className="card span-4 stat"><small>Investigation duration</small><strong>{investigation.duration_ms.toFixed(1)} ms</strong><p>{investigation.evidence.length} immutable evidence records</p></div>
          <div className="card span-12"><h2>Worker activity</h2>{investigation.worker_runs.map((run) => <div className="worker" key={run.worker}><div><strong>{run.worker}</strong><small>{run.tool} · {run.evidence_count} records</small></div><div><span className={`badge ${run.status === "complete" ? "complete" : "open"}`}>{run.status}</span> {run.latency_ms.toFixed(1)} ms</div></div>)}</div>
          <div className="card span-8"><h2>Leading hypothesis</h2><div className="confidence">{(investigation.hypotheses[0].confidence * 100).toFixed(0)}%</div><p>{investigation.hypotheses[0].statement}</p><span className="evidence-id">{investigation.hypotheses[0].supporting_evidence_ids.length} supporting sources</span></div>
          <div className="card span-4 critic"><h2>Critic pass</h2><strong>{investigation.critic.overturned ? "Leader overturned" : "Leader sustained"}</strong><p>{investigation.critic.challenge}</p></div>
        </section>
      </> : <section className="card"><h2>Ready to investigate</h2><p>The supervisor will fan out to four read-only telemetry workers, correlate their evidence, rank hypotheses, and run a critic before composing an RCA.</p></section>}
    </>
  );
}

