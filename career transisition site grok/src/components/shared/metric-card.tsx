"use client";

import { useId, type ReactNode } from "react";
import { cn } from "@/lib/utils";

export function MetricCard({
  label,
  value,
  hint,
  tone = "cyan",
  trust,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: "cyan" | "emerald" | "indigo" | "amber";
  trust?: "Fact" | "Derived" | "Recommendation";
}) {
  const wash = {
    cyan: "from-cyan-400/14 via-transparent to-transparent",
    emerald: "from-emerald-400/14 via-transparent to-transparent",
    indigo: "from-indigo-400/14 via-transparent to-transparent",
    amber: "from-amber-400/14 via-transparent to-transparent",
  }[tone];
  const valueColor = {
    cyan: "text-cyan-200",
    emerald: "text-emerald-200",
    indigo: "text-indigo-200",
    amber: "text-amber-200",
  }[tone];
  return (
    <div className={cn("card relative overflow-hidden p-4")}>
      <div className={cn("pointer-events-none absolute inset-0 bg-gradient-to-br", wash)} />
      <div className="relative">
        <div className="flex items-center justify-between gap-2">
          <p className="text-[11px] font-medium tracking-[0.14em] text-slate-400 uppercase">{label}</p>
          {trust ? <span className="text-[10px] text-slate-500">{trust}</span> : null}
        </div>
        <p className={cn("tabular mt-2 text-[28px] leading-none font-semibold", valueColor)}>{value}</p>
        {hint ? <p className="mt-2 text-[12px] leading-4 text-slate-400">{hint}</p> : null}
      </div>
    </div>
  );
}

export function ProgressBar({ value, label }: { value: number; label?: string }) {
  const v = Math.max(0, Math.min(100, value));
  return (
    <div>
      {label ? (
        <div className="mb-1.5 flex justify-between text-[12px] text-slate-400">
          <span>{label}</span>
          <span className="tabular text-slate-200">{Math.round(v)}</span>
        </div>
      ) : null}
      <div className="h-1.5 overflow-hidden rounded-full bg-white/8">
        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400"
          style={{ width: `${v}%`, transition: "width 500ms cubic-bezier(0.22, 1, 0.36, 1)" }}
        />
      </div>
    </div>
  );
}

export function ProgressRing({ value, size = 88, label }: { value: number; size?: number; label?: string }) {
  const v = Math.max(0, Math.min(100, value));
  const r = (size - 12) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (v / 100) * c;
  const gid = useId().replace(/:/g, "");
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="rgba(148,163,184,0.14)" strokeWidth="7" fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke={`url(#${gid})`}
          strokeWidth="7"
          fill="none"
          strokeDasharray={c}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 600ms cubic-bezier(0.22, 1, 0.36, 1)" }}
        />
        <defs>
          <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#34d399" />
            <stop offset="100%" stopColor="#22d3ee" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute text-center">
        <div className="tabular text-xl font-semibold tracking-tight">{Math.round(v)}</div>
        {label ? <div className="text-[10px] tracking-wide text-slate-400 uppercase">{label}</div> : null}
      </div>
    </div>
  );
}

export function CompensationTrack({
  baseline,
  floor,
  target,
  stretch,
  privacy,
}: {
  baseline: number;
  floor: number;
  target: number;
  stretch: number;
  privacy?: boolean;
}) {
  const max = Math.max(stretch, target, floor, baseline, 1);
  const mark = (n: number) => `${(n / max) * 100}%`;
  const fmt = (n: number) => (privacy ? "₹••" : `₹${n}L`);
  return (
    <div>
      <div className="relative mt-3 h-2 rounded-full bg-white/8">
        <div
          className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-slate-500/70 via-cyan-400/80 to-emerald-400"
          style={{ width: mark(target) }}
        />
        {[
          { n: baseline, label: "Now" },
          { n: floor, label: "Floor" },
          { n: target, label: "Target" },
          { n: stretch, label: "Stretch" },
        ].map((m) => (
          <span
            key={m.label}
            className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#111827] bg-white"
            style={{ left: mark(m.n) }}
            title={`${m.label} ${fmt(m.n)}`}
          />
        ))}
      </div>
      <div className="mt-3 grid grid-cols-4 gap-1 text-[11px] text-slate-400">
        <span>
          {fmt(baseline)}
          <span className="block text-slate-500">Current</span>
        </span>
        <span>
          {fmt(floor)}
          <span className="block text-slate-500">Floor</span>
        </span>
        <span>
          {fmt(target)}
          <span className="block text-slate-500">Target</span>
        </span>
        <span className="text-right">
          {fmt(stretch)}
          <span className="block text-slate-500">Stretch</span>
        </span>
      </div>
    </div>
  );
}
