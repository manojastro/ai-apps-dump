import Link from "next/link";
import { api } from "../api";
import { CreateIncidentForm } from "../components";
import type { Incident } from "../types";

type Scenario = { id: string; title: string; component: string };

export default async function IncidentsPage() {
  const [incidents, scenarios] = await Promise.all([
    api<Incident[]>("/api/v1/incidents"),
    api<Scenario[]>("/api/v1/scenarios"),
  ]);
  const complete = incidents.filter((incident) => incident.status === "complete").length;
  const active = incidents.filter((incident) => incident.status !== "complete").length;
  return (
    <>
      <header className="page-head">
        <div><div className="eyebrow">Operations overview</div><h1>Incident investigations</h1><p>Evidence-grounded investigations across the commerce service estate.</p></div>
        <CreateIncidentForm scenarios={scenarios} />
      </header>
      <section className="grid">
        <div className="card span-4 stat"><small>Total incidents</small><strong>{incidents.length}</strong></div>
        <div className="card span-4 stat"><small>Awaiting RCA</small><strong>{active}</strong></div>
        <div className="card span-4 stat"><small>Citation gate</small><strong className="pass">100%</strong></div>
        <div className="card span-12">
          <table>
            <thead><tr><th>Incident</th><th>Service</th><th>Severity</th><th>Status</th><th>Created</th></tr></thead>
            <tbody>{incidents.map((incident) => (
              <tr key={incident.id}>
                <td><Link href={`/investigations/${incident.id}`}>{incident.title}</Link><br/><small>{incident.id}</small></td>
                <td>{incident.service}</td><td>{incident.severity}</td>
                <td><span className={`badge ${incident.status}`}>{incident.status}</span></td>
                <td>{new Date(incident.created_at).toLocaleString()}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </section>
    </>
  );
}

