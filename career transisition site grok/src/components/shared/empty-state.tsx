import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";

export function EmptyState({
  title,
  detail,
  actionLabel,
  onAction,
}: {
  title: string;
  detail: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div className="card flex flex-col items-start gap-3 p-6">
      <div className="h-1.5 w-10 rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400" />
      <h3 className="text-sm font-semibold tracking-tight text-white">{title}</h3>
      <p className="max-w-xl text-[13px] leading-5 text-slate-400">{detail}</p>
      {actionLabel && onAction ? (
        <Button size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}

export function SectionHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-white">{title}</h1>
        {description ? <p className="mt-1 max-w-2xl text-[13px] leading-5 text-slate-400">{description}</p> : null}
      </div>
      {actions}
    </div>
  );
}

export function ConfirmDialog({
  open,
  title,
  detail,
  confirmLabel = "Confirm",
  onConfirm,
  onClose,
}: {
  open: boolean;
  title: string;
  detail: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onClose: () => void;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4 backdrop-blur-sm">
      <div role="dialog" aria-modal="true" className="card w-full max-w-md p-5">
        <h2 className="text-base font-semibold tracking-tight">{title}</h2>
        <p className="mt-2 text-[13px] leading-5 text-slate-400">{detail}</p>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="danger" onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
