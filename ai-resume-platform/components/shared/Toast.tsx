"use client";

import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, AlertCircle, Info } from "lucide-react";
import { useToastStore } from "@/store/toastStore";

const icons = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
};

export function ToastContainer() {
  const { toasts, removeToast } = useToastStore();

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2 pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => {
          const Icon = icons[toast.type];
          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 16, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 8, scale: 0.95 }}
              transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
              className="pointer-events-auto flex items-center gap-3 rounded-full bg-[#1d1d1f]/90 backdrop-blur-xl px-5 py-3 shadow-[0_8px_32px_rgba(0,0,0,0.2)]"
            >
              <Icon className="h-4 w-4 text-white shrink-0" strokeWidth={1.5} />
              <p className="text-[13px] text-white font-medium">{toast.message}</p>
              <button
                onClick={() => removeToast(toast.id)}
                className="ml-2 text-white/40 hover:text-white/80 text-[11px]"
                aria-label="Dismiss"
              >
                ✕
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}