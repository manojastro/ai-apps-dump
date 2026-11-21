"use client";
// Browser API client. All monetary values arrive as decimal STRINGS and are never converted to JS numbers.

export class ApiError extends Error {
  constructor(public status: number, public detail: unknown) {
    super(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
}

export async function api<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api/engine${path}`, { ...init, cache: "no-store" });
  if (res.status === 401 && typeof window !== "undefined" && !path.startsWith("/auth")) {
    window.location.href = "/login";
  }
  const ct = res.headers.get("content-type") ?? "";
  const body = ct.includes("application/json") ? await res.json() : await res.text();
  if (!res.ok) throw new ApiError(res.status, (body as { detail?: unknown })?.detail ?? body);
  return body as T;
}

export function post<T = unknown>(path: string, body?: unknown): Promise<T> {
  return api<T>(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export function errorText(e: unknown): string {
  if (e instanceof ApiError) {
    const d = e.detail as { message?: string; reasons?: string[] } | string;
    if (typeof d === "object" && d && "reasons" in d) return `${d.message}: ${(d.reasons ?? []).join("; ")}`;
    if (Array.isArray(d)) return d.map((x: { msg?: string }) => x.msg).join("; ");
    return typeof d === "string" ? d : JSON.stringify(d);
  }
  return e instanceof Error ? e.message : String(e);
}
