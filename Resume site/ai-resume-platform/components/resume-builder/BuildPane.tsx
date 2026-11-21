"use client";

import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { useResumeStore } from "@/store/resumeStore";
import { PasteContentTab } from "./PasteContentTab";
import { GuidedChatTab } from "./GuidedChatTab";
import { UploadTab } from "./UploadTab";
import { TemplatePicker } from "./TemplatePicker";
import { ResumeInsights } from "./ResumeInsights";
import { WorkspaceStatus } from "@/components/shared/WorkspaceStatus";
import { fadeOnly, slideDir } from "@/lib/motion";
import { cn } from "@/lib/utils";

const MODES = [
  { value: "paste" as const, label: "Paste" },
  { value: "chat" as const, label: "Guided" },
  { value: "upload" as const, label: "Upload" },
];

export function BuildPane() {
  const { inputMode, setInputMode, resume } = useResumeStore();
  const reduce = useReducedMotion();

  return (
    <div className="space-y-6">
      <div
        role="tablist"
        aria-label="Resume input mode"
        className="inline-flex gap-1 rounded-full bg-[#1d1d1f]/[0.04] p-1"
      >
        {MODES.map((m) => {
          const active = inputMode === m.value;
          return (
            <button
              key={m.value}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => setInputMode(m.value)}
              className={cn(
                "relative z-10 rounded-full px-4 py-2 text-[13px] font-medium transition-colors focus-ring",
                active ? "text-[#1d1d1f]" : "text-[#6e6e73] hover:text-[#1d1d1f]"
              )}
            >
              {active &&
                (reduce ? (
                  <span className="absolute inset-0 rounded-full bg-white shadow-sm" />
                ) : (
                  <motion.span
                    layoutId="build-mode-pill"
                    className="absolute inset-0 rounded-full bg-white shadow-sm"
                    transition={{ type: "spring", stiffness: 400, damping: 34 }}
                  />
                ))}
              <span className="relative z-10">{m.label}</span>
            </button>
          );
        })}
      </div>

      <div className="min-h-[200px]">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={inputMode}
            variants={reduce ? fadeOnly : slideDir(1)}
            initial="initial"
            animate="animate"
            exit="exit"
          >
            {inputMode === "paste" && <PasteContentTab />}
            {inputMode === "chat" && <GuidedChatTab />}
            {inputMode === "upload" && <UploadTab />}
          </motion.div>
        </AnimatePresence>
      </div>

      <ResumeInsights />

      <TemplatePicker />

      <WorkspaceStatus
        watchKey={`${resume.personalInfo.fullName}-${resume.summary?.slice(0, 24)}`}
      />
    </div>
  );
}
