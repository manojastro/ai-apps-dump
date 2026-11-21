import { CircleHelp } from "lucide-react";

import { RiskBadge } from "@/components/badges";
import { Progress } from "@/components/ui/progress";
import { fmtPct } from "@/lib/format";
import type { RiskAssessment } from "@/lib/types";
import { cn } from "@/lib/utils";

const ORDER = ["cvss", "epss", "kev", "asset_criticality", "internet_exposure"];

export function RiskBreakdown({ risk, compact = false }: { risk: RiskAssessment; compact?: boolean }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="text-4xl font-semibold tabular">{risk.score}</div>
        <div className="space-y-1">
          <RiskBadge level={risk.risk_level} />
          <div className="text-xs text-muted-foreground">
            {risk.priority} · business impact {risk.business_impact}
          </div>
        </div>
        <div className="ml-auto text-right text-xs text-muted-foreground">
          <div>Band <span className="tabular text-foreground">{risk.score_lower}–{risk.score_upper}</span></div>
          <div>Coverage <span className="tabular text-foreground">{fmtPct(risk.coverage, 0)}</span></div>
        </div>
      </div>
      <div className="space-y-3">
        {ORDER.filter((k) => risk.factors[k]).map((k) => {
          const f = risk.factors[k];
          return (
            <div key={k}>
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium">{f.label}</span>
                <span className={cn("tabular", !f.available && "text-risk-medium")}>
                  {f.available ? `${f.points} / ${f.max_points}` : `missing / ${f.max_points}`}
                </span>
              </div>
              <Progress value={f.available ? (f.points / f.max_points) * 100 : 0} className={cn("mt-1 h-1.5", !f.available && "opacity-40")} />
              {!compact && (
                <p className="mt-1 flex items-start gap-1 text-[11px] text-muted-foreground">
                  {!f.available && <CircleHelp className="mt-px size-3 shrink-0 text-risk-medium" />}
                  <span>
                    {f.explanation}
                    {f.source && <span className="opacity-70"> · source: {f.source}</span>}
                  </span>
                </p>
              )}
            </div>
          );
        })}
      </div>
      {risk.missing_factors.length > 0 && (
        <p className="rounded-md border border-risk-medium/30 bg-risk-medium/10 px-3 py-2 text-xs">
          Missing data is never scored as zero risk: {risk.missing_factors.join(", ")} imputed per policy. True score lies in{" "}
          {risk.score_lower}–{risk.score_upper}.
        </p>
      )}
      {!compact && <p className="font-mono text-[10px] text-muted-foreground">policy {risk.policy_version}</p>}
    </div>
  );
}
