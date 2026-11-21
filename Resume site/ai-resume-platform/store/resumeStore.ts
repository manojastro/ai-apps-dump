import { create } from "zustand";
import {
  emptyResume,
  type ResumeData,
  type TemplateId,
} from "@/lib/resumeSchema";

export type InputMode = "paste" | "chat" | "upload";
export type MobilePane = "build" | "preview";

const HISTORY_LIMIT = 30;

interface ResumeStore {
  resume: ResumeData;
  previousResume: ResumeData | null;
  templateId: TemplateId;
  inputMode: InputMode;
  mobilePane: MobilePane;
  isEnhancing: boolean;
  enhanceError: string | null;
  rawText: string;
  targetJobDescription: string;
  chatStep: number;
  chatAnswers: Record<string, string>;
  showCompare: boolean;
  hydrated: boolean;
  past: ResumeData[];
  future: ResumeData[];

  setResume: (data: ResumeData, keepPrevious?: boolean) => void;
  updateResume: (partial: Partial<ResumeData>) => void;
  setTemplateId: (id: TemplateId) => void;
  setInputMode: (mode: InputMode) => void;
  setMobilePane: (pane: MobilePane) => void;
  setIsEnhancing: (v: boolean) => void;
  setEnhanceError: (e: string | null) => void;
  setRawText: (t: string) => void;
  setTargetJobDescription: (t: string) => void;
  setChatStep: (s: number) => void;
  setChatAnswer: (key: string, value: string) => void;
  setShowCompare: (v: boolean) => void;
  setHydrated: (v: boolean) => void;
  hydrate: (data: Partial<ResumeStore>) => void;
  undo: () => void;
  redo: () => void;
  reset: () => void;
}

function pushHistory(past: ResumeData[], current: ResumeData): ResumeData[] {
  return [...past, structuredClone(current)].slice(-HISTORY_LIMIT);
}

export const useResumeStore = create<ResumeStore>((set, get) => ({
  resume: { ...emptyResume },
  previousResume: null,
  templateId: "blue-clean",
  inputMode: "paste",
  mobilePane: "build",
  isEnhancing: false,
  enhanceError: null,
  rawText: "",
  targetJobDescription: "",
  chatStep: 0,
  chatAnswers: {},
  showCompare: false,
  hydrated: false,
  past: [],
  future: [],

  setResume: (data, keepPrevious = false) =>
    set((s) => ({
      past: pushHistory(s.past, s.resume),
      future: [],
      resume: data,
      previousResume: keepPrevious ? structuredClone(s.resume) : s.previousResume,
    })),
  updateResume: (partial) =>
    set((s) => ({
      past: pushHistory(s.past, s.resume),
      future: [],
      resume: {
        ...s.resume,
        ...partial,
        personalInfo: { ...s.resume.personalInfo, ...partial.personalInfo },
        skills: partial.skills ?? s.resume.skills,
      },
    })),
  setTemplateId: (id) => set({ templateId: id }),
  setInputMode: (mode) => set({ inputMode: mode }),
  setMobilePane: (pane) => set({ mobilePane: pane }),
  setIsEnhancing: (v) => set({ isEnhancing: v }),
  setEnhanceError: (e) => set({ enhanceError: e }),
  setRawText: (t) => set({ rawText: t }),
  setTargetJobDescription: (t) => set({ targetJobDescription: t }),
  setChatStep: (s) => set({ chatStep: s }),
  setChatAnswer: (key, value) =>
    set((s) => ({ chatAnswers: { ...s.chatAnswers, [key]: value } })),
  setShowCompare: (v) => set({ showCompare: v }),
  setHydrated: (v) => set({ hydrated: v }),
  hydrate: (data) =>
    set((s) => ({
      ...s,
      ...data,
      past: [],
      future: [],
      hydrated: true,
    })),
  undo: () => {
    const { past, resume, future } = get();
    if (past.length === 0) return;
    const previous = past[past.length - 1];
    set({
      past: past.slice(0, -1),
      future: [structuredClone(resume), ...future].slice(0, HISTORY_LIMIT),
      resume: previous,
    });
  },
  redo: () => {
    const { past, resume, future } = get();
    if (future.length === 0) return;
    const next = future[0];
    set({
      past: pushHistory(past, resume),
      future: future.slice(1),
      resume: next,
    });
  },
  reset: () =>
    set({
      resume: { ...emptyResume },
      previousResume: null,
      templateId: "blue-clean",
      isEnhancing: false,
      enhanceError: null,
      rawText: "",
      targetJobDescription: "",
      chatStep: 0,
      chatAnswers: {},
      showCompare: false,
      past: [],
      future: [],
    }),
}));
