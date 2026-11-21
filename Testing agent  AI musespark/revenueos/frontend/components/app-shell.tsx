"use client";

import {
  Bot,
  Building2,
  HeartPulse,
  LayoutDashboard,
  LogOut,
  Moon,
  Settings2,
  Sun,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ThemeProvider, useTheme } from "next-themes";
import { type ReactNode, createContext, useContext, useEffect, useState } from "react";

import { SourceDrawerProvider } from "@/components/citations";
import { Button } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";
import { cn, titleCase } from "@/lib/utils";

const UserContext = createContext<User | null>(null);
export const useUser = () => useContext(UserContext);

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/deals", label: "Deals", icon: TrendingUp },
  { href: "/accounts", label: "Accounts", icon: Building2 },
  { href: "/retention", label: "Retention", icon: HeartPulse },
  { href: "/copilot", label: "Copilot", icon: Bot },
  { href: "/admin", label: "Admin", icon: Settings2, roles: ["admin", "revops"] },
];

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const dark = mounted && resolvedTheme === "dark";
  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
      onClick={() => setTheme(dark ? "light" : "dark")}
    >
      {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </Button>
  );
}

function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const isLogin = pathname === "/login";

  useEffect(() => {
    if (isLogin) return;
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => router.replace("/login"));
  }, [isLogin, router]);

  if (isLogin) return <>{children}</>;
  if (!user) return <div className="min-h-screen bg-background" />;

  const logout = async () => {
    await api("/auth/logout", { method: "POST" });
    window.location.href = "/login";
  };

  return (
    <UserContext.Provider value={user}>
      <SourceDrawerProvider>
        <div className="flex min-h-screen">
          <aside className="sticky top-0 flex h-screen w-56 shrink-0 flex-col border-r bg-card">
            <div className="flex items-center gap-2 px-4 py-4">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-xs font-bold text-primary-foreground">
                R
              </div>
              <span className="text-sm font-semibold tracking-tight">RevenueOS</span>
            </div>
            <nav className="flex-1 space-y-0.5 px-2" aria-label="Main">
              {NAV.filter((item) => !item.roles || item.roles.includes(user.role)).map((item) => {
                const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm",
                      active ? "bg-accent font-medium text-accent-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground",
                    )}
                  >
                    <item.icon className="h-4 w-4" aria-hidden />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
            <div className="border-t p-3">
              <p className="truncate text-sm font-medium">{user.full_name}</p>
              <p className="truncate text-xs text-muted-foreground">
                {titleCase(user.role)}
                {user.team_name ? ` · ${user.team_name}` : " · All teams"}
              </p>
              <div className="mt-2 flex items-center gap-1">
                <ThemeToggle />
                <Button variant="ghost" size="icon" aria-label="Sign out" onClick={logout}>
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </aside>
          <main className="min-w-0 flex-1 p-6">
            <div className="mx-auto max-w-7xl">{children}</div>
          </main>
        </div>
      </SourceDrawerProvider>
    </UserContext.Provider>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <Shell>{children}</Shell>
    </ThemeProvider>
  );
}
