"use client";

import { useCallback, useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { useResumeStore } from "@/store/resumeStore";
import { useToastStore } from "@/store/toastStore";

export function PasteContentTab() {
  const {
    rawText,
    setRawText,
    targetJobDescription,
    setTargetJobDescription,
    isEnhancing,
    setIsEnhancing,
    setEnhanceError,
    setResume,
    resume,
    setMobilePane,
  } = useResumeStore();
  const addToast = useToastStore((s) => s.addToast);
  const [success, setSuccess] = useState(false);

  const handleEnhance = useCallback(async () => {
    if (!rawText.trim()) return;
    setIsEnhancing(true);
    setEnhanceError(null);
    setSuccess(false);
    setMobilePane("preview");
    try {
      const res = await fetch("/api/resume/enhance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rawText,
          targetJobDescription: targetJobDescription || undefined,
          existingResumeJson: resume,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Enhancement failed");
      }
      setResume(await res.json(), true);
      setSuccess(true);
      addToast("Your resume is ready to review", "success");
    } catch (e) {
      setEnhanceError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setIsEnhancing(false);
    }
  }, [
    rawText,
    targetJobDescription,
    resume,
    setIsEnhancing,
    setEnhanceError,
    setResume,
    addToast,
    setMobilePane,
  ]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        const tag = (e.target as HTMLElement)?.tagName;
        if (tag === "TEXTAREA" || tag === "INPUT") {
          e.preventDefault();
          void handleEnhance();
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handleEnhance]);

  return (
    <div className="space-y-4">
      <Textarea
        id="raw-text"
        aria-label="Resume content"
        placeholder="Paste anything — old resume, LinkedIn profile, rough bullet points..."
        className="min-h-[240px] focus-ring"
        value={rawText}
        onChange={(e) => setRawText(e.target.value)}
      />

      <Textarea
        id="job-desc"
        aria-label="Target job description"
        placeholder="Paste a job description to tailor against (optional)"
        className="min-h-[80px] focus-ring"
        value={targetJobDescription}
        onChange={(e) => setTargetJobDescription(e.target.value)}
      />

      <div className="flex flex-wrap items-center gap-3">
        <LoadingButton
          onClick={handleEnhance}
          disabled={!rawText.trim()}
          loading={isEnhancing}
          success={success}
          successLabel="Ready"
          size="lg"
          icon={<ArrowRight className="h-4 w-4" />}
          iconHoverShift="right"
        >
          Enhance with AI
        </LoadingButton>
        <span className="text-[11px] text-[#6e6e73]">⌘/Ctrl + Enter</span>
      </div>
    </div>
  );
}
