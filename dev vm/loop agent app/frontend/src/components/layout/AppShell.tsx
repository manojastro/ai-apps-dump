"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  GitBranch,
  LayoutDashboard,
  Shield,
  Database,
  AlertTriangle,
  LineChart,
  Settings,
  FlaskConical,
  Radar,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/pipelines", label: "Pipelines", icon: Database },
  { href: "/incidents", label: "Incidents", icon: AlertTriangle },
  { href: "/quality", label: "Quality", icon: Radar },
  { href: "/lineage", label: "Lineage", icon: GitBranch },
  { href: "/evaluations", label: "Evaluations", icon: FlaskConical },
  { href: "/policies", label: "Policies", icon: Shield },
  { href: "/observability", label: "Observability", icon: LineChart },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return (
    <div className="min-h-screen flex">
      <aside className="relative w-60 shrink-0 border-r border-line bg-ink-900/80 backdrop-blur">
        <div className="h-14 px-4 flex items-center gap-2 border-b border-line">
          <Activity className="w-4 h-4 text-teal-300" />
          <div>
            <div className="text-[13px] font-semibold tracking-wide">DataSentinel AI</div>
            <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">Reliability graph</div>
          </div>
        </div>
        <nav className="p-2 space-y-0.5">
          {NAV.map((item) => {
            const active = path === item.href || path.startsWith(item.href + "/");
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-md text-[13px] border border-transparent",
                  active
                    ? "bg-teal-400/10 text-teal-200 border-teal-400/20"
                    : "text-zinc-400 hover:text-zinc-100 hover:bg-white/5"
                )}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="absolute bottom-0 w-60 p-3 border-t border-line text-[11px] text-zinc-500">
          Demo mode · mock LLM · bounded autonomy
        </div>
      </aside>
      <main className="flex-1 min-w-0">
        <header className="h-14 border-b border-line px-6 flex items-center justify-between bg-ink-900/40">
          <div className="text-[12px] text-zinc-500 uppercase tracking-[0.2em]">Data platform health</div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] px-2 py-1 rounded border border-teal-400/30 text-teal-300 bg-teal-400/10">
              MOCK PROVIDER
            </span>
            <span className="text-[11px] px-2 py-1 rounded border border-line text-zinc-400">prod-sim</span>
          </div>
        </header>
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
