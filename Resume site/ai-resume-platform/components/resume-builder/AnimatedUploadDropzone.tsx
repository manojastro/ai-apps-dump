"use client";

import { useEffect, useState } from "react";
import { motion, useReducedMotion, AnimatePresence } from "framer-motion";
import { FileText, Upload } from "lucide-react";
import { cn } from "@/lib/utils";

const PARSE_MESSAGES = [
  "Uploading securely",
  "Reading document",
  "Extracting experience",
  "Preparing your resume",
];

interface AnimatedUploadDropzoneProps {
  fileName?: string;
  isDragging: boolean;
  isParsing: boolean;
  error?: string | null;
  onBrowse: () => void;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: () => void;
  onDrop: (e: React.DragEvent) => void;
  onRetry?: () => void;
}

export function AnimatedUploadDropzone({
  fileName,
  isDragging,
  isParsing,
  error,
  onBrowse,
  onDragOver,
  onDragLeave,
  onDrop,
  onRetry,
}: AnimatedUploadDropzoneProps) {
  const reduce = useReducedMotion();
  const [msgIdx, setMsgIdx] = useState(0);
  const [shake, setShake] = useState(false);

  useEffect(() => {
    if (!isParsing) {
      setMsgIdx(0);
      return;
    }
    const id = setInterval(() => {
      setMsgIdx((i) => (i < PARSE_MESSAGES.length - 1 ? i + 1 : i));
    }, 1400);
    return () => clearInterval(id);
  }, [isParsing]);

  useEffect(() => {
    if (!error) return;
    setShake(true);
    const t = setTimeout(() => setShake(false), 450);
    return () => clearTimeout(t);
  }, [error]);

  return (
    <div>
      <motion.button
        type="button"
        onClick={onBrowse}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        aria-label="Upload resume file"
        animate={
          shake && !reduce
            ? { x: [0, -6, 6, -4, 4, 0] }
            : { x: 0 }
        }
        transition={{ duration: 0.4 }}
        className={cn(
          "group relative w-full overflow-hidden rounded-2xl border border-dashed py-14 text-center transition-colors duration-300",
          isDragging
            ? "border-[#0071e3] bg-[#0071e3]/[0.06]"
            : error
              ? "border-[#ff3b30]/40 bg-[#ff3b30]/[0.03]"
              : "border-[#1d1d1f]/10 hover:border-[#0071e3]/35 hover:bg-[#0071e3]/[0.03]",
          isParsing && "pointer-events-none"
        )}
      >
        {/* Scan line while parsing */}
        {isParsing && !reduce && (
          <motion.div
            className="pointer-events-none absolute inset-x-8 top-0 h-0.5 bg-gradient-to-r from-transparent via-[#0071e3]/70 to-transparent"
            animate={{ y: [0, 180, 0] }}
            transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
          />
        )}

        <motion.div
          className={cn(
            "mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl transition-colors duration-300",
            isDragging ? "bg-[#0071e3]/12" : "bg-[#1d1d1f]/[0.04] group-hover:bg-[#0071e3]/10"
          )}
          animate={
            reduce
              ? undefined
              : isDragging
                ? { y: -4 }
                : isParsing
                  ? { y: [0, -2, 0] }
                  : { y: 0 }
          }
          transition={
            isParsing && !reduce
              ? { duration: 1.4, repeat: Infinity, ease: "easeInOut" }
              : { duration: 0.25 }
          }
        >
          {fileName && !isParsing ? (
            <FileText className="h-5 w-5 text-[#0071e3]" strokeWidth={1.5} />
          ) : (
            <Upload
              className={cn(
                "h-5 w-5 transition-colors",
                isDragging ? "text-[#0071e3]" : "text-[#6e6e73] group-hover:text-[#0071e3]"
              )}
              strokeWidth={1.5}
            />
          )}
        </motion.div>

        <p className="text-[15px] font-medium text-[#1d1d1f]">
          {isParsing
            ? PARSE_MESSAGES[msgIdx]
            : isDragging
              ? "Release to import your resume"
              : fileName || "Drop or click to upload"}
        </p>
        <p className="mt-1 text-[12px] text-[#6e6e73]">
          {fileName && !isParsing ? fileName : ".docx or .pdf · processed on the server only"}
        </p>
      </motion.button>

      <div className="sr-only" role="status" aria-live="polite">
        {isParsing
          ? PARSE_MESSAGES[msgIdx]
          : error
            ? error
            : fileName
              ? `Imported ${fileName}`
              : ""}
      </div>

      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-3 text-center text-[13px] text-[#ff3b30]"
          >
            {error}.{" "}
            {onRetry && (
              <button type="button" onClick={onRetry} className="font-medium underline-offset-2 hover:underline">
                Retry
              </button>
            )}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
}
