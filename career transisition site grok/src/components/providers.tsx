"use client";

import { useEffect } from "react";
import { Toaster } from "sonner";
import { OnboardingGate } from "@/components/overlays/onboarding";
import { RecoveryMode } from "@/components/overlays/recovery-mode";
import { AppShell } from "@/components/shell/app-shell";
import { useCareerStore } from "@/store/career-store";

export function Providers({ children }: { children: React.ReactNode }) {
  const hydrate = useCareerStore((s) => s.hydrate);
  const hydrated = useCareerStore((s) => s.hydrated);

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  if (!hydrated) {
    return (
      <div className="grid min-h-screen place-items-center">
        <div className="flex flex-col items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-400 text-[12px] font-bold text-slate-950">
            OS
          </div>
          <p className="text-[13px] tracking-wide text-slate-400">Loading mission control…</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <RecoveryMode />
      <OnboardingGate />
      <AppShell>{children}</AppShell>
      <Toaster theme="dark" position="bottom-right" toastOptions={{ className: "border-white/10 bg-[#0d1320] text-slate-100" }} />
    </>
  );
}
