import { SCHEMA_VERSION } from "./constants";
import { createEmptyState } from "./empty-state";
import { migrateState } from "./migrations";
import { parseCareerState, stripSecrets } from "./validation";
import type { CareerOSState } from "@/types/career";

export interface ImportPreview {
  valid: boolean;
  errors: string[];
  version?: number;
  counts: Record<string, number>;
  demoMode?: boolean;
  duplicateHints: string[];
}

export function exportBundle(state: CareerOSState) {
  return {
    schemaVersion: SCHEMA_VERSION,
    exportedAt: new Date().toISOString(),
    app: "ai-career-os",
    state: stripSecrets(state),
  };
}

export function previewImport(raw: string, current: CareerOSState): ImportPreview {
  let json: unknown;
  try {
    json = JSON.parse(raw);
  } catch {
    return { valid: false, errors: ["JSON could not be parsed."], counts: {}, duplicateHints: [] };
  }
  const maybe = json as { state?: unknown; version?: unknown };
  const payload = maybe.state ?? json;
  const migrated = migrateState(payload);
  const parsed = parseCareerState(migrated);
  if (!parsed.success) {
    return {
      valid: false,
      errors: parsed.error.issues.slice(0, 8).map((i) => `${i.path.join(".")}: ${i.message}`),
      counts: {},
      duplicateHints: [],
    };
  }
  const s = parsed.data;
  const counts: Record<string, number> = {
    skills: s.skills.length,
    projects: s.projects.length,
    applications: s.applications.length,
    contacts: s.contacts.length,
    evidence: s.evidenceArtifacts.length,
    tasks: s.tasks.length,
  };
  const duplicateHints: string[] = [];
  const overlap = (a: { id: string }[], b: { id: string }[]) => a.filter((x) => b.some((y) => y.id === x.id)).length;
  if (overlap(s.applications, current.applications) > 0) duplicateHints.push("Some job IDs already exist in the workspace.");
  if (overlap(s.projects, current.projects) > 0) duplicateHints.push("Some project IDs already exist in the workspace.");
  return {
    valid: true,
    errors: [],
    version: s.version,
    counts,
    demoMode: s.ui.demoMode,
    duplicateHints,
  };
}

export function parseImportedState(raw: string): CareerOSState {
  const json = JSON.parse(raw) as { state?: unknown };
  const migrated = migrateState(json.state ?? json);
  const parsed = parseCareerState(migrated);
  if (!parsed.success) throw new Error(parsed.error.issues[0]?.message ?? "Invalid state");
  return parsed.data;
}

export function diagnosticExport(includeCareerData: boolean, extra?: Record<string, unknown>) {
  return JSON.stringify(
    {
      app: "ai-career-os",
      exportedAt: new Date().toISOString(),
      userAgent: typeof navigator !== "undefined" ? navigator.userAgent : "unknown",
      includeCareerData,
      state: includeCareerData ? extra?.state : undefined,
      note: includeCareerData ? "Contains personal career data." : "No career records included.",
    },
    null,
    2,
  );
}

export function resetWorkspace() {
  return createEmptyState({
    ui: {
      onboardingComplete: true,
      demoMode: false,
      privacyMode: false,
      sidebarCollapsed: false,
    },
  });
}
