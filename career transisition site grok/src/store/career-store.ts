"use client";

import { create } from "zustand";
import { createDemoState } from "@/data/demo-data";
import { captureSnapshot, computeReadiness } from "@/lib/scoring";
import { roleScoreMap } from "@/lib/role-readiness";
import { createEmptyState } from "@/lib/empty-state";
import { createId, nowIso, timestamps } from "@/lib/ids";
import {
  defaultRepository,
  newerState,
  publishCrossTab,
  restoreLastKnownGood,
  subscribeCrossTab,
  type LoadResult,
} from "@/lib/storage";
import { parseImportedState, resetWorkspace } from "@/lib/export-import";
import type {
  ActivityCategory,
  ArchitectureDecision,
  BaseEntity,
  CareerAsset,
  CareerCampaign,
  CareerOSState,
  CareerSettings,
  CareerTask,
  CertificationItem,
  EvidenceArtifact,
  InterviewQuestion,
  InterviewRound,
  JobApplication,
  JobDescriptionSnapshot,
  LearningSession,
  NegotiationLog,
  NetworkingContact,
  NetworkingInteraction,
  OfferItem,
  ProjectItem,
  ProjectMetric,
  ProjectMilestone,
  RecoveryPayload,
  ResearchSource,
  ResearchTopic,
  ResumeBullet,
  ResumeVariant,
  SaveStatus,
  SkillItem,
  StarStory,
  TargetCompany,
  TargetRoleProfile,
  TransitionNarrative,
  AchievementItem,
  WeeklySprint,
} from "@/types/career";

const repo = defaultRepository;
let saveTimer: ReturnType<typeof setTimeout> | null = null;
let unsub: (() => void) | null = null;
let applyingRemote = false;

function upsert<T extends BaseEntity>(list: T[], item: T): T[] {
  const i = list.findIndex((x) => x.id === item.id);
  if (i === -1) return [...list, item];
  const next = [...list];
  next[i] = { ...item, updatedAt: nowIso() };
  return next;
}

function archiveList<T extends BaseEntity>(list: T[], id: string): T[] {
  return list.map((x) => (x.id === id ? { ...x, archivedAt: nowIso(), updatedAt: nowIso() } : x));
}

function event(category: ActivityCategory, action: string, entityId?: string) {
  return {
    id: createId("evt"),
    ...timestamps(),
    occurredAt: nowIso(),
    category,
    action,
    entityId,
  };
}

export interface CareerStore {
  state: CareerOSState;
  hydrated: boolean;
  saveStatus: SaveStatus;
  recovery: RecoveryPayload | null;
  lastError: string | null;
  undo: CareerOSState | null;
  hydrate: () => Promise<void>;
  persistNow: () => Promise<void>;
  setState: (state: CareerOSState, opts?: { persist?: boolean; remote?: boolean }) => void;
  updateSettings: (patch: Partial<CareerSettings>) => void;
  setUi: (patch: Partial<CareerOSState["ui"]>) => void;
  addSkill: (item: SkillItem) => void;
  updateSkill: (item: SkillItem) => void;
  archiveSkill: (id: string) => void;
  addProject: (item: ProjectItem) => void;
  updateProject: (item: ProjectItem) => void;
  archiveProject: (id: string) => void;
  addApplication: (item: JobApplication) => void;
  updateApplication: (item: JobApplication) => void;
  archiveApplication: (id: string) => void;
  addContact: (item: NetworkingContact) => void;
  updateContact: (item: NetworkingContact) => void;
  archiveContact: (id: string) => void;
  addCertification: (item: CertificationItem) => void;
  updateCertification: (item: CertificationItem) => void;
  archiveCertification: (id: string) => void;
  addStarStory: (item: StarStory) => void;
  updateStarStory: (item: StarStory) => void;
  archiveStarStory: (id: string) => void;
  addResearchTopic: (item: ResearchTopic) => void;
  updateResearchTopic: (item: ResearchTopic) => void;
  archiveResearchTopic: (id: string) => void;
  addTask: (item: CareerTask) => void;
  updateTask: (item: CareerTask) => void;
  archiveTask: (id: string) => void;
  addInterviewQuestion: (item: InterviewQuestion) => void;
  updateInterviewQuestion: (item: InterviewQuestion) => void;
  archiveInterviewQuestion: (id: string) => void;
  updateRole: (item: TargetRoleProfile) => void;
  addEvidence: (item: EvidenceArtifact) => void;
  updateEvidence: (item: EvidenceArtifact) => void;
  archiveEvidence: (id: string) => void;
  addLearningSession: (item: LearningSession) => void;
  addProjectMilestone: (item: ProjectMilestone) => void;
  updateProjectMilestone: (item: ProjectMilestone) => void;
  addArchitectureDecision: (item: ArchitectureDecision) => void;
  addProjectMetric: (item: ProjectMetric) => void;
  addResumeVariant: (item: ResumeVariant) => void;
  updateResumeVariant: (item: ResumeVariant) => void;
  archiveResumeVariant: (id: string) => void;
  addJobDescription: (item: JobDescriptionSnapshot) => void;
  addInterviewRound: (item: InterviewRound) => void;
  updateInterviewRound: (item: InterviewRound) => void;
  addNetworkingInteraction: (item: NetworkingInteraction) => void;
  addTargetCompany: (item: TargetCompany) => void;
  updateTargetCompany: (item: TargetCompany) => void;
  archiveTargetCompany: (id: string) => void;
  addCampaign: (item: CareerCampaign) => void;
  updateCampaign: (item: CareerCampaign) => void;
  addAchievement: (item: AchievementItem) => void;
  updateAchievement: (item: AchievementItem) => void;
  addOffer: (item: OfferItem) => void;
  updateOffer: (item: OfferItem) => void;
  addResearchSource: (item: ResearchSource) => void;
  addAsset: (item: CareerAsset) => void;
  updateAsset: (item: CareerAsset) => void;
  addResumeBullet: (item: ResumeBullet) => void;
  addNegotiation: (item: NegotiationLog) => void;
  updateNegotiation: (item: NegotiationLog) => void;
  addSprint: (item: WeeklySprint) => void;
  updateSprint: (item: WeeklySprint) => void;
  saveNarrative: (item: TransitionNarrative) => void;
  importState: (raw: string) => void;
  resetState: () => void;
  restoreBackup: (raw: string) => void;
  loadDemo: () => void;
  convertDemo: () => void;
  restoreLkg: () => Promise<void>;
  exportCorrupted: () => string | null;
  snapshotIfNeeded: () => void;
  undoLast: () => void;
}

