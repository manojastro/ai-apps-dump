"use client";

import { type FormEvent, useState } from "react";

import { ErrorNote } from "@/components/shared";
import { Button, Card, CardContent, Input } from "@/components/ui/primitives";
import { ApiError, api } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      window.location.href = "/";
    } catch (failure) {
      setError(failure instanceof ApiError ? failure.message : "Sign-in failed");
      setBusy(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-sm">
        <CardContent className="p-6">
          <div className="mb-5 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-sm font-bold text-primary-foreground">
              R
            </div>
            <div>
              <h1 className="text-base font-semibold leading-tight">RevenueOS AI</h1>
              <p className="text-xs text-muted-foreground">All data here is synthetic</p>
            </div>
          </div>
          <form onSubmit={submit} className="space-y-3">
            <div className="space-y-1">
              <label htmlFor="email" className="text-xs font-medium">Email</label>
              <Input id="email" type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div className="space-y-1">
              <label htmlFor="password" className="text-xs font-medium">Password</label>
              <Input id="password" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            {error && <ErrorNote message={error} />}
            <Button type="submit" className="w-full" disabled={busy}>
              {busy ? "Signing in..." : "Sign in"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
