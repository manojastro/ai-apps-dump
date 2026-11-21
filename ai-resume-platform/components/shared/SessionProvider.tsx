"use client";

import { useEffect } from "react";
import { useResumeStore } from "@/store/resumeStore";
import { loadSession, saveSession } from "@/lib/persistence";
import { normalizeTemplateId, type TemplateId } from "@/lib/resumeSchema";
import type { InputMode } from "@/store/resumeStore";

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const store = useResumeStore();

  useEffect(() => {
    const saved = loadSession();
    if (saved?.resume) {
      store.hydrate({
        resume: saved.resume,
        templateId: normalizeTemplateId(saved.templateId || "blue-clean"),
        rawText: saved.rawText || "",
        targetJobDescription: saved.targetJobDescription || "",
        inputMode: (saved.inputMode as InputMode) || "paste",
      });
    } else {
      store.setHydrated(true);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!store.hydrated) return;
    const timer = setTimeout(() => {
      saveSession({
        resume: store.resume,
        templateId: store.templateId,
        rawText: store.rawText,
        targetJobDescription: store.targetJobDescription,
        inputMode: store.inputMode,
      });
    }, 500);
    return () => clearTimeout(timer);
  }, [
    store.hydrated,
    store.resume,
    store.templateId,
    store.rawText,
    store.targetJobDescription,
    store.inputMode,
  ]);

  return <>{children}</>;
}