"use client";

import { AlertCircle, AlertTriangle, CheckCircle2, ChevronLeft, ChevronRight, MinusCircle } from "lucide-react";
import type { ReactNode } from "react";

import { Button, Card, CardContent, Skeleton } from "@/components/ui/primitives";
import type { Reason } from "@/lib/types";
import { cn } from "@/lib/utils";

export function PageHeader({ title, description, children }: { title: string; description?: string; children?: ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        {description && <p className="mt-0.5 text-sm text-muted-foreground">{description}</p>}
      </div>
      {children}
    </div>
  );
}

export function StatTile({ label, value, detail }: { label: string; value: string; detail?: ReactNode }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        <p className="mt-1 text-2xl font-semibold tracking-tight">{value}</p>
        {detail && <div className="mt-1 text-xs text-muted-foreground">{detail}</div>}
      </CardContent>
    </Card>
  );
}

type Tone = "good" | "warning" | "serious" | "critical" | "neutral";

const TONES: Record<Tone, { icon: typeof CheckCircle2; color: string }> = {
  good: { icon: CheckCircle2, color: "var(--status-good)" },
  warning: { icon: AlertTriangle, color: "var(--status-warning)" },
  serious: { icon: AlertTriangle, color: "var(--status-serious)" },
  critical: { icon: AlertCircle, color: "var(--status-critical)" },
  neutral: { icon: MinusCircle, color: "hsl(var(--muted-foreground))" },
};

/** Status always pairs an icon and a word with colour, so it never relies on colour alone. */
export function StatusBadge({ tone, label }: { tone: Tone; label: string }) {
  const { icon: Icon, color } = TONES[tone];
  return (
    <span className="inline-flex items-center gap-1 whitespace-nowrap rounded-full border bg-card px-2 py-0.5 text-xs font-medium">
      <Icon className="h-3.5 w-3.5" style={{ color }} aria-hidden />
      {label}
    </span>
  );
}

export function DealBand({ band }: { band: string | null }) {
  if (band === "at_risk") return <StatusBadge tone="critical" label="At risk" />;
  if (band === "watch") return <StatusBadge tone="warning" label="Watch" />;
  if (band === "healthy") return <StatusBadge tone="good" label="Healthy" />;
  return <StatusBadge tone="neutral" label="Not scored" />;
}

export function ChurnBand({ band }: { band: string | null }) {
  if (band === "high") return <StatusBadge tone="critical" label="High" />;
  if (band === "medium") return <StatusBadge tone="warning" label="Medium" />;
  if (band === "low") return <StatusBadge tone="good" label="Low" />;
  return <StatusBadge tone="neutral" label="Not scored" />;
}

export function HealthBadge({ status }: { status: string | null }) {
  if (status === "green") return <StatusBadge tone="good" label="Healthy" />;
  if (status === "yellow") return <StatusBadge tone="warning" label="Watch" />;
  if (status === "red") return <StatusBadge tone="critical" label="Poor" />;
  return <StatusBadge tone="neutral" label="Unknown" />;
}

export function ReasonChips({ reasons, limit = 3 }: { reasons: Reason[]; limit?: number }) {
  if (!reasons.length) return <span className="text-xs text-muted-foreground">No clear driver</span>;
  return (
    <div className="flex flex-wrap gap-1">
      {reasons.slice(0, limit).map((reason) => (
        <span
          key={reason.feature}
          className={cn(
            "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-xs",
            reason.direction === "risk" ? "bg-muted" : "bg-card",
          )}
        >
          <span aria-hidden>{reason.direction === "risk" ? "▼" : "▲"}</span>
          <span className="sr-only">{reason.direction === "risk" ? "Risk:" : "Positive:"}</span>
          {reason.text}
        </span>
      ))}
    </div>
  );
}

export function Meter({ value }: { value: number | null }) {
  if (value === null) return <span className="text-muted-foreground">-</span>;
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full" style={{ width: `${value * 100}%`, background: "var(--series-1)" }} />
      </div>
      <span className="tabular-nums">{(value * 100).toFixed(0)}%</span>
    </div>
  );
}

export function Pagination({
  page,
  pageSize,
  total,
  onPage,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPage: (page: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="flex items-center justify-between gap-3 px-3 py-2 text-xs text-muted-foreground">
      <span>
        {total.toLocaleString()} result{total === 1 ? "" : "s"}
      </span>
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon" aria-label="Previous page" disabled={page <= 1} onClick={() => onPage(page - 1)}>
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span>
          Page {page} of {pages}
        </span>
        <Button variant="ghost" size="icon" aria-label="Next page" disabled={page >= pages} onClick={() => onPage(page + 1)}>
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

export function LoadingBlock({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2 p-3" role="status" aria-label="Loading">
      {Array.from({ length: rows }, (_, i) => (
        <Skeleton key={i} className="h-8 w-full" />
      ))}
    </div>
  );
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-2 rounded-md border p-3 text-sm" role="alert">
      <AlertCircle className="h-4 w-4 shrink-0" style={{ color: "var(--status-critical)" }} aria-hidden />
      {message}
    </div>
  );
}

export function EmptyNote({ message }: { message: string }) {
  return <p className="p-6 text-center text-sm text-muted-foreground">{message}</p>;
}
