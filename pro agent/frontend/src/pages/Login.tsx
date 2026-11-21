import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { Button, ErrorBox, Field, Input } from "../ui";

const DEMO = [
  ["requester@acme.test", "Requester"],
  ["approver@acme.test", "Approver"],
  ["admin@acme.test", "Administrator"],
];

export default function Login() {
  const { refresh } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("requester@acme.test");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api("/api/auth/login", { method: "POST", json: { email, password } });
      await refresh();
      nav("/");
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center px-4 py-10">
      <div className="w-full max-w-md space-y-5">
        <div>
          <h1 className="text-2xl font-semibold">Procurement Navigator</h1>
          <p className="mt-1 text-sm text-muted">Compare synthetic supplier offers, approve, and complete a simulated purchase.</p>
        </div>
        <form onSubmit={submit} className="space-y-4 rounded-lg border border-line bg-white p-5 shadow-sm">
          <Field id="email" label="Email">
            <Input id="email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </Field>
          <Field id="password" label="Password" hint="Demo users are created by the seed command; see README.">
            <Input id="password" type="password" autoComplete="current-password" value={password}
              onChange={(e) => setPassword(e.target.value)} required />
          </Field>
          <ErrorBox error={error} />
          <Button type="submit" disabled={busy} className="w-full">{busy ? "Signing in…" : "Sign in"}</Button>
        </form>
        <div className="text-xs text-muted">
          <p className="mb-1 font-medium">Demo accounts (tenant acme)</p>
          <div className="flex flex-wrap gap-2">
            {DEMO.map(([e, label]) => (
              <button key={e} type="button" className="rounded border border-line bg-white px-2 py-1 hover:bg-canvas"
                onClick={() => setEmail(e)}>{label}</button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
