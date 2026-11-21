"use client";
import { type ReactNode, useEffect, useId, useRef } from "react";

type Tone = "ok" | "warn" | "bad" | "info" | "muted" | "brand";

const toneClass: Record<Tone, string> = {
  ok: "bg-ok-bg text-ok border-ok/30",
  warn: "bg-warn-bg text-warn border-warn/30",
  bad: "bg-bad-bg text-bad border-bad/30",
  info: "bg-info-bg text-info border-info/30",
  muted: "bg-bg text-muted border-line",
  brand: "bg-brand text-brand-ink border-brand",
};

export function Badge({ tone = "muted", children, title }: { tone?: Tone; children: ReactNode; title?: string }) {
  return (
    <span title={title} className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-xs font-medium whitespace-nowrap ${toneClass[tone]}`}>
      {children}
    </span>
  );
}

const STATUS_TONE: Record<string, Tone> = {
  pass: "ok", completed: "ok", succeeded: "ok", approved: "ok", ready_for_review: "info", computed: "ok", resolved: "ok",
  fail: "bad", failed: "bad", critical: "bad", rejected: "bad", unsupported: "bad",
  requires_review: "warn", warning: "warn", awaiting_input: "warn", awaiting_confirmation: "warn", partial: "warn",
  special_interpretation: "warn", explained: "info", submitted_for_review: "info", reopened: "warn", draft: "warn",
  insufficient_data: "muted", not_applicable: "muted", info: "info", open: "warn", running: "info", queued: "muted",
  in_preparation: "muted", blocked: "warn", duplicate: "muted", halted: "muted",
};

export function StatusBadge({ status }: { status: string | null | undefined }) {
  const s = status ?? "unknown";
  return <Badge tone={STATUS_TONE[s] ?? "muted"}>{s.replace(/_/g, " ")}</Badge>;
}

export function Card({ title, actions, children, className = "" }: { title?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-lg border border-line bg-panel ${className}`}>
      {(title || actions) && (
        <header className="flex items-center justify-between gap-2 border-b border-line px-4 py-2.5">
          <h2 className="text-sm font-semibold">{title}</h2>
          {actions}
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}

export function Button({ children, variant = "primary", ...rest }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "danger" | "ghost" }) {
  const v = {
    primary: "bg-brand text-brand-ink hover:opacity-90",
    secondary: "border border-line bg-panel hover:bg-bg",
    danger: "bg-bad text-white hover:opacity-90",
    ghost: "hover:bg-bg",
  }[variant];
  return (
    <button {...rest} className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50 ${v} ${rest.className ?? ""}`}>
      {children}
    </button>
  );
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <span role="status" className="inline-flex items-center gap-2 text-sm text-muted">
      <span aria-hidden className="h-3 w-3 animate-spin rounded-full border-2 border-muted border-t-transparent" />
      {label}
    </span>
  );
}

export function Alert({ tone = "info", children }: { tone?: Tone; children: ReactNode }) {
  return <div role={tone === "bad" ? "alert" : "status"} className={`rounded-md border px-3 py-2 text-sm ${toneClass[tone]}`}>{children}</div>;
}

export function Tabs<T extends string>({ tabs, value, onChange, label }: { tabs: { id: T; label: ReactNode }[]; value: T; onChange: (t: T) => void; label: string }) {
  return (
    <div role="tablist" aria-label={label} className="flex gap-1 border-b border-line">
      {tabs.map((t) => (
        <button key={t.id} role="tab" aria-selected={value === t.id} onClick={() => onChange(t.id)}
          onKeyDown={(e) => {
            const i = tabs.findIndex((x) => x.id === value);
            if (e.key === "ArrowRight") onChange(tabs[(i + 1) % tabs.length].id);
            if (e.key === "ArrowLeft") onChange(tabs[(i - 1 + tabs.length) % tabs.length].id);
          }}
          className={`-mb-px border-b-2 px-3 py-2 text-sm ${value === t.id ? "border-brand font-semibold text-ink" : "border-transparent text-muted hover:text-ink"}`}>
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function Drawer({ open, onClose, title, children, wide = false }: { open: boolean; onClose: () => void; title: ReactNode; children: ReactNode; wide?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const id = useId();
  useEffect(() => {
    if (!open) return;
    const prev = document.activeElement as HTMLElement | null;
    ref.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => { window.removeEventListener("keydown", onKey); prev?.focus(); };
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/30" onClick={onClose}>
      <div ref={ref} tabIndex={-1} role="dialog" aria-modal="true" aria-labelledby={id} onClick={(e) => e.stopPropagation()}
        className={`h-full overflow-y-auto border-l border-line bg-panel shadow-xl outline-none ${wide ? "w-full max-w-6xl" : "w-full max-w-xl"}`}>
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-line bg-panel px-4 py-3">
          <h2 id={id} className="font-semibold">{title}</h2>
          <Button variant="ghost" onClick={onClose} aria-label="Close panel">✕</Button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-muted">{hint}</span>}
    </label>
  );
}

export const inputClass = "w-full rounded-md border border-line bg-panel px-2.5 py-1.5 text-sm";

export function Kv({ items }: { items: [string, ReactNode][] }) {
  return (
    <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-1 text-sm">
      {items.map(([k, v]) => (
        <div key={k} className="contents">
          <dt className="text-muted">{k}</dt>
          <dd className="break-words">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

export function when(d: string | null | undefined): string {
  if (!d) return "—";
  return new Date(d).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}
