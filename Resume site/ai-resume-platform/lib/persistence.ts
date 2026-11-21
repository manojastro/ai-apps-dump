import type { ResumeData, TemplateId } from "./resumeSchema";

const STORAGE_KEY = "resumeai-session";

export interface PersistedSession {
  resume: ResumeData;
  templateId: TemplateId;
  rawText: string;
  targetJobDescription: string;
  inputMode: string;
}

export function loadSession(): Partial<PersistedSession> | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as PersistedSession;
  } catch {
    return null;
  }
}

export function saveSession(data: PersistedSession): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    // Storage full or unavailable
  }
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
}