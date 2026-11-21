import { NextResponse } from "next/server";
import { SESSION_COOKIE, engineFetch } from "@/lib/server";

export async function POST() {
  await engineFetch("/api/auth/logout", { method: "POST" }).catch(() => undefined);
  const out = NextResponse.json({ ok: true });
  out.cookies.set(SESSION_COOKIE, "", { httpOnly: true, path: "/", maxAge: 0 });
  return out;
}
