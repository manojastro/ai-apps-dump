"use client";

import { Loader2, ShieldCheck } from "lucide-react";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";

const schema = z.object({
  email: z.email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

const DEMO_USERS = [
  ["analyst@northstar.example", "Security Analyst"],
  ["approver@northstar.example", "Approver"],
  ["admin@northstar.example", "Administrator"],
  ["viewer@northstar.example", "Viewer"],
];

function LoginForm() {
  const params = useSearchParams();
  const [email, setEmail] = useState("analyst@northstar.example");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [pending, setPending] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = schema.safeParse({ email, password });
    if (!parsed.success) {
      setErrors(Object.fromEntries(parsed.error.issues.map((i) => [String(i.path[0]), i.message])));
      return;
    }
    setErrors({});
    setPending(true);
    try {
      await api.post("/auth/login", parsed.data);
      const next = params.get("next");
      window.location.href = next && next.startsWith("/") && !next.startsWith("//") ? next : "/dashboard";
    } catch (err) {
      setErrors({ form: err instanceof Error ? err.message : "Login failed" });
      setPending(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <div className="space-y-1.5">
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} aria-invalid={!!errors.email} />
        {errors.email && <p className="text-xs text-destructive">{errors.email}</p>}
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="password">Password</Label>
        <Input id="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} aria-invalid={!!errors.password} />
        {errors.password && <p className="text-xs text-destructive">{errors.password}</p>}
      </div>
      {errors.form && <p role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{errors.form}</p>}
      <Button type="submit" className="w-full" size="lg" disabled={pending}>
        {pending && <Loader2 className="animate-spin" />} Sign in
      </Button>
      <div className="rounded-md border border-dashed p-3 text-xs text-muted-foreground">
        <div className="mb-1.5 font-medium text-foreground">Development demo accounts</div>
        <p className="mb-2">Credentials are documented in docs/setup.md and are for local demonstration only.</p>
        <div className="flex flex-wrap gap-1.5">
          {DEMO_USERS.map(([mail, role]) => (
            <button type="button" key={mail} onClick={() => setEmail(mail)} className="rounded border px-2 py-1 hover:bg-muted">
              {role}
            </button>
          ))}
        </div>
      </div>
    </form>
  );
}

export default function LoginPage() {
  return (
    <div className="grid min-h-screen place-items-center bg-[radial-gradient(ellipse_at_top,var(--accent),transparent_60%)] px-4">
      <div className="w-full max-w-md">
        <div className="mb-6 flex items-center justify-center gap-3">
          <span className="grid size-11 place-items-center rounded-xl bg-primary/15 text-primary"><ShieldCheck className="size-6" /></span>
          <div>
            <div className="text-lg font-semibold tracking-tight">AegisRemediate AI</div>
            <div className="text-xs text-muted-foreground">Autonomous Intelligence. Human-Controlled Remediation.</div>
          </div>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Sign in</CardTitle>
            <CardDescription>Enterprise agentic vulnerability remediation orchestration</CardDescription>
          </CardHeader>
          <CardContent>
            <Suspense fallback={null}>
              <LoginForm />
            </Suspense>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
