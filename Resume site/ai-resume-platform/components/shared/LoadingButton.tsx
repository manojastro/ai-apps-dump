"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Loader2 } from "lucide-react";
import { Button, type ButtonProps } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface LoadingButtonProps extends ButtonProps {
  loading?: boolean;
  success?: boolean;
  successLabel?: string;
  icon?: React.ReactNode;
  iconHoverShift?: "right" | "down" | "none";
}

/**
 * Primary CTA with loading width lock + brief success state.
 */
export function LoadingButton({
  loading,
  success,
  successLabel = "Done",
  icon,
  iconHoverShift = "none",
  children,
  className,
  disabled,
  ...props
}: LoadingButtonProps) {
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    if (!success) return;
    setShowSuccess(true);
    const t = setTimeout(() => setShowSuccess(false), 1600);
    return () => clearTimeout(t);
  }, [success]);

  const busy = !!loading || showSuccess;

  return (
    <Button
      {...props}
      disabled={disabled || loading}
      className={cn(
        "relative min-w-[8.5rem] transition-transform duration-200 hover:scale-[1.015] active:scale-[0.98]",
        className
      )}
    >
      <AnimatePresence mode="wait" initial={false}>
        {loading ? (
          <motion.span
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="inline-flex items-center gap-2"
          >
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Working…
          </motion.span>
        ) : showSuccess ? (
          <motion.span
            key="success"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="inline-flex items-center gap-2"
          >
            <Check className="h-3.5 w-3.5" />
            {successLabel}
          </motion.span>
        ) : (
          <motion.span
            key="idle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className={cn(
              "inline-flex items-center gap-2 group/btn",
              iconHoverShift === "right" && "[&_svg]:transition-transform [&_svg]:duration-300 group-hover/btn:[&_svg]:translate-x-0.5",
              iconHoverShift === "down" && "[&_svg]:transition-transform [&_svg]:duration-300 group-hover/btn:[&_svg]:translate-y-0.5"
            )}
          >
            {icon}
            {children}
          </motion.span>
        )}
      </AnimatePresence>
      {/* Preserve layout while states swap */}
      <span className="invisible absolute" aria-hidden>
        {busy ? "Working…" : children}
      </span>
    </Button>
  );
}
