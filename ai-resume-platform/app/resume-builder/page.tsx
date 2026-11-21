"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useResumeStore } from "@/store/resumeStore";
import { PageHero } from "@/components/shared/PageHero";
import { SetupBanner } from "@/components/shared/SetupBanner";
import { ModuleBridge } from "@/components/shared/ModuleBridge";
import { BuildPane } from "@/components/resume-builder/BuildPane";
import { PreviewPane } from "@/components/resume-builder/PreviewPane";

export default function ResumeBuilderPage() {
  const { mobilePane, setMobilePane } = useResumeStore();

  return (
    <div className="mx-auto max-w-5xl px-6 pb-24 pt-8 md:pt-12">
      <SetupBanner context="resume" />

      <PageHero
        title="Your resume."
        subtitle="ATS-ready. AI-enhanced. Download in seconds."
      />

      <div className="md:hidden flex justify-center gap-6 mb-8 sticky top-12 z-40 glass-nav py-3 -mx-6 px-6">
        {(["build", "preview"] as const).map((pane) => (
          <button
            key={pane}
            className={cn(
              "text-[12px] font-medium tracking-wide capitalize transition-opacity duration-300",
              mobilePane === pane ? "text-[#1d1d1f] opacity-100" : "text-[#1d1d1f] opacity-35"
            )}
            onClick={() => setMobilePane(pane)}
          >
            {pane}
          </button>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 32 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.15, ease: [0.25, 0.1, 0.25, 1] }}
        className="grid grid-cols-1 md:grid-cols-2 gap-10 md:gap-16 items-start"
      >
        <div className={cn(mobilePane !== "build" && "hidden md:block")}>
          <BuildPane />
        </div>
        <div className={cn("md:sticky md:top-20", mobilePane !== "preview" && "hidden md:block")}>
          <PreviewPane />
        </div>
      </motion.div>

      <ModuleBridge
        title="See what's hiring."
        description="Explore live job trends and CTC data across India."
        href="/job-trends"
        cta="View job trends"
      />
    </div>
  );
}