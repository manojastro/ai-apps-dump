// Server-only helpers for the BFF: the session token lives in an httpOnly cookie and is never exposed to JS.
import { cookies } from "next/headers";

export const ENGINE_URL = process.env.ENGINE_URL ?? "http://127.0.0.1:8000";
export const SESSION_COOKIE = "sl_session";

export async function sessionToken(): Promise<string | undefined> {
  return (await cookies()).get(SESSION_COOKIE)?.value;
}

export async function engineFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = await sessionToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("authorization", `Bearer ${token}`);
  if (!headers.has("x-correlation-id")) headers.set("x-correlation-id", crypto.randomUUID().replace(/-/g, "").slice(0, 16));
  return fetch(`${ENGINE_URL}${path}`, { ...init, headers, cache: "no-store", redirect: "manual" });
}
