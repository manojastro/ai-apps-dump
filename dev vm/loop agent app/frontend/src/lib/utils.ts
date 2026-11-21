import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function fmtPct(n: number | undefined) {
  if (n == null || Number.isNaN(n)) return "—";
  return `${Math.round(n * 10) / 10}%`;
}

export function fmtSec(n: number | undefined) {
  if (n == null) return "—";
  if (n < 60) return `${Math.round(n)} sec`;
  return `${Math.round(n / 60)}m ${Math.round(n % 60)}s`;
}

export function fmtTime(iso?: string | null) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function statusTone(status?: string) {
  const s = (status || "").toUpperCase();
  if (["HEALTHY", "SUCCESS", "RESOLVED", "PASSED", "CONFIRMED"].includes(s))
    return "text-emerald-400 bg-emerald-400/10 border-emerald-400/20";
  if (["WARNING", "WAITING", "WAITING_APPROVAL"].includes(s))
    return "text-amber-300 bg-amber-400/10 border-amber-400/20";
  if (["FAILED", "CRITICAL", "BLOCKED", "REJECTED"].includes(s))
    return "text-rose-400 bg-rose-400/10 border-rose-400/20";
  if (["RUNNING", "INVESTIGATING", "REMEDIATING", "RECOVERING"].includes(s))
    return "text-sky-300 bg-sky-400/10 border-sky-400/20";
  if (["HUMAN_REVIEW_REQUIRED", "HIGH"].includes(s))
    return "text-orange-300 bg-orange-400/10 border-orange-400/20";
  return "text-zinc-300 bg-zinc-400/10 border-zinc-400/20";
}
