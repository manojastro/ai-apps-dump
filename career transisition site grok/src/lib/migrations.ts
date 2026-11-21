import { CATALOG_COMPETENCIES, CATALOG_ROLES } from "@/data/catalog";
import { SCHEMA_VERSION } from "./constants";
import { createEmptyState, defaultSettings } from "./empty-state";
import { nowIso } from "./ids";
import type { CareerOSState } from "@/types/career";

function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function mergeById<T extends { id: string }>(incoming: T[], catalog: T[]): T[] {
  const map = new Map<string, T>();
  for (const item of catalog) map.set(item.id, item);
  for (const item of incoming) map.set(item.id, { ...map.get(item.id), ...item });
  return [...map.values()];
}

export function needsMigration(raw: unknown): boolean {
  if (!raw || typeof raw !== "object") return true;
  const version = (raw as { version?: unknown }).version;
  return typeof version !== "number" || version < SCHEMA_VERSION;
}

export function migrateState(raw: unknown): CareerOSState {
  const empty = createEmptyState();
  if (!raw || typeof raw !== "object") return empty;
  const r = raw as Record<string, unknown>;
  const settings = { ...defaultSettings(), ...((r.settings as object) ?? {}) };
  const ui = { ...empty.ui, ...((r.ui as object) ?? {}) };
  const meta = { ...empty.meta, ...((r.meta as object) ?? {}), updatedAt: nowIso() };

  const migrated: CareerOSState = {
    ...empty,
    version: SCHEMA_VERSION,
    settings,
    ui,
    meta,
    skills: asArray(r.skills),
    projects: asArray<Record<string, unknown>>(r.projects).map((p) => ({
      maturity: "Prototype",
      evaluationNotes: "",
      testingNotes: "",
      safetyNotes: "",
      observabilityNotes: "",
      failureHandlingNotes: "",
      documentationNotes: "",
      interviewDefense30s: "",
      interviewDefense2m: "",
      interviewDefenseDeep: "",
      ...p,
    })) as CareerOSState["projects"],
    applications: asArray(r.applications),
    contacts: asArray(r.contacts),
    certifications: asArray(r.certifications),
    starStories: asArray(r.starStories),
    researchTopics: asArray(r.researchTopics),
    weeklySprints: asArray<Record<string, unknown>>(r.weeklySprints).map((s) => ({
      buildingHours: 0,
      jobSearchHours: 0,
      availableHours: settings.weeklyAvailableHours,
      ...s,
    })) as CareerOSState["weeklySprints"],
    tasks: asArray(r.tasks),
    interviewQuestions: asArray(r.interviewQuestions),
    targetRoles: mergeById(asArray(r.targetRoles), CATALOG_ROLES),
    competencies: mergeById(asArray(r.competencies), CATALOG_COMPETENCIES),
    evidenceArtifacts: asArray(r.evidenceArtifacts),
    learningSessions: asArray(r.learningSessions),
    projectMilestones: asArray(r.projectMilestones),
    architectureDecisions: asArray(r.architectureDecisions),
    projectMetrics: asArray(r.projectMetrics),
    resumeVariants: asArray(r.resumeVariants),
    jobDescriptions: asArray(r.jobDescriptions),
    interviewRounds: asArray(r.interviewRounds),
    networkingInteractions: asArray(r.networkingInteractions),
    targetCompanies: asArray(r.targetCompanies),
    campaigns: asArray(r.campaigns),
    achievements: asArray(r.achievements),
    offers: asArray(r.offers),
    researchSources: asArray(r.researchSources),
    activityEvents: asArray(r.activityEvents),
    scoreSnapshots: asArray(r.scoreSnapshots),
    careerAssets: asArray(r.careerAssets),
    resumeBullets: asArray(r.resumeBullets),
    negotiationLogs: asArray(r.negotiationLogs),
    transitionNarratives: asArray(r.transitionNarratives),
    attachments: asArray(r.attachments),
  };

  return migrated;
}
