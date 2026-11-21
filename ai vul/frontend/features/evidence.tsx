import { CircleCheck, CircleX } from "lucide-react";

import { fmtDate } from "@/lib/format";
import type { ScanEvidence } from "@/lib/types";

export function EvidenceTimeline({ evidence }: { evidence: ScanEvidence[] }) {
  if (evidence.length === 0) return <p className="text-sm text-muted-foreground">No scan evidence recorded.</p>;
  return (
    <ol className="relative space-y-3 border-l pl-4">
      {evidence.map((e) => (
        <li key={e.id} className="text-sm">
          <span className="absolute -left-[7px] mt-1 grid size-3.5 place-items-center rounded-full bg-background">
            {e.vulnerable ? <CircleX className="size-3.5 text-risk-critical" /> : <CircleCheck className="size-3.5 text-risk-low" />}
          </span>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded bg-muted px-1.5 text-[10px] font-semibold uppercase">{e.kind}</span>
            <span className="font-medium">{e.vulnerable ? "Vulnerable" : "Not detected"}</span>
            <span className="text-xs text-muted-foreground">{fmtDate(e.scanned_at)}</span>
          </div>
          <div className="mt-0.5 text-xs text-muted-foreground">
            {e.scanner} · scan {e.scan_id} · {e.asset_identifier} · {e.software_name ?? "software n/a"} {e.software_version ?? ""}
            {typeof e.raw?.detail === "string" && <div className="mt-0.5">{e.raw.detail}</div>}
          </div>
        </li>
      ))}
    </ol>
  );
}
