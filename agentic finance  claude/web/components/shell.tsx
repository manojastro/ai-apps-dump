"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { createContext, type ReactNode, useContext, useEffect, useState } from "react";
import { Badge } from "@/components/ui";
import { api } from "@/lib/api";

export type Me = { user: { id: string; email: string; display_name: string }; workspaces: { id: string; name: string; role: string }[] };
type Health = { agent_mode: string; ocr_provider: string; processing: { ocr: string; models: string } };

const Ctx = createContext<{ me?: Me; workspaceId?: string; role?: string; setWorkspace: (id: string) => void }>({ setWorkspace: () => {} });
export const useSession = () => useContext(Ctx);

export function Shell({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me>();
  const [health, setHealth] = useState<Health>();
  const [ws, setWs] = useState<string>();
  const path = usePathname();

  useEffect(() => {
    api<Me>("/me").then((m) => {
      setMe(m);
      let saved: string | null = null;
      try { saved = localStorage.getItem("sl_ws"); } catch { /* storage unavailable */ }
      setWs(m.workspaces.find((w) => w.id === saved)?.id ?? m.workspaces[0]?.id);
    }).catch(() => undefined);
    api<Health>("/health").then(setHealth).catch(() => undefined);
  }, []);

  const setWorkspace = (id: string) => {
    setWs(id);
    try { localStorage.setItem("sl_ws", id); } catch { /* ignore */ }
  };
  const role = me?.workspaces.find((w) => w.id === ws)?.role;
  const nav = [
    { href: "/", label: "Dashboard" },
    { href: "/exports", label: "Exports" },
    { href: "/adjustments", label: "Adjustments" },
    ...(role === "reviewer" || role === "admin" ? [{ href: "/audit", label: "Audit log" }] : []),
  ];

  return (
    <Ctx.Provider value={{ me, workspaceId: ws, role, setWorkspace }}>
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:p-2">Skip to content</a>
      <header className="border-b border-line bg-panel">
        <div className="mx-auto flex max-w-[1500px] flex-wrap items-center gap-4 px-4 py-2.5">
          <Link href="/" className="font-semibold">SpreadLens <span className="text-brand">AI</span></Link>
          <nav aria-label="Main" className="flex gap-1">
            {nav.map((n) => (
              <Link key={n.href} href={n.href} aria-current={path === n.href ? "page" : undefined}
                className={`rounded px-2.5 py-1 text-sm ${path === n.href ? "bg-bg font-semibold" : "text-muted hover:text-ink"}`}>{n.label}</Link>
            ))}
          </nav>
          <div className="ml-auto flex flex-wrap items-center gap-3 text-sm">
            {health && (
              <Badge tone={health.agent_mode === "demo" ? "warn" : "info"} title={`Models: ${health.processing.models}. OCR: ${health.processing.ocr}.`}>
                {health.agent_mode === "demo" ? "DEMO processing (deterministic, no model calls)" : "LIVE processing (eve agents via AI Gateway)"}
              </Badge>
            )}
            {me && (
              <label className="flex items-center gap-1.5">
                <span className="sr-only">Workspace</span>
                <select className="rounded border border-line bg-panel px-2 py-1" value={ws} onChange={(e) => setWorkspace(e.target.value)}>
                  {me.workspaces.map((w) => <option key={w.id} value={w.id}>{w.name} ({w.role})</option>)}
                </select>
              </label>
            )}
            <span className="text-muted">{me?.user.display_name}</span>
            <button className="text-muted underline" onClick={async () => { await fetch("/api/auth/logout", { method: "POST" }); window.location.href = "/login"; }}>Sign out</button>
          </div>
        </div>
      </header>
      <main id="main" className="mx-auto max-w-[1500px] px-4 py-5">{children}</main>
    </Ctx.Provider>
  );
}
