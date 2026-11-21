"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Award,
  Brain,
  Briefcase,
  Building2,
  LineChart,
  FlaskConical,
  FolderKanban,
  Kanban,
  LayoutDashboard,
  Layers,
  Mic,
  PanelLeft,
  Search,
  Settings,
  ShieldCheck,
  Sunrise,
  Target,
  Users,
} from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { derivePhase } from "@/lib/phase";
import { computeReadiness } from "@/lib/scoring";
import { deriveNotifications } from "@/lib/notifications";
import { APP_NAME } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { useCareerStore } from "@/store/career-store";
import { CommandPalette, useCommandPalette } from "@/components/overlays/command-palette";
import { QuickAddDialog } from "@/components/overlays/quick-add";
import { BackupDialog } from "@/components/overlays/backup-dialog";
import { SaveStatus } from "@/components/shell/save-status";

const NAV_GROUPS = [
  {
    label: "Command",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/today", label: "Today", icon: Sunrise },
    ],
  },
  {
    label: "Build",
    items: [
      { href: "/skills", label: "Skills", icon: Brain },
      { href: "/projects", label: "Projects", icon: Layers },
      { href: "/evidence", label: "Evidence", icon: ShieldCheck },
      { href: "/roles", label: "Roles", icon: Target },
    ],
  },
  {
    label: "Market",
    items: [
      { href: "/jobs", label: "Jobs", icon: Briefcase },
      { href: "/companies", label: "Companies", icon: Building2 },
      { href: "/network", label: "Network", icon: Users },
    ],
  },
  {
    label: "Prepare",
    items: [
      { href: "/interview", label: "Interview", icon: Mic },
      { href: "/certifications", label: "Certifications", icon: Award },
      { href: "/research", label: "Research", icon: FlaskConical },
    ],
  },
  {
    label: "Operate",
    items: [
      { href: "/execution", label: "Execution", icon: Kanban },
      { href: "/analytics", label: "Analytics", icon: LineChart },
      { href: "/assets", label: "Assets", icon: FolderKanban },
      { href: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const state = useCareerStore((s) => s.state);
  const setUi = useCareerStore((s) => s.setUi);
  const collapsed = state.ui.sidebarCollapsed;
  const phase = derivePhase(state);
  const readiness = useMemo(() => computeReadiness(state), [state]);
  const notes = deriveNotifications(state);
  const palette = useCommandPalette();
  const [quick, setQuick] = useState(false);
  const [backup, setBackup] = useState(false);

  return (
    <div className="min-h-screen">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <div className="flex min-h-screen">
        <aside
          className={cn(
            "sticky top-0 hidden h-screen shrink-0 flex-col border-r border-white/[0.07] bg-[#0b111c]/90 backdrop-blur-xl md:flex",
            "transition-[width] duration-200 ease-out",
            collapsed ? "w-[76px]" : "w-[236px]",
          )}
        >
          <div className={cn("flex items-center gap-2.5 px-3 py-4", collapsed && "justify-center")}>
            <div className="grid h-8 w-8 place-items-center rounded-[10px] bg-gradient-to-br from-emerald-400 to-cyan-400 text-[11px] font-bold text-slate-950 shadow-[0_0_20px_rgb(34_211_238_/_0.25)]">
              OS
            </div>
            {!collapsed ? (
              <div className="min-w-0">
                <div className="truncate text-[13px] font-semibold tracking-tight">{APP_NAME}</div>
                <div className="text-[11px] tracking-wide text-slate-500">Mission Control</div>
              </div>
            ) : null}
          </div>
          <nav className="flex-1 space-y-3 overflow-y-auto px-2 pb-4 scrollbar-thin" aria-label="Primary">
            {NAV_GROUPS.map((group) => (
              <div key={group.label}>
                {!collapsed ? (
                  <p className="px-2.5 pb-1 text-[10px] font-medium tracking-[0.16em] text-slate-500 uppercase">
                    {group.label}
                  </p>
                ) : null}
                <div className="space-y-0.5">
                  {group.items.map((item) => {
                    const active =
                      item.href === "/dashboard"
                        ? pathname === "/" || pathname.startsWith("/dashboard")
                        : pathname === item.href || pathname.startsWith(`${item.href}/`);
                    const Icon = item.icon;
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={cn(
                          "group relative flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-[13px] text-slate-400 hover:bg-white/[0.045] hover:text-white",
                          active && "bg-white/[0.06] text-white",
                          collapsed && "justify-center px-0",
                        )}
                        title={item.label}
                      >
                        {active ? (
                          <span className="absolute top-1/2 left-0 h-4 w-0.5 -translate-y-1/2 rounded-full bg-cyan-400" />
                        ) : null}
                        <Icon className={cn("h-4 w-4 shrink-0", active ? "text-cyan-300" : "text-slate-500 group-hover:text-slate-200")} />
                        {!collapsed ? item.label : <span className="sr-only">{item.label}</span>}
                      </Link>
                    );
                  })}
                </div>
              </div>
            ))}
          </nav>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-30 flex h-14 items-center gap-2 border-b border-white/[0.07] bg-[#090d16]/75 px-3 backdrop-blur-xl md:px-5">
            <Button
              variant="ghost"
              size="icon"
              className="hidden md:inline-flex"
              aria-label="Collapse sidebar"
              onClick={() => setUi({ sidebarCollapsed: !collapsed })}
            >
              <PanelLeft className="h-4 w-4" />
            </Button>
            <div className="hidden items-center gap-2 sm:flex">
              <Badge tone="indigo">{phase}</Badge>
              {state.ui.demoMode ? <Badge tone="amber">Demo</Badge> : null}
              {state.ui.privacyMode ? <Badge tone="cyan">Privacy</Badge> : null}
            </div>
            <button
              type="button"
              onClick={() => palette.setOpen(true)}
              className="flex min-w-0 flex-1 items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-1.5 text-left text-[13px] text-slate-500 hover:border-white/18 hover:bg-white/[0.05]"
            >
              <Search className="h-3.5 w-3.5 text-slate-400" />
              <span className="truncate">Search the OS</span>
              <kbd className="ml-auto hidden rounded-md border border-white/10 bg-white/5 px-1.5 py-0.5 font-mono text-[10px] text-slate-400 sm:inline">
                Ctrl K
              </kbd>
            </button>
            <Button size="sm" onClick={() => setQuick(true)}>
              Quick Add
            </Button>
            <SaveStatus />
            <button
              type="button"
              onClick={() => router.push("/dashboard")}
              className="tabular hidden items-center gap-1.5 rounded-lg border border-cyan-400/20 bg-cyan-400/8 px-2 py-1 text-[12px] text-cyan-200 sm:flex"
              title="Transition readiness"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
              {readiness.global}
            </button>
            <Button variant="outline" size="sm" onClick={() => setBackup(true)}>
              Backup
            </Button>
            <Button
              variant={state.ui.privacyMode ? "emerald" : "ghost"}
              size="sm"
              onClick={() => setUi({ privacyMode: !state.ui.privacyMode })}
            >
              Privacy
            </Button>
            <Link
              href="/settings"
              className="rounded-lg p-2 text-slate-400 hover:bg-white/5 hover:text-white"
              aria-label="Settings"
            >
              <Settings className="h-4 w-4" />
            </Link>
          </header>

          {notes.length > 0 ? (
            <div className="border-b border-amber-400/15 bg-amber-500/[0.06] px-4 py-1.5 text-[12px] text-amber-100">
              <span className="font-medium">{notes[0]?.title}</span>
              <span className="text-amber-200/80"> · {notes[0]?.detail}</span>
              {notes.length > 1 ? ` · +${notes.length - 1} more` : ""}
            </div>
          ) : null}

          <main id="main" className="page-enter flex-1 px-3 py-5 pb-24 md:px-7 md:pb-10">
            {children}
          </main>
        </div>
      </div>

      <nav
        className="fixed inset-x-3 bottom-3 z-30 grid grid-cols-5 overflow-hidden rounded-2xl border border-white/10 bg-[#0d1320]/90 shadow-[0_12px_40px_rgb(0_0_0_/_0.35)] backdrop-blur-xl md:hidden"
        aria-label="Mobile"
      >
        {[
          { href: "/dashboard", label: "Home", icon: LayoutDashboard },
          { href: "/today", label: "Today", icon: Sunrise },
          { href: "/jobs", label: "Jobs", icon: Briefcase },
          { href: "/projects", label: "Build", icon: Layers },
          { href: "/settings", label: "More", icon: Settings },
        ].map((item) => {
          const Icon = item.icon;
          const active =
            item.href === "/dashboard"
              ? pathname === "/" || pathname.startsWith("/dashboard")
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center gap-0.5 py-2.5 text-[11px]",
                active ? "text-cyan-300" : "text-slate-400",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <CommandPalette open={palette.open} onOpenChange={palette.setOpen} />
      <QuickAddDialog open={quick} onOpenChange={setQuick} />
      <BackupDialog open={backup} onOpenChange={setBackup} />
    </div>
  );
}
