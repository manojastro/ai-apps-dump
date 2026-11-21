import clsx from "clsx";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";
import { ApiError } from "./api";

export function Button({ variant = "primary", className, ...rest }: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger" | "ghost";
}) {
  return (
    <button
      {...rest}
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-md px-3.5 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "bg-brand text-white hover:bg-blue-800",
        variant === "secondary" && "border border-line bg-white text-ink hover:bg-canvas",
        variant === "danger" && "bg-bad text-white hover:bg-red-800",
        variant === "ghost" && "text-brand hover:bg-brand-soft",
        className,
      )}
    />
  );
}

export function Card({ title, actions, children, className }: { title?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={clsx("rounded-lg border border-line bg-panel shadow-sm", className)}>
      {(title || actions) && (
        <header className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
          <h2 className="text-sm font-semibold text-ink">{title}</h2>
          <div className="flex flex-wrap gap-2">{actions}</div>
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}

const tone: Record<string, string> = {
  good: "bg-good-soft text-good",
  bad: "bg-bad-soft text-bad",
  warn: "bg-warn-soft text-warn",
  info: "bg-brand-soft text-brand",
  muted: "bg-canvas text-muted",
};

export function Badge({ kind = "muted", children }: { kind?: keyof typeof tone; children: ReactNode }) {
  return <span className={clsx("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", tone[kind])}>{children}</span>;
}

const statusTone: Record<string, keyof typeof tone> = {
  completed: "good", purchased: "good", reconciled: "good", approved: "good", consumed: "good", submitted: "info",
  running: "info", queued: "muted", awaiting_approval: "warn", pending: "warn", paused_for_human: "warn",
  submitting: "info", reconciling: "info", unknown: "warn", cancellation_requested: "warn",
  failed: "bad", rejected: "bad", invalidated: "bad", expired: "bad", canceled: "muted",
  no_eligible_offer: "bad", needs_clarification: "warn", ok: "good", error: "bad", blocked: "bad", handoff: "warn",
};

export function Status({ value }: { value?: string | null }) {
  if (!value) return <Badge>—</Badge>;
  return <Badge kind={statusTone[value] ?? "muted"}>{value.replaceAll("_", " ")}</Badge>;
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
      </div>
      <div className="flex flex-wrap gap-2">{actions}</div>
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="rounded-md border border-dashed border-line p-6 text-center text-sm text-muted">{children}</div>;
}

export function ErrorBox({ error }: { error: unknown }) {
  if (!error) return null;
  const msg = error instanceof ApiError ? `${error.message} (${error.code})` : String((error as Error)?.message ?? error);
  return <div role="alert" className="rounded-md border border-bad/30 bg-bad-soft px-3 py-2 text-sm text-bad">{msg}</div>;
}

export function Loading({ what = "Loading" }: { what?: string }) {
  return <p className="text-sm text-muted" aria-live="polite">{what}…</p>;
}

export function Field({ label, hint, children, id }: { label: string; hint?: string; children: ReactNode; id: string }) {
  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block text-sm font-medium">{label}</label>
      {children}
      {hint && <p className="text-xs text-muted">{hint}</p>}
    </div>
  );
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={clsx("w-full rounded-md border border-line bg-white px-3 py-2 text-sm", props.className)} />;
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={clsx("w-full rounded-md border border-line bg-white px-3 py-2 text-sm", props.className)} />;
}

export function SyntheticBanner({ simulated }: { simulated?: boolean }) {
  return (
    <div role="note" className="rounded-md border border-warn/30 bg-warn-soft px-3 py-2 text-xs text-warn">
      <strong>Synthetic environment.</strong> Suppliers, prices, tax rates and orders are fixtures; no money moves.
      {simulated && <> Model decisions in this run are <strong>simulated</strong> (deterministic fixture mode).</>}
    </div>
  );
}

export function KV({ items }: { items: [string, ReactNode][] }) {
  return (
    <dl className="grid grid-cols-1 gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
      {items.map(([k, v]) => (
        <div key={k} className="flex justify-between gap-3 border-b border-line/70 py-1">
          <dt className="text-muted">{k}</dt>
          <dd className="text-right font-medium tabular">{v}</dd>
        </div>
      ))}
    </dl>
  );
}
