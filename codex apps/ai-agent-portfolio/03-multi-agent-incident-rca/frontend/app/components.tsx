"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { Investigation } from "./types";

const browserApi = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8003";

export function InvestigateButton({ incidentId }: { incidentId: string }) {
  const router = useRouter();
  const [state, setState] = useState("Investigate now");
  async function run() {
    setState("Workers collecting evidence…");
    const response = await fetch(`${browserApi}/api/v1/incidents/${incidentId}/investigate`, {
      method: "POST",
      headers: { "X-User": "operations-console", "X-Role": "investigator" },
    });
    if (!response.ok) {
      setState("Investigation failed");
      return;
    }
    setState("Investigation complete");
    router.refresh();
  }
  return <button onClick={run}>{state}</button>;
}

export function CreateIncidentForm({ scenarios }: { scenarios: Array<{ id: string; title: string; component: string }> }) {
  const router = useRouter();
  const [scenario, setScenario] = useState(scenarios[0]?.id ?? "bad-deployment");
  const [busy, setBusy] = useState(false);
  async function create() {
    setBusy(true);
    const config = scenarios.find((item) => item.id === scenario)!;
    const response = await fetch(`${browserApi}/api/v1/incidents`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Role": "investigator" },
      body: JSON.stringify({
        title: config.title,
        service: config.component,
        scenario,
        severity: "SEV-2",
        alert_summary: "Incident injected from the deterministic operations console",
      }),
    });
    setBusy(false);
    if (response.ok) router.refresh();
  }
  return (
    <div className="create-row">
      <select value={scenario} onChange={(event) => setScenario(event.target.value)} aria-label="Scenario">
        {scenarios.map((item) => <option value={item.id} key={item.id}>{item.title}</option>)}
      </select>
      <button onClick={create} disabled={busy}>{busy ? "Injecting…" : "Inject incident"}</button>
    </div>
  );
}

export function RCAEditor({ investigation }: { investigation: Investigation }) {
  const [markdown, setMarkdown] = useState(investigation.rca.markdown);
  const [state, setState] = useState("Citation gate ready");
  async function save() {
    setState("Validating citations…");
    const response = await fetch(`${browserApi}/api/v1/incidents/${investigation.incident.id}/rca`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", "X-Role": "investigator" },
      body: JSON.stringify({ ...investigation.rca, markdown }),
    });
    setState(response.ok ? "Saved — citation gate passed" : "Rejected — restore required evidence citations");
  }
  return (
    <div className="editor">
      <textarea value={markdown} onChange={(event) => setMarkdown(event.target.value)} aria-label="RCA markdown" />
      <div className="editor-actions"><span>{state}</span><button onClick={save}>Validate & save</button></div>
    </div>
  );
}

export function EvaluationRunner() {
  const [state, setState] = useState("Run all 60 deterministic replays");
  const router = useRouter();
  async function run() {
    setState("Running replay suite…");
    const response = await fetch(`${browserApi}/api/v1/evaluations/run`, {
      method: "POST",
      headers: { "X-User": "evaluation-admin", "X-Role": "admin" },
    });
    setState(response.ok ? "Evaluation complete" : "Evaluation failed");
    router.refresh();
  }
  return <button onClick={run}>{state}</button>;
}

