import { NextResponse } from "next/server";
import { ENGINE_URL, SESSION_COOKIE } from "@/lib/server";

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const res = await fetch(`${ENGINE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email: String(body.email ?? ""), password: String(body.password ?? "") }),
    cache: "no-store",
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) return NextResponse.json({ detail: data.detail ?? "Login failed" }, { status: res.status });
  const out = NextResponse.json({ user: data.user });
  out.cookies.set(SESSION_COOKIE, data.token, {
    httpOnly: true,
    sameSite: "strict",
    secure: process.env.COOKIE_SECURE === "true",
    path: "/",
    maxAge: 60 * 60 * 12,
  });
  return out;
}
