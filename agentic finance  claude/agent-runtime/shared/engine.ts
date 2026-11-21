// Read-only callbacks into the SpreadLens engine. Every call carries the signed tool scope that the
// coordinator placed in this turn's client context; the engine derives the workspace from its signature,
// so a model cannot widen its own access by choosing another workspace.
const base = () => process.env.SPREADLENS_ENGINE_URL ?? "http://127.0.0.1:8000";

function headers(scope: string): Record<string, string> {
  return {
    authorization: `Bearer ${process.env.SPREADLENS_AGENT_TOOL_TOKEN ?? ""}`,
    "x-spreadlens-scope": scope,
  };
}

export async function engineGet(path: string, scope: string): Promise<unknown> {
  const res = await fetch(`${base()}${path}`, { headers: headers(scope) });
  if (!res.ok) throw new Error(`engine tool ${path} returned HTTP ${res.status}`);
  return res.json();
}

export async function enginePost(path: string, scope: string, body: unknown): Promise<unknown> {
  const res = await fetch(`${base()}${path}`, {
    method: "POST",
    headers: { ...headers(scope), "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`engine tool ${path} returned HTTP ${res.status}`);
  return res.json();
}
