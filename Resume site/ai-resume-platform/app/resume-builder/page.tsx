"use client";

import { cn } from "@/lib/utils";
import { useResumeStore } from "@/store/resumeStore";
import { PageHero } from "@/components/shared/PageHero";
import { SetupBanner } from "@/components/shared/SetupBanner";
import { ModuleBridge } from "@/components/shared/ModuleBridge";
import { MotionPage } from "@/components/shared/MotionPage";
import { BuildPane } from "@/components/resume-builder/BuildPane";
import { PreviewPane } from "@/components/resume-builder/PreviewPane";

export default function ResumeBuilderPage() {
  const { mobilePane, setMobilePane } = useResumeStore();

  return (
    <MotionPage className="mx-auto max-w-5xl px-6 pb-24 pt-10">
      <PageHero
        title="Your resume."
        subtitle="Add your experience, let AI structure it, download an ATS-ready .docx."
      />

      <SetupBanner context="resume" />

      {/* Mobile only: the two panes don't fit side by side */}
      <div className="sticky top-14 z-40 -mx-6 mb-8 flex gap-1 border-b border-black/[0.04] bg-[#fbfbfd]/90 px-6 py-2 backdrop-blur-xl md:hidden">
        {(["build", "preview"] as const).map((pane) => (
          <button
            key={pane}
            type="button"
            className={cn(
              "flex-1 rounded-full py-1.5 text-[13px] font-medium capitalize transition-colors",
              mobilePane === pane
                ? "bg-[#1d1d1f]/[0.06] text-[#1d1d1f]"
                : "text-[#6e6e73]"
            )}
            onClick={() => setMobilePane(pane)}
          >
            {pane}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 items-start gap-10 md:grid-cols-2 md:gap-14">
        <div className={cn(mobilePane !== "build" && "hidden md:block")}>
          <BuildPane />
        </div>
        <div
          className={cn(
            "md:sticky md:top-20",
            mobilePane !== "preview" && "hidden md:block"
          )}
        >
          <PreviewPane />
        </div>
      </div>

      <ModuleBridge
        title="See what's hiring."
        description="Domain demand, market questions, and open roles across India."
        href="/job-trends"
        cta="View job trends"
      />
    </MotionPage>
  );
}
