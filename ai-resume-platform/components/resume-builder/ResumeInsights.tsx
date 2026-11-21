"use client";

import { useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ResumeScoreRing } from "@/components/shared/ResumeScoreRing";
import { calculateResumeScore } from "@/lib/resumeScore";
import { analyzeKeywordMatch } from "@/lib/keywordMatch";
import { useResumeStore } from "@/store/resumeStore";

export function ResumeInsights() {
  const { resume, targetJobDescription } = useResumeStore();

  const score = useMemo(() => calculateResumeScore(resume), [resume]);
  const keywordMatch = useMemo(
    () => analyzeKeywordMatch(resume, targetJobDescription),
    [resume, targetJobDescription]
  );

  const hasContent = score.overall > 0;

  if (!hasContent) return null;

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      className="rounded-2xl bg-white p-5 shadow-[0_2px_20px_rgba(0,0,0,0.04)] space-y-4"
    >
      <div className="flex items-center gap-4">
        <ResumeScoreRing score={score.overall} />
        <div>
          <p className="text-[13px] font-semibold text-[#1d1d1f]">Resume score</p>
          <p className="text-[12px] text-[#6e6e73] mt-0.5">
            {score.overall >= 80
              ? "Looking strong"
              : score.overall >= 50
                ? "Good progress"
                : "Keep building"}
          </p>
        </div>
      </div>

      <div className="flex gap-1.5">
        {score.sections.map((s) => (
          <div key={s.label} className="flex-1">
            <div className="h-1 rounded-full bg-[#1d1d1f]/[0.06] overflow-hidden">
              <motion.div
                className="h-full rounded-full bg-[#0071e3]"
                initial={{ width: 0 }}
                animate={{ width: `${s.score}%` }}
                transition={{ duration: 0.8, ease: [0.25, 0.1, 0.25, 1] }}
              />
            </div>
            <p className="text-[10px] text-[#6e6e73] mt-1 truncate">{s.label}</p>
          </div>
        ))}
      </div>

      <AnimatePresence>
        {keywordMatch && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="pt-3 border-t border-[#1d1d1f]/[0.04]"
          >
            <div className="flex items-center justify-between mb-2">
              <p className="text-[12px] font-medium text-[#1d1d1f]">Job match</p>
              <p className="text-[12px] font-semibold text-[#0071e3]">
                {keywordMatch.matchPercent}%
              </p>
            </div>
            {keywordMatch.matched.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-2">
                {keywordMatch.matched.map((kw) => (
                  <span
                    key={kw}
                    className="text-[10px] px-2 py-0.5 rounded-full bg-[#34c759]/10 text-[#248a3d]"
                  >
                    {kw}
                  </span>
                ))}
              </div>
            )}
            {keywordMatch.missing.length > 0 && (
              <p className="text-[11px] text-[#6e6e73]">
                Missing: {keywordMatch.missing.join(", ")}
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {score.tips.length > 0 && (
        <div className="space-y-1.5">
          {score.tips.map((tip) => (
            <p key={tip} className="text-[11px] text-[#6e6e73] flex items-start gap-1.5">
              <span className="text-[#ff9500] shrink-0">→</span> {tip}
            </p>
          ))}
        </div>
      )}
    </motion.div>
  );
}