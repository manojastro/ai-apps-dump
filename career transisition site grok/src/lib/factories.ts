import { TARGET_ROLE_NAMES } from "./constants";
import { addDaysIso, isoDate, nowInKolkata } from "./dates";
import { createId, timestamps } from "./ids";
import type {
  CareerTask,
  CertificationItem,
  EvidenceArtifact,
  InterviewQuestion,
  JobApplication,
  NetworkingContact,
  ProjectItem,
  ResearchTopic,
  SkillItem,
  StarStory,
  TargetCompany,
} from "@/types/career";

export function newSkill(partial: Partial<SkillItem> = {}): SkillItem {
  return {
    id: createId("sk"),
    ...timestamps(),
    category: "agents",
    name: "",
    sourceLearned: "",
    sourceUrl: "",
    summary: "",
    whatNext: "",
    mappedRoles: [TARGET_ROLE_NAMES[0]],
    status: "to_learn",
    ...partial,
  };
}

export function newProject(partial: Partial<ProjectItem> = {}): ProjectItem {
  return {
    id: createId("pr"),
    ...timestamps(),
    title: "",
    category: "Agents",
    targetRole: TARGET_ROLE_NAMES[0],
    techStack: [],
    useCase: "",
    architectureSummary: "",
    githubUrl: "",
    liveUrl: "",
    starPitch: "",
    status: "planned",
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
    ...partial,
  };
}

export function newJob(partial: Partial<JobApplication> = {}): JobApplication {
  return {
    id: createId("job"),
    ...timestamps(),
    company: "",
    tier: "GCC",
    role: TARGET_ROLE_NAMES[0],
    platform: "LinkedIn",
    dateApplied: isoDate(nowInKolkata()),
    nextFollowUpDate: addDaysIso(isoDate(nowInKolkata()), 5),
    status: "Identified",
    notes: "",
    interest: 3,
    ...partial,
  };
}

export function newContact(partial: Partial<NetworkingContact> = {}): NetworkingContact {
  return {
    id: createId("ct"),
    ...timestamps(),
    name: "",
    designation: "",
    company: "",
    medium: "LinkedIn",
    contactDate: isoDate(nowInKolkata()),
    outreachFormulaUsed: true,
    status: "Reached Out",
    helpfulRating: "Medium",
    keyTakeaway: "",
    ...partial,
  };
}

export function newEvidence(partial: Partial<EvidenceArtifact> = {}): EvidenceArtifact {
  return {
    id: createId("ev"),
    ...timestamps(),
    title: "",
    type: "GitHub Repository",
    description: "",
    skillIds: [],
    competencyIds: [],
    mappedRoleIds: [],
    strength: "Draft",
    ...partial,
  };
}

export function newStar(partial: Partial<StarStory> = {}): StarStory {
  return {
    id: createId("star"),
    ...timestamps(),
    category: "System Architecture",
    title: "",
    situation: "",
    task: "",
    action: "",
    result: "",
    techNotes: "",
    ...partial,
  };
}

export function newResearch(partial: Partial<ResearchTopic> = {}): ResearchTopic {
  return {
    id: createId("rs"),
    ...timestamps(),
    title: "",
    coreConcept: "",
    mathOrFormula: "",
    tradeOffs: "",
    interviewTalkingPoints: "",
    isMastered: false,
    ...partial,
  };
}

export function newQuestion(partial: Partial<InterviewQuestion> = {}): InterviewQuestion {
  return {
    id: createId("iq"),
    ...timestamps(),
    category: "Agents",
    question: "",
    answer: "",
    confidence: 2,
    mastered: false,
    ...partial,
  };
}

export function newTask(partial: Partial<CareerTask> = {}): CareerTask {
  return {
    id: createId("tk"),
    ...timestamps(),
    title: "",
    category: "Project",
    priority: "High",
    completed: false,
    ...partial,
  };
}

export function newCompany(partial: Partial<TargetCompany> = {}): TargetCompany {
  return {
    id: createId("co"),
    ...timestamps(),
    name: "",
    tier: "GCC",
    priority: "High",
    targetRoleIds: [],
    locations: [],
    whyTarget: "",
    notes: "",
    ...partial,
  };
}

export function newCert(partial: Partial<CertificationItem> = {}): CertificationItem {
  return {
    id: createId("cert"),
    ...timestamps(),
    name: "",
    provider: "Microsoft",
    code: "",
    status: "Not Started",
    whatNext: "",
    mappedTrack: "Option A: Azure Enterprise",
    ...partial,
  };
}

export function nextReviewForConfidence(confidence: 1 | 2 | 3 | 4 | 5) {
  const days = confidence <= 2 ? 2 : confidence === 3 ? 5 : confidence === 4 ? 10 : 21;
  return addDaysIso(isoDate(nowInKolkata()), days);
}
