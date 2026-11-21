"use client";

import { useMemo } from "react";
import { ResumeScoreRing } from "@/components/shared/ResumeScoreRing";
import { calculateResumeScore } from "@/lib/resumeScore";
import { analyzeKeywordMatch } from "@/lib/keywordMatch";
import { getLocalChecklist } from "@/lib/localWorkspace";
import { useResumeStore } from "@/store/resumeStore";

/**
 * Single feedback card: how complete the resume is, what to add next, and —
 * when a job description is pasted — how well it matches.
 */
export function ResumeInsights() {
  const { resume, targetJobDescription } = useResumeStore();

  const score = useMemo(() => calculateResumeScore(resume), [resume]);
  const missingItems = useMemo(
    () => getLocalChecklist(resume).filter((i) => !i.done),
    [resume]
  );
  const keywordMatch = useMemo(
    () => analyzeKeywordMatch(resume, targetJobDescription),
    [resume, targetJobDescription]
  );

  if (score.overall === 0) return null;

  return (
    <div className="premium-card-static space-y-4 p-5">
      <div className="flex items-center gap-4">
        <ResumeScoreRing score={score.overall} />
        <div className="min-w-0">
          <p className="text-[13px] font-semibold text-[#1d1d1f]">Resume score</p>
          {missingItems.length > 0 ? (
            <p className="mt-0.5 text-[12px] leading-relaxed text-[#6e6e73]">
              Add next:{" "}
              {missingItems
                .slice(0, 3)
                .map((i) => i.label.toLowerCase())
                .join(", ")}
              {missingItems.length > 3 && ` +${missingItems.length - 3} more`}
            </p>
          ) : (
            <p className="mt-0.5 text-[12px] text-[#6e6e73]">
              All key sections filled in.
            </p>
          )}
        </div>
      </div>

      {keywordMatch && (
        <div className="border-t border-[#1d1d1f]/[0.06] pt-3">
          <div className="flex items-center justify-between">
            <p className="text-[12px] font-medium text-[#1d1d1f]">
              Job description match
            </p>
            <p className="text-[12px] font-semibold text-[#0071e3]">
              {keywordMatch.matchPercent}%
            </p>
          </div>
          {keywordMatch.missing.length > 0 && (
            <p className="mt-1 text-[11px] leading-relaxed text-[#6e6e73]">
              Not mentioned yet: {keywordMatch.missing.slice(0, 6).join(", ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
