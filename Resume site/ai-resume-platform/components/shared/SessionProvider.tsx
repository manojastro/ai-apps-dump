"use client";

import { useEffect } from "react";
import { useResumeStore } from "@/store/resumeStore";
import { loadSession, saveSession } from "@/lib/persistence";
import { markSessionSaved } from "@/lib/localWorkspace";
import { normalizeTemplateId } from "@/lib/resumeSchema";
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
      markSessionSaved();
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

  // Undo / redo shortcuts (skip when typing in inputs for redo-only browser conflict)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const meta = e.metaKey || e.ctrlKey;
      if (!meta) return;
      const target = e.target as HTMLElement | null;
      const tag = target?.tagName;
      const editing =
        tag === "INPUT" || tag === "TEXTAREA" || target?.isContentEditable;

      if (e.key.toLowerCase() === "z" && !e.shiftKey) {
        // Allow undo in app even from fields for resume history
        e.preventDefault();
        useResumeStore.getState().undo();
        return;
      }
      if (
        (e.key.toLowerCase() === "z" && e.shiftKey) ||
        (e.key.toLowerCase() === "y" && !editing)
      ) {
        e.preventDefault();
        useResumeStore.getState().redo();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return <>{children}</>;
}
