import { ReactNode } from "react";
import { Check, X, Database, Server } from "lucide-react";
export function Badge({
  children,
  tone = "",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <span className={`tag ${tone}`}>{children}</span>;
}
export function Status({ value }: { value: string }) {
  return (
    <Badge
      tone={
        [
          "completed",
          "resolved",
          "supported",
          "pass",
          "executed",
          "connected",
          "success",
        ].includes(value)
          ? "good"
          : ["failed", "fail", "error"].includes(value)
            ? "bad"
            : [
                  "awaiting_review",
                  "pending",
                  "inconclusive",
                  "insufficient_evidence",
                  "budget_exceeded",
                  "blocked",
                ].includes(value)
              ? "warn"
              : "info"
      }
    >
      <i className="dot" />
      {value.replaceAll("_", " ")}
    </Badge>
  );
}
export function Panel({
  title,
  extra,
  children,
  note,
}: {
  title: string;
  extra?: ReactNode;
  children: ReactNode;
  note?: string;
}) {
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>{title}</h2>
        {extra}
      </div>
      {children}
      {note && <div className="panel-note">{note}</div>}
    </section>
  );
}
export function Empty({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty">
      <Database size={28} />
      <h3>{title}</h3>
      <p>{description}</p>
      {children}
    </div>
  );
}
export function Modal({
  title,
  onClose,
  children,
  wide = false,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}) {
  return (
    <div
      className="modal-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`modal ${wide ? "wide" : ""}`}
        onKeyDown={(e) => {
          if (e.key === "Escape") onClose();
        }}
      >
        <div className="modal-head">
          <h2>{title}</h2>
          <button
            className="iconbtn"
            aria-label="Close dialog"
            onClick={onClose}
          >
            <X size={20} />
          </button>
        </div>
        <div className="modal-body">{children}</div>
      </section>
    </div>
  );
}
export function Stat({
  label,
  value,
  foot,
  icon,
}: {
  label: string;
  value: ReactNode;
  foot: string;
  icon?: ReactNode;
}) {
  return (
    <div className="stat">
      <div className="stat-label">
        {label}
        {icon}
      </div>
      <div className="stat-value">{value}</div>
      <div className="stat-foot">{foot}</div>
    </div>
  );
}
export function Dependencies() {
  return (
    <div
      className="service-map"
      aria-label="Checkout depends on payment, inventory, and the demo database"
    >
      <div className="service-node focus">
        <Server size={17} style={{ margin: "0 auto 7px" }} />
        Checkout API<small>Customer entry point</small>
      </div>
      <div className="service-edge" />
      <div className="service-children">
        <div className="service-node">
          Payment<small>Upstream dependency</small>
        </div>
        <div className="service-node">
          Inventory<small>Stock availability</small>
        </div>
        <div className="service-node">
          Demo database<small>Isolated storage</small>
        </div>
      </div>
    </div>
  );
}
export function CheckRow({
  pass,
  children,
}: {
  pass: boolean;
  children: ReactNode;
}) {
  return (
    <div className="row" style={{ padding: "8px 0", fontSize: 12 }}>
      {pass ? (
        <Check size={15} className="green" />
      ) : (
        <X size={15} className="amber" />
      )}
      {children}
    </div>
  );
}
export function time(value: number) {
  return new Date(value * 1000).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}
export function relative(value: number) {
  const m = Math.floor((Date.now() / 1000 - value) / 60);
  return m < 1
    ? "Just now"
    : m < 60
      ? `${m}m ago`
      : m < 1440
        ? `${Math.floor(m / 60)}h ago`
        : new Date(value * 1000).toLocaleDateString();
}
