/**
 * Local-only productivity helpers (browser storage).
 * Never sends data to servers — privacy-safe workspace UX.
 */

const NOTES_KEY = "resumeai-workspace-notes";
const PINS_KEY = "resumeai-pinned-queries";
const PREFS_KEY = "resumeai-ui-prefs";
const LAST_SAVED_KEY = "resumeai-last-saved-at";

export interface WorkspaceNotes {
  /** Freeform job-hunt notes — local only */
  notes: string;
  updatedAt: number;
}

export interface UiPrefs {
  focusPreview: boolean;
  compactBuild: boolean;
}

export function loadNotes(): WorkspaceNotes {
  if (typeof window === "undefined") return { notes: "", updatedAt: 0 };
  try {
    const raw = localStorage.getItem(NOTES_KEY);
    if (!raw) return { notes: "", updatedAt: 0 };
    return JSON.parse(raw) as WorkspaceNotes;
  } catch {
    return { notes: "", updatedAt: 0 };
  }
}

export function saveNotes(notes: string): void {
  if (typeof window === "undefined") return;
  try {
    const payload: WorkspaceNotes = { notes, updatedAt: Date.now() };
    localStorage.setItem(NOTES_KEY, JSON.stringify(payload));
  } catch {
    /* ignore */
  }
}

export function loadPinnedQueries(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(PINS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as string[];
    return Array.isArray(parsed) ? parsed.slice(0, 8) : [];
  } catch {
    return [];
  }
}

export function togglePinnedQuery(q: string): string[] {
  const trimmed = q.trim();
  if (!trimmed || typeof window === "undefined") return loadPinnedQueries();
  const current = loadPinnedQueries();
  const exists = current.some((x) => x.toLowerCase() === trimmed.toLowerCase());
  const next = exists
    ? current.filter((x) => x.toLowerCase() !== trimmed.toLowerCase())
    : [trimmed, ...current].slice(0, 8);
  try {
    localStorage.setItem(PINS_KEY, JSON.stringify(next));
  } catch {
    /* ignore */
  }
  return next;
}

export function loadUiPrefs(): UiPrefs {
  if (typeof window === "undefined") {
    return { focusPreview: false, compactBuild: false };
  }
  try {
    const raw = localStorage.getItem(PREFS_KEY);
    if (!raw) return { focusPreview: false, compactBuild: false };
    return { focusPreview: false, compactBuild: false, ...JSON.parse(raw) };
  } catch {
    return { focusPreview: false, compactBuild: false };
  }
}

export function saveUiPrefs(prefs: Partial<UiPrefs>): UiPrefs {
  const next = { ...loadUiPrefs(), ...prefs };
  if (typeof window !== "undefined") {
    try {
      localStorage.setItem(PREFS_KEY, JSON.stringify(next));
    } catch {
      /* ignore */
    }
  }
  return next;
}

export function markSessionSaved(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(LAST_SAVED_KEY, String(Date.now()));
  } catch {
    /* ignore */
  }
}

export function getLastSavedAt(): number | null {
  if (typeof window === "undefined") return null;
  try {
    const v = localStorage.getItem(LAST_SAVED_KEY);
    return v ? Number(v) : null;
  } catch {
    return null;
  }
}

export function formatRelativeTime(ts: number | null): string {
  if (!ts) return "Not saved yet";
  const diff = Date.now() - ts;
  if (diff < 15_000) return "Saved just now";
  if (diff < 60_000) return "Saved moments ago";
  if (diff < 3_600_000) return `Saved ${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `Saved ${Math.floor(diff / 3_600_000)}h ago`;
  return `Saved ${new Date(ts).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}`;
}

/** Local checklist for resume completeness — no network. */
export function getLocalChecklist(resume: {
  personalInfo?: { fullName?: string; email?: string; phone?: string; location?: string };
  targetRole?: string;
  summary?: string;
  experience?: unknown[];
  education?: unknown[];
  skills?: { technical?: string[] };
}): { id: string; label: string; done: boolean }[] {
  const pi = resume.personalInfo || {};
  return [
    { id: "name", label: "Full name", done: !!pi.fullName?.trim() },
    {
      id: "contact",
      label: "Email or phone",
      done: !!(pi.email?.trim() || pi.phone?.trim()),
    },
    { id: "role", label: "Target role", done: !!resume.targetRole?.trim() },
    { id: "summary", label: "Professional summary", done: !!resume.summary?.trim() },
    {
      id: "exp",
      label: "At least one experience",
      done: Array.isArray(resume.experience) && resume.experience.length > 0,
    },
    {
      id: "edu",
      label: "Education",
      done: Array.isArray(resume.education) && resume.education.length > 0,
    },
    {
      id: "skills",
      label: "Technical skills",
      done: (resume.skills?.technical?.length || 0) > 0,
    },
    { id: "location", label: "Location", done: !!pi.location?.trim() },
  ];
}
