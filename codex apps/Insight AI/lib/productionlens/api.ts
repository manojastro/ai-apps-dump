let csrf = "";
export function setCsrf(value: string) {
  csrf = value;
}
export async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers:
      body === undefined
        ? {}
        : { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const result = await response
      .json()
      .catch(() => ({
        detail:
          "API disconnected. Start the Python API and worker, then retry.",
      }));
    throw new Error(
      typeof result.detail === "string"
        ? result.detail
        : "Invalid request. Check the form fields.",
    );
  }
  return response.json();
}
