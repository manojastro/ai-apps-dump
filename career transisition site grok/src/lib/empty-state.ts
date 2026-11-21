import { CATALOG_COMPETENCIES, CATALOG_ROLES } from "@/data/catalog";
import { SCHEMA_VERSION, TARGET_LOCATIONS, TARGET_ROLE_NAMES } from "./constants";
import { nowIso } from "./ids";
import type { CareerOSState, CareerSettings } from "@/types/career";

export function defaultSettings(): CareerSettings {
  return {
    baselineCtc: 11,
    targetMinCtc: 20,
    targetMaxCtc: 25,
    stretchCtc: 35,
    targetRoles: [...TARGET_ROLE_NAMES],
    targetLocations: [...TARGET_LOCATIONS],
    transitionStartDate: "2026-01-01",
    targetSwitchDate: "2026-12-31",
    weeklyLearningHoursTarget: 10,
    weeklyApplicationsTarget: 8,
    weeklyNetworkingTarget: 5,
    weeklyInterviewPracticeTarget: 3,
    weeklyAvailableHours: 20,
    maxActiveProjects: 3,
    maxActiveCourses: 2,
    maxPrimaryRoles: 3,
    locale: "en-IN",
    timezone: "Asia/Kolkata",
    currency: "INR",
    offerWeightAlignment: 30,
    offerWeightComp: 25,
    offerWeightLearning: 20,
    offerWeightScope: 15,
    offerWeightLocation: 10,
  };
}

export function createEmptyState(partial?: Partial<CareerOSState>): CareerOSState {
  const now = nowIso();
  return {
    version: SCHEMA_VERSION,
    settings: defaultSettings(),
    ui: {
      onboardingComplete: false,
      demoMode: false,
      privacyMode: false,
      sidebarCollapsed: false,
    },
    meta: { updatedAt: now },
    skills: [],
    projects: [],
    applications: [],
    contacts: [],
    certifications: [],
    starStories: [],
    researchTopics: [],
    weeklySprints: [],
    tasks: [],
    interviewQuestions: [],
    targetRoles: CATALOG_ROLES.map((r) => ({ ...r })),
    competencies: CATALOG_COMPETENCIES.map((c) => ({ ...c })),
    evidenceArtifacts: [],
    learningSessions: [],
    projectMilestones: [],
    architectureDecisions: [],
    projectMetrics: [],
    resumeVariants: [],
    jobDescriptions: [],
    interviewRounds: [],
    networkingInteractions: [],
    targetCompanies: [],
    campaigns: [],
    achievements: [],
    offers: [],
    researchSources: [],
    activityEvents: [],
    scoreSnapshots: [],
    careerAssets: [],
    resumeBullets: [],
    negotiationLogs: [],
    transitionNarratives: [],
    attachments: [],
    ...partial,
  };
}
