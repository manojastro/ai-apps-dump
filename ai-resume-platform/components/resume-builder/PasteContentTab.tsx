"use client";

import { useCallback } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useResumeStore } from "@/store/resumeStore";
import { useToastStore } from "@/store/toastStore";

export function PasteContentTab() {
  const {
    rawText, setRawText, targetJobDescription, setTargetJobDescription,
    isEnhancing, setIsEnhancing, setEnhanceError, setResume, resume, setMobilePane,
  } = useResumeStore();
  const addToast = useToastStore((s) => s.addToast);

  const handleEnhance = useCallback(async () => {
    if (!rawText.trim()) return;
    setIsEnhancing(true);
    setEnhanceError(null);
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
      addToast("Resume enhanced with AI", "success");
    } catch (e) {
      setEnhanceError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setIsEnhancing(false);
    }
  }, [rawText, targetJobDescription, resume, setIsEnhancing, setEnhanceError, setResume, addToast, setMobilePane]);

  const charCount = rawText.length;
  const ready = rawText.trim().length > 20;

  return (
    <div className="space-y-6">
      <div className="relative">
        <Textarea
          id="raw-text"
          aria-label="Resume content"
          placeholder="Paste anything — old resume, LinkedIn, bullet points..."
          className="min-h-[240px]"
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
        />
        {charCount > 0 && (
          <p className="absolute bottom-3 right-4 text-[11px] text-[#6e6e73]/60">
            {charCount.toLocaleString()} chars
          </p>
        )}
      </div>

      <Textarea
        id="job-desc"
        aria-label="Target job description"
        placeholder="Job description to tailor against (optional)"
        className="min-h-[80px]"
        value={targetJobDescription}
        onChange={(e) => setTargetJobDescription(e.target.value)}
      />

      <div className="flex justify-center pt-2">
        <motion.div
          animate={ready ? { scale: [1, 1.02, 1] } : {}}
          transition={{ duration: 2, repeat: ready ? Infinity : 0, repeatDelay: 3 }}
        >
          <Button
            onClick={handleEnhance}
            disabled={!rawText.trim() || isEnhancing}
            size="lg"
            className={ready ? "shadow-[0_0_24px_rgba(0,113,227,0.25)]" : ""}
          >
            {isEnhancing ? "Enhancing..." : "Enhance with AI"}
          </Button>
        </motion.div>
      </div>
    </div>
  );
}