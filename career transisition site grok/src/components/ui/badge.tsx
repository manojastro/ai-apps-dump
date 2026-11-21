import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

const tones: Record<string, string> = {
  green: "bg-emerald-500/12 text-emerald-300 border-emerald-400/20",
  cyan: "bg-cyan-500/12 text-cyan-300 border-cyan-400/20",
  amber: "bg-amber-500/12 text-amber-200 border-amber-400/20",
  red: "bg-rose-500/12 text-rose-300 border-rose-400/20",
  indigo: "bg-indigo-500/12 text-indigo-300 border-indigo-400/20",
  slate: "bg-white/4 text-slate-300 border-white/10",
};

export function Badge({
  children,
  tone = "slate",
  className,
}: {
  children: ReactNode;
  tone?: keyof typeof tones | string;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium tracking-wide uppercase",
        tones[tone] ?? tones.slate,
        className,
      )}
    >
      {children}
    </span>
  );
}

export function StatusBadge({ value }: { value: string }) {
  const map: Record<string, string> = {
    mastered: "green",
    deployed: "green",
    Offer: "green",
    Certified: "green",
    Passed: "green",
    Complete: "green",
    in_progress: "cyan",
    Applied: "cyan",
    Screening: "cyan",
    Technical: "cyan",
    Studying: "cyan",
    "In Progress": "cyan",
    Identified: "slate",
    planned: "slate",
    to_learn: "slate",
    Referred: "indigo",
    Overdue: "red",
    Rejected: "red",
    Failed: "red",
    Draft: "amber",
    "Follow-up": "amber",
  };
  return <Badge tone={map[value] ?? "slate"}>{value.replaceAll("_", " ")}</Badge>;
}
