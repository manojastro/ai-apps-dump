"use client";

import { useCallback, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { ArrowDownToLine, RefreshCw, Columns2, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { Skeleton } from "@/components/ui/skeleton";
import { ShimmerOverlay } from "@/components/shared/ShimmerOverlay";
import { TemplateRenderer } from "@/components/resume-templates/TemplateRenderer";
import { getTemplate } from "@/lib/templates";
import { isResumeDownloadable } from "@/lib/resumeSchema";
import { useResumeStore } from "@/store/resumeStore";
import { useToastStore } from "@/store/toastStore";
import { fadeOnly } from "@/lib/motion";

export function PreviewPane() {
  const {
    resume,
    previousResume,
    templateId,
    isEnhancing,
    enhanceError,
    showCompare,
    setShowCompare,
    setEnhanceError,
  } = useResumeStore();
  const addToast = useToastStore((s) => s.addToast);
  const style = getTemplate(templateId);
  const canDownload = isResumeDownloadable(resume);
  const displayResume = showCompare && previousResume ? previousResume : resume;
  const reduce = useReducedMotion();
  const [dlSuccess, setDlSuccess] = useState(false);
  const [dlLoading, setDlLoading] = useState(false);

  const empty =
    !resume.personalInfo.fullName &&
    !resume.summary &&
    resume.experience.length === 0;

  const handleDownload = useCallback(async () => {
    setDlLoading(true);
    setDlSuccess(false);
    try {
      const res = await fetch("/api/resume/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume, templateId }),
      });
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${resume.personalInfo.fullName || "Resume"}_Resume.docx`;
      a.click();
      URL.revokeObjectURL(url);
      setDlSuccess(true);
      addToast("Resume downloaded successfully", "success");
    } catch {
      addToast("Download failed. Try again.", "error");
    } finally {
      setDlLoading(false);
    }
  }, [resume, templateId, addToast]);

  return (
    <div className="flex flex-col">
      <div className="mb-4 flex items-center justify-between px-1">
        <div className="flex items-center gap-3">
          <span className="section-label">Preview</span>
          {previousResume && (
            <button
              type="button"
              onClick={() => setShowCompare(!showCompare)}
              className={`flex items-center gap-1 text-[11px] font-medium transition-colors ${
                showCompare
                  ? "text-[#0071e3]"
                  : "text-[#6e6e73] hover:text-[#1d1d1f]"
              }`}
            >
              <Columns2 className="h-3 w-3" />
              {showCompare ? "Showing before" : "Compare"}
            </button>
          )}
        </div>
        <LoadingButton
          onClick={handleDownload}
          disabled={!canDownload}
          loading={dlLoading}
          success={dlSuccess}
          successLabel="Downloaded"
          size="sm"
          variant={canDownload ? "default" : "secondary"}
          icon={<ArrowDownToLine className="h-3.5 w-3.5" />}
          iconHoverShift="down"
        >
          .docx
        </LoadingButton>
      </div>

      <div className="document-preview relative min-h-[620px] overflow-hidden">
        {isEnhancing && <ShimmerOverlay />}

        {isEnhancing ? (
          <div className="space-y-4 p-12">
            <Skeleton className="mx-auto h-6 w-36 rounded-full" />
            <Skeleton className="mx-auto h-3 w-48 rounded-full" />
            <div className="space-y-2.5 pt-6">
              <Skeleton className="h-2.5 w-full rounded-full" />
              <Skeleton className="h-2.5 w-full rounded-full" />
              <Skeleton className="h-2.5 w-2/3 rounded-full" />
            </div>
          </div>
        ) : enhanceError ? (
          <div className="flex min-h-[400px] flex-col items-center justify-center p-12 text-center">
            <p className="mb-6 text-[15px] leading-relaxed text-[#6e6e73]">
              {enhanceError}
            </p>
            <Button
              variant="ghost"
              onClick={() => {
                setEnhanceError(null);
                addToast("Use Enhance in the Build panel to retry", "info");
              }}
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Try again
            </Button>
          </div>
        ) : empty ? (
          <div className="flex min-h-[400px] flex-col items-center justify-center p-10 text-center">
            <FileText
              className="mb-4 h-7 w-7 text-[#6e6e73]/50"
              strokeWidth={1.5}
            />
            <p className="text-[15px] font-medium text-[#1d1d1f]">
              Your preview appears here
            </p>
            <p className="mt-1.5 max-w-xs text-[13px] leading-relaxed text-[#6e6e73]">
              It updates as you add content.
            </p>
          </div>
        ) : (
          <AnimatePresence mode="wait">
            <motion.div
              key={`${templateId}-${showCompare ? "before" : "after"}-${resume.personalInfo.fullName}`}
              variants={reduce ? fadeOnly : undefined}
              initial={reduce ? "initial" : { opacity: 0 }}
              animate={reduce ? "animate" : { opacity: 1 }}
              exit={reduce ? "exit" : { opacity: 0 }}
              transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
            >
              <TemplateRenderer data={displayResume} style={style} />
            </motion.div>
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
