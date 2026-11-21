"use client";
import { useState } from "react";
import { Alert, Button, Field, inputClass } from "@/components/ui";

export default function LoginPage() {
  const [email, setEmail] = useState("analyst@demo.local");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(undefined);
    const res = await fetch("/api/auth/login", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email, password }) });
    setBusy(false);
    if (res.ok) window.location.href = "/";
    else setError((await res.json().catch(() => ({}))).detail ?? "Login failed");
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <form onSubmit={submit} className="w-full max-w-sm space-y-4 rounded-lg border border-line bg-panel p-6" aria-labelledby="login-title">
        <div>
          <h1 id="login-title" className="text-lg font-semibold">SpreadLens AI</h1>
          <p className="text-sm text-muted">Financial spreading and analyst review</p>
        </div>
        <Field label="Email"><input className={inputClass} type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required /></Field>
        <Field label="Password"><input className={inputClass} type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required /></Field>
        {error && <Alert tone="bad">{error}</Alert>}
        <Button type="submit" disabled={busy} className="w-full justify-center">{busy ? "Signing in…" : "Sign in"}</Button>
        <p className="text-xs text-muted">Local demo users: analyst@demo.local, reviewer@demo.local, admin@demo.local (password from SPREADLENS_SEED_PASSWORD).</p>
      </form>
    </main>
  );
}
