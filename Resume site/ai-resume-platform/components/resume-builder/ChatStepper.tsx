"use client";

import { motion } from "framer-motion";

interface ChatStepperProps {
  total: number;
  current: number;
}

export function ChatStepper({ total, current }: ChatStepperProps) {
  const pct = total > 1 ? (current / (total - 1)) * 100 : 0;

  return (
    <div className="space-y-2">
      <p className="text-[11px] text-[#6e6e73]">
        Step {current + 1} of {total}
      </p>
      <div className="relative h-1 overflow-hidden rounded-full bg-[#1d1d1f]/[0.06]">
        <motion.div
          className="absolute inset-y-0 left-0 rounded-full bg-[#0071e3]"
          initial={false}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>
    </div>
  );
}
