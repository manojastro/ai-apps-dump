import * as React from "react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Field({
  label,
  hint,
  error,
  className,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <label className={cn("block space-y-1.5", className)}>
      <span className="text-[12px] font-medium tracking-wide text-slate-400">{label}</span>
      {children}
      {hint ? <span className="block text-xs text-slate-500">{hint}</span> : null}
      {error ? <span className="block text-xs text-rose-400">{error}</span> : null}
    </label>
  );
}

const control =
  "w-full rounded-lg border border-white/10 bg-[#0b1220] px-3 text-[13px] text-slate-100 placeholder:text-slate-500 hover:border-white/16 focus:border-cyan-400/40 focus:bg-[#0e1628]";

export function Input({ className, ...props }: React.ComponentProps<"input">) {
  return <input className={cn("h-9", control, className)} {...props} />;
}

export function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return <textarea className={cn("min-h-24 py-2", control, className)} {...props} />;
}

export function Select({ className, children, ...props }: React.ComponentProps<"select">) {
  return (
    <select className={cn("h-9", control, className)} {...props}>
      {children}
    </select>
  );
}
