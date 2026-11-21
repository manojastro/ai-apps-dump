"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  BrainCircuit,
  ChartColumn,
  FlaskConical,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Plug,
  Radar,
  ScrollText,
  Server,
  Settings,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Sun,
  Ticket,
  Workflow,
  Wrench,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import { useState } from "react";

import { AssistantPanel } from "@/components/assistant-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { useMe } from "@/hooks/use-me";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/vulnerabilities", label: "Vulnerabilities", icon: ShieldAlert },
  { href: "/assets", label: "Assets & CMDB", icon: Server },
  { href: "/investigations", label: "AI Investigations", icon: BrainCircuit },
  { href: "/remediation", label: "Remediation Plans", icon: Wrench },
  { href: "/approvals", label: "Approval Center", icon: ShieldCheck, badgeKey: "pending_approvals" as const },
  { href: "/servicenow", label: "ServiceNow", icon: Ticket, badgeKey: "sync_failures" as const },
  { href: "/threat-intel", label: "Threat Intelligence", icon: Radar },
  { href: "/workflows", label: "Agent Workflows", icon: Workflow },
  { href: "/analytics", label: "Analytics", icon: ChartColumn },
  { href: "/evaluation", label: "AI Evaluation", icon: FlaskConical },
  { href: "/audit", label: "Audit Logs", icon: ScrollText },
  { href: "/integrations", label: "Integrations", icon: Plug },
  { href: "/settings", label: "Settings", icon: Settings },
];

function Brand() {
  return (
    <Link href="/dashboard" className="flex items-center gap-2.5 px-2">
      <span className="grid size-8 place-items-center rounded-lg bg-primary/15 text-primary">
        <ShieldCheck className="size-4.5" />
      </span>
      <span className="leading-tight">
        <span className="block text-sm font-semibold tracking-tight">AegisRemediate AI</span>
        <span className="block text-[10px] text-muted-foreground">Human-controlled remediation</span>
      </span>
    </Link>
  );
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { data } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.get<{ kpis: Record<string, number> }>("/dashboard"),
    refetchInterval: 30_000,
  });
  return (
    <nav className="space-y-0.5" aria-label="Main">
      {NAV.map((item) => {
        const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
        const count = item.badgeKey ? data?.kpis[item.badgeKey] : undefined;
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm transition-colors",
              active ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground" : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60",
            )}
          >
            <item.icon className={cn("size-4", active ? "text-primary" : "opacity-70")} />
            <span className="flex-1 truncate">{item.label}</span>
            {count ? (
              <span className={cn("rounded px-1.5 text-[10px] font-semibold tabular", item.badgeKey === "sync_failures" ? "bg-risk-critical/20 text-risk-critical" : "bg-primary/15 text-primary")}>
                {count}
              </span>
            ) : null}
          </Link>
        );
      })}
    </nav>
  );
}

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  return (
    <Button variant="ghost" size="icon" aria-label="Toggle theme" onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}>
      <Sun className="hidden dark:block" />
      <Moon className="dark:hidden" />
    </Button>
  );
}

function UserMenu() {
  const { data: me } = useMe();
  const logout = async () => {
    await api.post("/auth/logout").catch(() => undefined);
    window.location.href = "/login";
  };
  if (!me) return <div className="h-8 w-24 animate-pulse rounded bg-muted" />;
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-9 gap-2 px-2">
          <span className="grid size-7 place-items-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
            {me.full_name.split(" ").map((p) => p[0]).join("").slice(0, 2)}
          </span>
          <span className="hidden text-left leading-tight sm:block">
            <span className="block text-xs font-medium">{me.full_name}</span>
            <span className="block text-[10px] capitalize text-muted-foreground">{me.role}</span>
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-60">
        <DropdownMenuLabel>
          <div className="text-sm">{me.full_name}</div>
          <div className="text-xs font-normal text-muted-foreground">{me.email}</div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">
          Role: <span className="capitalize text-foreground">{me.role}</span> · {me.permissions.length} permissions
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={logout}>
          <LogOut /> Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function EnvironmentBadge() {
  const { data } = useQuery({
    queryKey: ["health-ready"],
    queryFn: () => api.get<{ servicenow_mode: string; ai_provider: string; threat_intel_mode: string }>("/health/ready"),
    staleTime: 300_000,
  });
  if (!data) return null;
  const simulated = data.servicenow_mode === "mock" || data.ai_provider === "mock";
  return (
    <Badge variant="outline" className={cn("hidden gap-1.5 text-[11px] md:inline-flex", simulated ? "border-dashed border-primary/40 text-primary" : "")}>
      <Activity className="size-3" />
      {simulated ? "Simulation environment" : "Live integrations"} · AI {data.ai_provider} · SN {data.servicenow_mode} · Intel {data.threat_intel_mode}
    </Badge>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [assistantOpen, setAssistantOpen] = useState(false);
  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r bg-sidebar py-4 lg:flex">
        <Brand />
        <div className="mt-6 flex-1 overflow-y-auto px-2">
          <NavLinks />
        </div>
        <div className="px-4 pt-3 text-[10px] leading-relaxed text-muted-foreground">
          Northstar Global Technologies · synthetic enterprise. No infrastructure is changed by this platform.
        </div>
      </aside>
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="w-64 bg-sidebar p-4">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <Brand />
          <div className="mt-6">
            <NavLinks onNavigate={() => setMobileOpen(false)} />
          </div>
        </SheetContent>
      </Sheet>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-14 items-center gap-2 border-b bg-background/85 px-4 backdrop-blur">
          <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open navigation" onClick={() => setMobileOpen(true)}>
            <Menu />
          </Button>
          <EnvironmentBadge />
          <div className="flex-1" />
          <Button variant="outline" size="sm" onClick={() => setAssistantOpen(true)}>
            <Sparkles className="text-primary" /> <span className="hidden sm:inline">Ask Aegis</span>
          </Button>
          <ThemeToggle />
          <UserMenu />
        </header>
        <main className="mx-auto w-full max-w-[1500px] flex-1 px-4 py-6 sm:px-6">{children}</main>
      </div>
      <AssistantPanel open={assistantOpen} onOpenChange={setAssistantOpen} />
    </div>
  );
}
