"use client";

import { useCallback, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check } from "lucide-react";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { AnimatedUploadDropzone } from "./AnimatedUploadDropzone";
import { useResumeStore } from "@/store/resumeStore";
import { useToastStore } from "@/store/toastStore";

export function UploadTab() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState("");
  const [parsedText, setParsedText] = useState("");
  const [parseError, setParseError] = useState<string | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [successTick, setSuccessTick] = useState(0);
  const {
    isEnhancing,
    setIsEnhancing,
    setEnhanceError,
    setResume,
    resume,
    targetJobDescription,
    setMobilePane,
    setRawText,
  } = useResumeStore();
  const addToast = useToastStore((s) => s.addToast);

  const handleFile = useCallback(
    async (file: File) => {
      setFileName(file.name);
      setParseError(null);
      setIsParsing(true);
      try {
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch("/api/resume/parse", {
          method: "POST",
          body: formData,
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.error || "Failed to parse file");
        }
        const { text } = await res.json();
        setParsedText(text);
        setRawText(text);
        setSuccessTick((n) => n + 1);
        addToast("File parsed successfully", "success");
      } catch (e) {
        setParseError(e instanceof Error ? e.message : "Parse failed");
      } finally {
        setIsParsing(false);
      }
    },
    [addToast, setRawText]
  );

  const handleEnhance = useCallback(async () => {
    if (!parsedText.trim()) return;
    setIsEnhancing(true);
    setEnhanceError(null);
    setMobilePane("preview");
    try {
      const res = await fetch("/api/resume/enhance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rawText: parsedText,
          targetJobDescription: targetJobDescription || undefined,
          existingResumeJson: resume,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Enhancement failed");
      }
      setResume(await res.json(), true);
      addToast("Your resume is ready to review", "success");
    } catch (e) {
      setEnhanceError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setIsEnhancing(false);
    }
  }, [
    parsedText,
    targetJobDescription,
    resume,
    setIsEnhancing,
    setEnhanceError,
    setResume,
    addToast,
    setMobilePane,
  ]);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div className="space-y-6">
      <AnimatedUploadDropzone
        fileName={fileName}
        isDragging={isDragging}
        isParsing={isParsing}
        error={parseError}
        onBrowse={() => fileRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        onRetry={() => fileRef.current?.click()}
      />
      <input
        ref={fileRef}
        type="file"
        accept=".docx,.pdf"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />

      <AnimatePresence>
        {parsedText && !isParsing && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="premium-card-static space-y-4 p-5"
          >
            <div className="flex items-center gap-2 text-[13px] font-medium text-[#1d1d1f]">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#34c759]/15 text-[#248a3d]">
                <Check className="h-3.5 w-3.5" strokeWidth={2.5} />
              </span>
              Imported · {fileName}
              <span className="text-[11px] font-normal text-[#6e6e73]">
                · {parsedText.length.toLocaleString()} chars
              </span>
            </div>
            <p className="line-clamp-3 text-[12px] leading-relaxed text-[#6e6e73]">
              {parsedText.slice(0, 280)}
              {parsedText.length > 280 ? "…" : ""}
            </p>
            <div className="flex justify-center pt-1">
              <LoadingButton
                size="lg"
                loading={isEnhancing}
                success={successTick > 0 && !isEnhancing}
                successLabel="Ready"
                onClick={handleEnhance}
                disabled={!parsedText.trim()}
                iconHoverShift="right"
              >
                Improve with AI
              </LoadingButton>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
