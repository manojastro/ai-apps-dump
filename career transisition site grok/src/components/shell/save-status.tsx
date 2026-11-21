"use client";

import { useCareerStore } from "@/store/career-store";

export function SaveStatus() {
  const status = useCareerStore((s) => s.saveStatus);
  const error = useCareerStore((s) => s.lastError);
  const label = status === "saving" ? "Saving" : status === "failed" ? "Save failed" : status === "saved" ? "Saved" : "";
  const color = status === "failed" ? "text-rose-300" : status === "saving" ? "text-amber-300" : "text-slate-500";
  if (!label) return null;
  return (
    <span className={`hidden items-center gap-1.5 text-[11px] tracking-wide sm:inline-flex ${color}`} title={error ?? ""}>
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          status === "failed" ? "bg-rose-400" : status === "saving" ? "animate-[pulse-soft_1.2s_ease-in-out_infinite] bg-amber-400" : "bg-emerald-400/80"
        }`}
      />
      {label}
    </span>
  );
}
