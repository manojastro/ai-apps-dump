import { Badge } from "@/components/ui/badge";
import { titleCase } from "@/lib/format";
import { cn } from "@/lib/utils";

const RISK_STYLES: Record<string, string> = {
  critical: "bg-risk-critical/15 text-risk-critical border-risk-critical/30",
  high: "bg-risk-high/15 text-risk-high border-risk-high/30",
  medium: "bg-risk-medium/15 text-risk-medium border-risk-medium/30",
  low: "bg-risk-low/15 text-risk-low border-risk-low/30",
  none: "bg-muted text-muted-foreground border-border",
  unknown: "bg-risk-unknown/15 text-risk-unknown border-risk-unknown/30",
};

export function RiskBadge({ level, score, className }: { level: string | null | undefined; score?: number | null; className?: string }) {
  const key = level ?? "unknown";
  return (
    <Badge variant="outline" className={cn("gap-1 font-semibold tabular", RISK_STYLES[key] ?? RISK_STYLES.unknown, className)}>
      {score !== undefined && score !== null && <span>{score}</span>}
      <span className="uppercase tracking-wide text-[10px]">{level ?? "unscored"}</span>
    </Badge>
  );
}

export function SeverityBadge({ severity }: { severity: string | null | undefined }) {
  const key = severity ?? "unknown";
  return (
    <Badge variant="outline" className={cn("uppercase tracking-wide text-[10px]", RISK_STYLES[key] ?? RISK_STYLES.unknown)}>
      {key}
    </Badge>
  );
}

export function KevBadge({ kev }: { kev: boolean | null | undefined }) {
  if (kev === true)
    return (
      <Badge variant="outline" className="border-risk-critical/40 bg-risk-critical/15 text-risk-critical text-[10px] font-semibold">
        KEV
      </Badge>
    );
  if (kev === false) return <span className="text-xs text-muted-foreground">No</span>;
  return <span className="text-xs text-muted-foreground" title="KEV status could not be verified">Unknown</span>;
}

const STATUS_TONE: Record<string, string> = {
  good: "bg-risk-low/15 text-risk-low border-risk-low/30",
  warn: "bg-risk-medium/15 text-risk-medium border-risk-medium/30",
  bad: "bg-risk-critical/15 text-risk-critical border-risk-critical/30",
  info: "bg-primary/10 text-primary border-primary/30",
  neutral: "bg-muted text-muted-foreground border-border",
};

const STATUS_MAP: Record<string, keyof typeof STATUS_TONE> = {
  // workflow
  completed: "good", running: "info", queued: "neutral", waiting_approval: "warn", waiting_manual_review: "warn",
  waiting_evidence: "info", waiting_sync_retry: "bad", rejected: "bad", failed: "bad", blocked: "bad", cancelled: "neutral",
  // approvals / plans
  PENDING: "warn", APPROVED: "good", REJECTED: "bad", CHANGES_REQUESTED: "warn", INVALIDATED: "neutral", CANCELLED: "neutral",
  DRAFT: "neutral", ASSESSMENT_COMPLETE: "info", PENDING_APPROVAL: "warn", SUPERSEDED: "neutral",
  SYNC_PENDING: "warn", SYNCED: "good", SYNC_FAILED: "bad", REMEDIATION_IN_PROGRESS: "info", PENDING_VERIFICATION: "info",
  VERIFIED: "good", CLOSED: "good", IMPLEMENTED: "good", NOT_STARTED: "neutral",
  // findings
  open: "warn", in_remediation: "info", remediated: "good", closed: "good",
  verified_remediated: "good", verification_failed: "bad", inconclusive: "warn", pending_rescan: "info",
  verification_in_progress: "info", not_started: "neutral",
  matched: "good", ambiguous: "warn", unmatched: "bad", pending: "neutral",
  // integrations
  Mock: "info", Connected: "good", "Not Configured": "neutral", Error: "bad", Unsupported: "neutral", Unverified: "warn",
  Configured: "info",
  success: "good", error: "bad", denied: "bad", adopted_existing: "info", ok: "good",
};

export function StatusBadge({ status, className, label }: { status: string | null | undefined; className?: string; label?: string }) {
  if (!status) return <span className="text-xs text-muted-foreground">—</span>;
  const tone = STATUS_MAP[status] ?? "neutral";
  return (
    <Badge variant="outline" className={cn("text-[11px] font-medium", STATUS_TONE[tone], className)}>
      {label ?? titleCase(status)}
    </Badge>
  );
}

export function SimBadge({ label = "Simulated" }: { label?: string }) {
  return (
    <Badge variant="outline" className="border-dashed border-primary/40 text-primary text-[10px] uppercase tracking-wider">
      {label}
    </Badge>
  );
}
