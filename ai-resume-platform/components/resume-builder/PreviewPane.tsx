"use client";

import { useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowDownToLine, RefreshCw, Columns2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ShimmerOverlay } from "@/components/shared/ShimmerOverlay";
import { TemplateRenderer } from "@/components/resume-templates/TemplateRenderer";
import { getTemplate } from "@/lib/templates";
import { isResumeDownloadable } from "@/lib/resumeSchema";
import { useResumeStore } from "@/store/resumeStore";
import { useToastStore } from "@/store/toastStore";

export function PreviewPane() {
  const {
    resume, previousResume, templateId, isEnhancing, enhanceError,
    showCompare, setShowCompare,
    setEnhanceError, setIsEnhancing, rawText, targetJobDescription, setResume,
  } = useResumeStore();
  const addToast = useToastStore((s) => s.addToast);
  const style = getTemplate(templateId);
  const canDownload = isResumeDownloadable(resume);
  const displayResume = showCompare && previousResume ? previousResume : resume;

  const handleDownload = useCallback(async () => {
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
      addToast("Resume downloaded successfully", "success");
    } catch {
      addToast("Download failed. Try again.", "error");
    }
  }, [resume, templateId, addToast]);

  const handleRetry = useCallback(() => {
    setEnhanceError(null);
    addToast("Use the Enhance button in the Build panel to retry", "info");
  }, [setEnhanceError, addToast]);

  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between mb-5 px-1">
        <div className="flex items-center gap-3">
          <span className="section-label">Preview</span>
          {previousResume && (
            <button
              onClick={() => setShowCompare(!showCompare)}
              className={`flex items-center gap-1 text-[11px] font-medium transition-colors ${
                showCompare ? "text-[#0071e3]" : "text-[#6e6e73] hover:text-[#1d1d1f]"
              }`}
            >
              <Columns2 className="h-3 w-3" />
              {showCompare ? "Before" : "Compare"}
            </button>
          )}
        </div>
        <Button
          onClick={handleDownload}
          disabled={!canDownload}
          variant={canDownload ? "default" : "secondary"}
          size="sm"
        >
          <ArrowDownToLine className="h-3.5 w-3.5" />
          .docx
        </Button>
      </div>

      <motion.div layout className="document-preview overflow-hidden min-h-[620px] relative">
        {isEnhancing && <ShimmerOverlay />}

        {isEnhancing ? (
          <div className="p-12 space-y-4">
            <Skeleton className="h-6 w-36 mx-auto rounded-full" />
            <Skeleton className="h-3 w-48 mx-auto rounded-full" />
            <div className="space-y-2.5 pt-6">
              <Skeleton className="h-2.5 w-full rounded-full" />
              <Skeleton className="h-2.5 w-full rounded-full" />
              <Skeleton className="h-2.5 w-2/3 rounded-full" />
            </div>
          </div>
        ) : enhanceError ? (
          <div className="flex flex-col items-center justify-center h-full min-h-[400px] p-12 text-center">
            <p className="text-[#6e6e73] text-[15px] mb-6 leading-relaxed">{enhanceError}</p>
            <Button variant="ghost" onClick={handleRetry}>
              <RefreshCw className="h-3.5 w-3.5" />
              Try again
            </Button>
          </div>
        ) : (
          <AnimatePresence mode="wait">
            <motion.div
              key={showCompare ? "before" : "after"}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <TemplateRenderer data={displayResume} style={style} />
            </motion.div>
          </AnimatePresence>
        )}
      </motion.div>
    </div>
  );
}