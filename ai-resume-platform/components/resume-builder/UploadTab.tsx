"use client";

import { useCallback, useRef, useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useResumeStore } from "@/store/resumeStore";
import { useToastStore } from "@/store/toastStore";

export function UploadTab() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState("");
  const [parsedText, setParsedText] = useState("");
  const [parseError, setParseError] = useState<string | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const {
    isEnhancing, setIsEnhancing, setEnhanceError, setResume, resume,
    targetJobDescription, setMobilePane,
  } = useResumeStore();
  const addToast = useToastStore((s) => s.addToast);

  const handleFile = useCallback(async (file: File) => {
    setFileName(file.name);
    setParseError(null);
    setIsParsing(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/api/resume/parse", { method: "POST", body: formData });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Failed to parse file");
      }
      const { text } = await res.json();
      setParsedText(text);
      addToast("File parsed successfully", "success");
    } catch (e) {
      setParseError(e instanceof Error ? e.message : "Parse failed");
    } finally {
      setIsParsing(false);
    }
  }, [addToast]);

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
      addToast("Resume restructured with AI", "success");
    } catch (e) {
      setEnhanceError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setIsEnhancing(false);
    }
  }, [parsedText, targetJobDescription, resume, setIsEnhancing, setEnhanceError, setResume, addToast, setMobilePane]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  return (
    <div className="space-y-6">
      <button
        type="button"
        className={`w-full rounded-2xl border border-dashed py-16 text-center transition-all duration-300 group ${
          isDragging
            ? "border-[#0071e3] bg-[#0071e3]/5"
            : "border-[#1d1d1f]/10 hover:border-[#1d1d1f]/20 hover:bg-[#1d1d1f]/[0.02]"
        }`}
        onClick={() => fileRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        aria-label="Upload resume file"
      >
        <div className="mx-auto mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-[#1d1d1f]/[0.04] group-hover:bg-[#1d1d1f]/[0.08] transition-colors duration-300">
          <Plus className="h-4 w-4 text-[#6e6e73]" strokeWidth={1.5} />
        </div>
        <p className="text-[15px] text-[#1d1d1f] font-medium">
          {fileName || "Drop or click to upload"}
        </p>
        <p className="text-[12px] text-[#6e6e73] mt-1">.docx or .pdf</p>
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
      </button>

      {isParsing && (
        <p className="text-[13px] text-[#6e6e73] text-center animate-pulse">Reading file...</p>
      )}

      {parseError && (
        <p className="text-[13px] text-[#6e6e73] text-center">
          {parseError}.{" "}
          <button onClick={() => fileRef.current?.click()} className="text-[#0071e3] hover:opacity-60">
            Retry
          </button>
        </p>
      )}

      {parsedText && !isParsing && (
        <div className="flex flex-col items-center gap-4">
          <p className="text-[12px] text-[#6e6e73]">
            {parsedText.length.toLocaleString()} characters ready
          </p>
          <Button onClick={handleEnhance} disabled={isEnhancing} size="lg">
            {isEnhancing ? "Restructuring..." : "Enhance with AI"}
          </Button>
        </div>
      )}
    </div>
  );
}