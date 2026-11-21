"use client";

import { cn } from "@/lib/utils";

interface ChatStepperProps {
  total: number;
  current: number;
}

export function ChatStepper({ total, current }: ChatStepperProps) {
  return (
    <div className="flex items-center gap-1.5 justify-center">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "rounded-full transition-all duration-500",
            i === current
              ? "h-2 w-6 bg-[#1d1d1f]"
              : i < current
                ? "h-2 w-2 bg-[#1d1d1f]/40"
                : "h-2 w-2 bg-[#1d1d1f]/[0.08]"
          )}
        />
      ))}
    </div>
  );
}