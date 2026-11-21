// Thin client for the Procurement Navigator API. Cookies carry the session; mutations send the
// CSRF token from the readable csrf cookie. Errors arrive in a stable envelope.

export class ApiError extends Error {
  status: number;
  code: string;
  details: Record<string, unknown>;
  constructor(status: number, code: string, message: string, details: Record<string, unknown> = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function csrf(): string {
  const m = document.cookie.match(/(?:^|; )procnav_csrf=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : "";
}

export async function api<T = any>(path: string, init: RequestInit & { json?: unknown; idempotent?: boolean } = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const method = (init.method ?? "GET").toUpperCase();
  let body = init.body;
  if (init.json !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(init.json);
  }
  if (method !== "GET") headers.set("X-CSRF-Token", csrf());
  if (init.idempotent) headers.set("Idempotency-Key", crypto.randomUUID());
  const res = await fetch(path, { ...init, method, headers, body, credentials: "same-origin" });
  const type = res.headers.get("content-type") ?? "";
  const data = type.includes("application/json") ? await res.json() : await res.text();
  if (!res.ok) {
    const e = (data as any)?.error ?? {};
    throw new ApiError(res.status, e.code ?? "HTTP_" + res.status, e.message ?? res.statusText, e.details ?? {});
  }
  return data as T;
}

export const inr = (v: string | number | null | undefined) => {
  if (v === null || v === undefined || v === "") return "—";
  const n = typeof v === "number" ? v : Number(v);
  return "₹" + n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

export const when = (iso?: string | null) => (iso ? new Date(iso).toLocaleString() : "—");

export const seconds = (ms: number) => `${(ms / 1000).toFixed(1)}s`;

export type Role = "requester" | "approver" | "admin" | "viewer";

export interface Session {
  user: { id: string; email: string; display_name: string };
  tenant: { id: string; slug: string; name: string };
  roles: Role[];
  csrf_token: string;
}