function scheduleSave(get: () => CareerStore, set: (p: Partial<CareerStore>) => void) {
  if (saveTimer) clearTimeout(saveTimer);
  set({ saveStatus: "saving" });
  saveTimer = setTimeout(() => {
    void get().persistNow();
  }, 400);
}

export const useCareerStore = create<CareerStore>((set, get) => {
  const commit = (
    updater: (s: CareerOSState) => CareerOSState,
    opts?: { event?: ReturnType<typeof event>; persist?: boolean },
  ) => {
    const prev = get().state;
    let next = updater(prev);
    if (opts?.event) next = { ...next, activityEvents: [...next.activityEvents, opts.event] };
    next = { ...next, meta: { ...next.meta, updatedAt: nowIso() } };
    set({ state: next, undo: prev, lastError: null });
    if (opts?.persist === false) return;
    scheduleSave(get, set);
  };

  return {
    state: createEmptyState(),
    hydrated: false,
    saveStatus: "idle",
    recovery: null,
    lastError: null,
    undo: null,

    hydrate: async () => {
      const result: LoadResult = await repo.load();
      if (!result.ok) {
        set({ hydrated: true, recovery: result.recovery, saveStatus: "failed" });
        return;
      }
      set({ state: result.state, hydrated: true, recovery: null, saveStatus: "saved" });
      if (!unsub) {
        unsub = subscribeCrossTab((remote) => {
          const local = get().state;
          if (newerState(local, remote)) {
            applyingRemote = true;
            set({ state: remote, saveStatus: "saved" });
            applyingRemote = false;
          }
        });
      }
      get().snapshotIfNeeded();
    },

    persistNow: async () => {
      if (applyingRemote || get().recovery) return;
      try {
        await repo.save(get().state);
        publishCrossTab(get().state);
        set({ saveStatus: "saved", lastError: null });
      } catch (err) {
        const message = err instanceof Error ? err.message : "Save failed";
        set({ saveStatus: "failed", lastError: message });
      }
    },

    setState: (state, opts) => {
      set({ state, recovery: null });
      if (opts?.remote) return;
      if (opts?.persist === false) return;
      scheduleSave(get, set);
    },

    updateSettings: (patch) => commit((s) => ({ ...s, settings: { ...s.settings, ...patch } })),
    setUi: (patch) => commit((s) => ({ ...s, ui: { ...s.ui, ...patch } })),

    addSkill: (item) => commit((s) => ({ ...s, skills: upsert(s.skills, item) }), { event: event("Skill", `Added skill ${item.name}`, item.id) }),
    updateSkill: (item) => commit((s) => ({ ...s, skills: upsert(s.skills, item) })),
    archiveSkill: (id) => commit((s) => ({ ...s, skills: archiveList(s.skills, id) })),

    addProject: (item) => commit((s) => ({ ...s, projects: upsert(s.projects, item) }), { event: event("Project", `Added project ${item.title}`, item.id) }),
    updateProject: (item) =>
      commit((s) => ({ ...s, projects: upsert(s.projects, item) }), {
        event: item.status === "deployed" ? event("Project", `Deployed ${item.title}`, item.id) : undefined,
      }),
    archiveProject: (id) => commit((s) => ({ ...s, projects: archiveList(s.projects, id) })),

    addApplication: (item) =>
      commit((s) => ({ ...s, applications: upsert(s.applications, item) }), {
        event: event("Application", `Added ${item.company} · ${item.role}`, item.id),
      }),
    updateApplication: (item) =>
      commit((s) => ({ ...s, applications: upsert(s.applications, item) }), {
        event: event("Application", `${item.company} → ${item.status}`, item.id),
      }),
    archiveApplication: (id) => commit((s) => ({ ...s, applications: archiveList(s.applications, id) })),

    addContact: (item) =>
      commit((s) => ({ ...s, contacts: upsert(s.contacts, item) }), { event: event("Networking", `Added contact ${item.name}`, item.id) }),
    updateContact: (item) => commit((s) => ({ ...s, contacts: upsert(s.contacts, item) })),
    archiveContact: (id) => commit((s) => ({ ...s, contacts: archiveList(s.contacts, id) })),

    addCertification: (item) =>
      commit((s) => ({ ...s, certifications: upsert(s.certifications, item) }), {
        event: event("Certification", `Added ${item.name}`, item.id),
      }),
    updateCertification: (item) => commit((s) => ({ ...s, certifications: upsert(s.certifications, item) })),
    archiveCertification: (id) => commit((s) => ({ ...s, certifications: archiveList(s.certifications, id) })),

    addStarStory: (item) => commit((s) => ({ ...s, starStories: upsert(s.starStories, item) })),
    updateStarStory: (item) => commit((s) => ({ ...s, starStories: upsert(s.starStories, item) })),
    archiveStarStory: (id) => commit((s) => ({ ...s, starStories: archiveList(s.starStories, id) })),

    addResearchTopic: (item) =>
      commit((s) => ({ ...s, researchTopics: upsert(s.researchTopics, item) }), {
        event: event("Research", `Added topic ${item.title}`, item.id),
      }),
    updateResearchTopic: (item) => commit((s) => ({ ...s, researchTopics: upsert(s.researchTopics, item) })),
    archiveResearchTopic: (id) => commit((s) => ({ ...s, researchTopics: archiveList(s.researchTopics, id) })),

    addTask: (item) => commit((s) => ({ ...s, tasks: upsert(s.tasks, item) })),
    updateTask: (item) => commit((s) => ({ ...s, tasks: upsert(s.tasks, item) })),
    archiveTask: (id) => commit((s) => ({ ...s, tasks: archiveList(s.tasks, id) })),

    addInterviewQuestion: (item) => commit((s) => ({ ...s, interviewQuestions: upsert(s.interviewQuestions, item) })),
    updateInterviewQuestion: (item) => commit((s) => ({ ...s, interviewQuestions: upsert(s.interviewQuestions, item) })),
    archiveInterviewQuestion: (id) => commit((s) => ({ ...s, interviewQuestions: archiveList(s.interviewQuestions, id) })),

    updateRole: (item) => commit((s) => ({ ...s, targetRoles: upsert(s.targetRoles, item) })),

    addEvidence: (item) =>
      commit((s) => ({ ...s, evidenceArtifacts: upsert(s.evidenceArtifacts, item) }), {
        event: event("Evidence", `Added ${item.title}`, item.id),
      }),
    updateEvidence: (item) => commit((s) => ({ ...s, evidenceArtifacts: upsert(s.evidenceArtifacts, item) })),
    archiveEvidence: (id) => commit((s) => ({ ...s, evidenceArtifacts: archiveList(s.evidenceArtifacts, id) })),

    addLearningSession: (item) => commit((s) => ({ ...s, learningSessions: upsert(s.learningSessions, item) })),
    addProjectMilestone: (item) => commit((s) => ({ ...s, projectMilestones: upsert(s.projectMilestones, item) })),
    updateProjectMilestone: (item) => commit((s) => ({ ...s, projectMilestones: upsert(s.projectMilestones, item) })),
    addArchitectureDecision: (item) => commit((s) => ({ ...s, architectureDecisions: upsert(s.architectureDecisions, item) })),
    addProjectMetric: (item) => commit((s) => ({ ...s, projectMetrics: upsert(s.projectMetrics, item) })),

    addResumeVariant: (item) => commit((s) => ({ ...s, resumeVariants: upsert(s.resumeVariants, item) })),
    updateResumeVariant: (item) => commit((s) => ({ ...s, resumeVariants: upsert(s.resumeVariants, item) })),
    archiveResumeVariant: (id) => commit((s) => ({ ...s, resumeVariants: archiveList(s.resumeVariants, id) })),

    addJobDescription: (item) => commit((s) => ({ ...s, jobDescriptions: upsert(s.jobDescriptions, item) })),
    addInterviewRound: (item) =>
      commit((s) => ({ ...s, interviewRounds: upsert(s.interviewRounds, item) }), {
        event: event("Interview", `Round ${item.roundNumber} ${item.type}`, item.id),
      }),
    updateInterviewRound: (item) => commit((s) => ({ ...s, interviewRounds: upsert(s.interviewRounds, item) })),
    addNetworkingInteraction: (item) =>
      commit((s) => ({ ...s, networkingInteractions: upsert(s.networkingInteractions, item) }), {
        event: event("Networking", item.type, item.id),
      }),

    addTargetCompany: (item) => commit((s) => ({ ...s, targetCompanies: upsert(s.targetCompanies, item) })),
    updateTargetCompany: (item) => commit((s) => ({ ...s, targetCompanies: upsert(s.targetCompanies, item) })),
    archiveTargetCompany: (id) => commit((s) => ({ ...s, targetCompanies: archiveList(s.targetCompanies, id) })),

    addCampaign: (item) => commit((s) => ({ ...s, campaigns: upsert(s.campaigns, item) })),
    updateCampaign: (item) => commit((s) => ({ ...s, campaigns: upsert(s.campaigns, item) })),

    addAchievement: (item) => commit((s) => ({ ...s, achievements: upsert(s.achievements, item) })),
    updateAchievement: (item) => commit((s) => ({ ...s, achievements: upsert(s.achievements, item) })),

    addOffer: (item) => commit((s) => ({ ...s, offers: upsert(s.offers, item) })),
    updateOffer: (item) => commit((s) => ({ ...s, offers: upsert(s.offers, item) })),

    addResearchSource: (item) => commit((s) => ({ ...s, researchSources: upsert(s.researchSources, item) })),
    addAsset: (item) => commit((s) => ({ ...s, careerAssets: upsert(s.careerAssets, item) })),
    updateAsset: (item) => commit((s) => ({ ...s, careerAssets: upsert(s.careerAssets, item) })),
    addResumeBullet: (item) => commit((s) => ({ ...s, resumeBullets: upsert(s.resumeBullets, item) })),
    addNegotiation: (item) => commit((s) => ({ ...s, negotiationLogs: upsert(s.negotiationLogs, item) })),
    updateNegotiation: (item) => commit((s) => ({ ...s, negotiationLogs: upsert(s.negotiationLogs, item) })),
    addSprint: (item) =>
      commit((s) => ({ ...s, weeklySprints: upsert(s.weeklySprints, item) }), {
        event: event("Sprint", item.title, item.id),
      }),
    updateSprint: (item) => commit((s) => ({ ...s, weeklySprints: upsert(s.weeklySprints, item) })),
    saveNarrative: (item) => commit((s) => ({ ...s, transitionNarratives: upsert(s.transitionNarratives, item) })),

    importState: (raw) => {
      const imported = parseImportedState(raw);
      set({ state: imported, recovery: null, undo: get().state });
      scheduleSave(get, set);
    },
    resetState: () => {
      set({ state: resetWorkspace(), recovery: null, undo: get().state });
      scheduleSave(get, set);
    },
    restoreBackup: (raw) => get().importState(raw),
    loadDemo: () => {
      const demo = createDemoState();
      set({ state: demo, recovery: null, undo: get().state });
      scheduleSave(get, set);
    },
    convertDemo: () =>
      commit((s) => ({
        ...s,
        ui: { ...s.ui, demoMode: false },
        skills: s.skills.map((x) => ({ ...x, tags: (x.tags ?? []).filter((t) => t !== "demo") })),
      })),
    restoreLkg: async () => {
      const state = await restoreLastKnownGood(repo);
      set({ state, recovery: null, saveStatus: "saved" });
    },
    exportCorrupted: () => repo.readCorrupted(),
    snapshotIfNeeded: () => {
      const s = get().state;
      const last = s.scoreSnapshots.at(-1);
      const today = nowIso().slice(0, 10);
      if (last && last.capturedAt.slice(0, 10) === today) return;
      const snap = captureSnapshot(s, roleScoreMap(s));
      commit((st) => ({ ...st, scoreSnapshots: [...st.scoreSnapshots, snap] }));
    },
    undoLast: () => {
      const prev = get().undo;
      if (!prev) return;
      set({ state: prev, undo: null });
      scheduleSave(get, set);
    },
  };
});

export function useReadiness() {
  return computeReadiness(useCareerStore.getState().state);
}
