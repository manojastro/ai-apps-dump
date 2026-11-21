const API = process.env.NEXT_PUBLIC_API_URL || "";

export async function api<T = any>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${text}`);
  }
  return res.json();
}

export const getMetrics = () => api("/api/metrics");
export const getPipelines = () => api("/api/pipelines");
export const getPipeline = (id: string) => api(`/api/pipelines/${id}`);
export const getIncidents = () => api("/api/incidents");
export const getIncident = (id: string) => api(`/api/incidents/${id}`);
export const getIncidentGraph = (id: string) => api(`/api/incidents/${id}/graph`);
export const getEvidence = (id: string) => api(`/api/incidents/${id}/evidence`);
export const getHypotheses = (id: string) => api(`/api/incidents/${id}/hypotheses`);
export const getReport = (id: string) => api(`/api/incidents/${id}/report`);
export const getTimeline = (id: string) => api(`/api/incidents/${id}/timeline`);
export const investigate = (id: string) => api(`/api/incidents/${id}/investigate`, { method: "POST" });
export const approve = (id: string, decision: string, comment?: string) =>
  api(`/api/incidents/${id}/approval`, {
    method: "POST",
    body: JSON.stringify({ decision, comment }),
  });
export const getQuality = () => api("/api/quality");
export const getLineage = () => api("/api/lineage");
export const getPolicies = () => api("/api/policies");
export const getObservability = () => api("/api/observability");
export const getEvaluations = () => api("/api/evaluations");
export const getScenarios = () => api("/api/scenarios");
export const runScenario = (id: string) => api(`/api/scenarios/${id}/run`, { method: "POST" });
export const getSettings = () => api("/api/settings");
export const getHealth = () => api("/api/health");
