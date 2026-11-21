import { z } from "zod";
import { SCHEMA_VERSION } from "./constants";
import type { CareerOSState } from "@/types/career";

const base = {
  id: z.string().min(1),
  createdAt: z.string().min(1),
  updatedAt: z.string().min(1),
  archivedAt: z.string().optional(),
  tags: z.array(z.string()).optional(),
};

const rating = z.union([z.literal(1), z.literal(2), z.literal(3), z.literal(4), z.literal(5)]);

export const skillSchema = z.object({
  ...base,
  category: z.enum(["core_python", "intermediate_python", "llm_orchestration", "agents", "rag", "serving_llmops"]),
  name: z.string().min(1),
  sourceLearned: z.string(),
  sourceUrl: z.string(),
  summary: z.string(),
  whatNext: z.string(),
  mappedRoles: z.array(z.string()),
  status: z.enum(["to_learn", "in_progress", "mastered"]),
});

export const projectSchema = z.object({
  ...base,
  title: z.string().min(1),
  category: z.enum(["AIOps", "RAG", "Agents", "Security_LLMOps", "FullStack_SaaS"]),
  targetRole: z.string(),
  techStack: z.array(z.string()),
  useCase: z.string(),
  architectureSummary: z.string(),
  githubUrl: z.string(),
  liveUrl: z.string(),
  starPitch: z.string(),
  status: z.enum(["planned", "in_progress", "deployed"]),
  maturity: z.enum(["Tutorial", "Prototype", "Portfolio Ready", "Production Grade"]),
  evaluationNotes: z.string(),
  testingNotes: z.string(),
  safetyNotes: z.string(),
  observabilityNotes: z.string(),
  failureHandlingNotes: z.string(),
  documentationNotes: z.string(),
  interviewDefense30s: z.string(),
  interviewDefense2m: z.string(),
  interviewDefenseDeep: z.string(),
});

export const applicationSchema = z.object({
  ...base,
  company: z.string().min(1),
  tier: z.enum(["GCC", "Enterprise IT", "AI Startup", "Consulting"]),
  role: z.string().min(1),
  platform: z.string(),
  jobUrl: z.string().optional(),
  referralContact: z.string().optional(),
  referralContactId: z.string().optional(),
  resumeVariantId: z.string().optional(),
  dateApplied: z.string(),
  nextFollowUpDate: z.string(),
  status: z.enum(["Identified", "Referred", "Applied", "Screening", "Technical", "Offer", "Rejected"]),
  notes: z.string(),
  outcomeReason: z
    .enum([
      "No Response",
      "Role Closed",
      "Skill Gap",
      "Experience Mismatch",
      "Compensation",
      "Location",
      "Failed Interview",
      "Candidate Withdrew",
      "Accepted Another Offer",
      "Unknown",
      "Other",
    ])
    .optional(),
  location: z.string().optional(),
  compensationText: z.string().optional(),
  interest: rating.optional(),
  jdCaptured: z.boolean().optional(),
  evidenceReviewed: z.boolean().optional(),
  referralAttempted: z.boolean().optional(),
  campaignId: z.string().optional(),
  companyId: z.string().optional(),
});

export const contactSchema = z.object({
  ...base,
  name: z.string().min(1),
  designation: z.string(),
  company: z.string(),
  medium: z.enum(["LinkedIn", "Topmate", "Hackathon", "Email", "In-Person"]),
  contactDate: z.string(),
  outreachFormulaUsed: z.boolean(),
  status: z.enum(["Reached Out", "Connected", "Call Scheduled", "Mentorship Active"]),
  helpfulRating: z.enum(["High", "Medium", "Low", "Unresponsive"]),
  keyTakeaway: z.string(),
  nextTouchpointDate: z.string().optional(),
  email: z.string().optional(),
  linkedinUrl: z.string().optional(),
});

export const certificationSchema = z.object({
  ...base,
  name: z.string().min(1),
  provider: z.enum(["Microsoft", "AWS", "Azure", "Databricks", "NVIDIA"]),
  code: z.string(),
  status: z.enum(["Not Started", "Studying", "Scheduled", "Certified"]),
  examDate: z.string().optional(),
  credentialUrl: z.string().optional(),
  whatNext: z.string(),
  mappedTrack: z.enum([
    "Option A: Azure Enterprise",
    "Option B: Cloud-Agnostic AWS",
    "Option C: Agentic Specialist",
  ]),
});

export const starStorySchema = z.object({
  ...base,
  category: z.enum(["Outage/RCA", "System Architecture", "Automation Impact", "Conflict/Governance", "LLM Trade-Offs"]),
  title: z.string().min(1),
  situation: z.string(),
  task: z.string(),
  action: z.string(),
  result: z.string(),
  techNotes: z.string(),
});

export const researchTopicSchema = z.object({
  ...base,
  title: z.string().min(1),
  coreConcept: z.string(),
  mathOrFormula: z.string(),
  tradeOffs: z.string(),
  interviewTalkingPoints: z.string(),
  isMastered: z.boolean(),
  category: z.string().optional(),
});

export const settingsSchema = z.object({
  baselineCtc: z.number(),
  targetMinCtc: z.number(),
  targetMaxCtc: z.number(),
  stretchCtc: z.number(),
  targetRoles: z.array(z.string()),
  targetLocations: z.array(z.string()),
  transitionStartDate: z.string(),
  targetSwitchDate: z.string().optional(),
  weeklyLearningHoursTarget: z.number(),
  weeklyApplicationsTarget: z.number(),
  weeklyNetworkingTarget: z.number(),
  weeklyInterviewPracticeTarget: z.number(),
  weeklyAvailableHours: z.number(),
  maxActiveProjects: z.number(),
  maxActiveCourses: z.number(),
  maxPrimaryRoles: z.number(),
  locale: z.string(),
  timezone: z.string(),
  currency: z.string(),
  linkedinUrl: z.string().optional(),
  githubUrl: z.string().optional(),
  portfolioUrl: z.string().optional(),
  recruiterIntro: z.string().optional(),
  offerWeightAlignment: z.number(),
  offerWeightComp: z.number(),
  offerWeightLearning: z.number(),
  offerWeightScope: z.number(),
  offerWeightLocation: z.number(),
});

export const taskSchema = z.object({
  ...base,
  title: z.string().min(1),
  category: z.enum(["Learning", "Project", "Application", "Networking", "Interview", "Research"]),
  priority: z.enum(["Critical", "High", "Medium", "Low"]),
  dueDate: z.string().optional(),
  completed: z.boolean(),
  completedAt: z.string().optional(),
  linkedEntityId: z.string().optional(),
  linkedRoleIds: z.array(z.string()).optional(),
  blockedByTaskIds: z.array(z.string()).optional(),
  estimatedMinutes: z.number().optional(),
  waitingOn: z.string().optional(),
});

export const sprintSchema = z.object({
  ...base,
  weekStart: z.string(),
  title: z.string(),
  objectives: z.array(z.string()),
  completedObjectives: z.array(z.string()),
  learningHours: z.number(),
  applicationsSubmitted: z.number(),
  networkingActions: z.number(),
  interviewSessions: z.number(),
  buildingHours: z.number(),
  jobSearchHours: z.number(),
  availableHours: z.number(),
  retrospective: z.string(),
  movedForward: z.string().optional(),
  blocked: z.string().optional(),
  producedInterviews: z.string().optional(),
  strengthenedCapability: z.string().optional(),
  createdEvidence: z.string().optional(),
  shouldStop: z.string().optional(),
  nextWeekPriority: z.string().optional(),
});

export const interviewQuestionSchema = z.object({
  ...base,
  category: z.enum([
    "Python",
    "LLM",
    "RAG",
    "Agents",
    "System Design",
    "Cloud",
    "MLOps",
    "Behavioral",
    "Backend",
    "Security",
    "Observability",
    "Evaluation",
  ]),
  question: z.string().min(1),
  answer: z.string(),
  confidence: rating,
  lastPracticed: z.string().optional(),
  nextReviewDate: z.string().optional(),
  mastered: z.boolean(),
});

export const roleSchema = z.object({
  ...base,
  name: z.string().min(1),
  priority: z.enum(["Primary", "Secondary", "Stretch", "Parked"]),
  active: z.boolean(),
  targetSeniority: z.enum(["Mid", "Senior", "Lead", "Architect"]),
  competencyRequirements: z.array(
    z.object({
      competencyId: z.string(),
      importance: rating,
      targetLevel: rating,
      evidenceRequired: z.boolean(),
    }),
  ),
  notes: z.string(),
});

export const competencySchema = z.object({
  ...base,
  name: z.string().min(1),
  domain: z.enum([
    "Python",
    "LLM",
    "RAG",
    "Agents",
    "Evaluation",
    "LLMOps",
    "Cloud",
    "System Design",
    "Security",
    "Data",
    "Backend",
    "Observability",
    "Communication",
  ]),
  description: z.string(),
  skillIds: z.array(z.string()),
  researchTopicIds: z.array(z.string()),
});

export const evidenceSchema = z.object({
  ...base,
  title: z.string().min(1),
  type: z.enum([
    "GitHub Repository",
    "Live Demo",
    "Architecture Diagram",
    "Benchmark",
    "Evaluation Report",
    "Case Study",
    "Resume Bullet",
    "STAR Story",
    "Technical Article",
    "Credential",
    "Presentation",
    "Other",
  ]),
  url: z.string().optional(),
  description: z.string(),
  projectId: z.string().optional(),
  skillIds: z.array(z.string()),
  competencyIds: z.array(z.string()),
  mappedRoleIds: z.array(z.string()),
  strength: z.enum(["Draft", "Usable", "Strong"]),
  lastVerifiedAt: z.string().optional(),
});

export const learningSessionSchema = z.object({
  ...base,
  skillId: z.string().optional(),
  researchTopicId: z.string().optional(),
  date: z.string(),
  durationMinutes: z.number(),
  activity: z.enum(["Course", "Reading", "Coding", "Lab", "Revision", "Interview Practice"]),
  notes: z.string(),
  evidenceCreated: z.string().optional(),
});

export const milestoneSchema = z.object({
  ...base,
  projectId: z.string(),
  title: z.string().min(1),
  category: z.enum(["Architecture", "Implementation", "Evaluation", "Testing", "Deployment", "Documentation", "Demo"]),
  dueDate: z.string().optional(),
  status: z.enum(["Not Started", "In Progress", "Blocked", "Complete"]),
  notes: z.string(),
});

export const adrSchema = z.object({
  ...base,
  projectId: z.string(),
  title: z.string().min(1),
  context: z.string(),
  decision: z.string(),
  alternativesConsidered: z.string(),
  tradeOffs: z.string(),
  consequences: z.string(),
});

export const metricSchema = z.object({
  ...base,
  projectId: z.string(),
  name: z.string().min(1),
  baseline: z.string().optional(),
  achieved: z.string().optional(),
  unit: z.string().optional(),
  methodology: z.string(),
  notes: z.string(),
});

export const resumeSchema = z.object({
  ...base,
  name: z.string().min(1),
  targetRoleIds: z.array(z.string()),
  versionLabel: z.string(),
  externalUrl: z.string().optional(),
  summary: z.string(),
  selectedProjectIds: z.array(z.string()),
  selectedEvidenceIds: z.array(z.string()),
  notes: z.string(),
  isActive: z.boolean(),
});

export const jdSchema = z.object({
  ...base,
  applicationId: z.string(),
  sourceUrl: z.string().optional(),
  capturedAt: z.string(),
  rawText: z.string(),
  requiredSkills: z.array(z.string()),
  preferredSkills: z.array(z.string()),
  responsibilities: z.array(z.string()),
  locationText: z.string().optional(),
  compensationText: z.string().optional(),
  notes: z.string(),
});

export const roundSchema = z.object({
  ...base,
  applicationId: z.string(),
  roundNumber: z.number(),
  type: z.enum([
    "Recruiter",
    "Hiring Manager",
    "Technical",
    "Coding",
    "System Design",
    "AI / ML",
    "Project Discussion",
    "Behavioral",
    "Assignment",
    "HR",
    "Other",
  ]),
  scheduledAt: z.string().optional(),
  completedAt: z.string().optional(),
  interviewerName: z.string().optional(),
  interviewerRole: z.string().optional(),
  outcome: z.enum(["Upcoming", "Passed", "Failed", "Pending", "Cancelled"]),
  questionsAsked: z.array(z.string()),
  strongAreas: z.array(z.string()),
  weakAreas: z.array(z.string()),
  notes: z.string(),
  followUpDate: z.string().optional(),
  wentWell: z.string().optional(),
  difficult: z.string().optional(),
  exposedGap: z.string().optional(),
  shouldRevise: z.string().optional(),
});

export const interactionSchema = z.object({
  ...base,
  contactId: z.string(),
  date: z.string(),
  type: z.enum(["Message", "Reply", "Call", "Referral Ask", "Referral", "Meeting", "Follow-Up"]),
  summary: z.string(),
  nextAction: z.string().optional(),
  nextActionDate: z.string().optional(),
});

export const companySchema = z.object({
  ...base,
  name: z.string().min(1),
  tier: z.enum(["GCC", "Enterprise IT", "AI Startup", "Consulting", "Product"]),
  priority: z.enum(["Dream", "High", "Medium", "Watch"]),
  targetRoleIds: z.array(z.string()),
  careerUrl: z.string().optional(),
  locations: z.array(z.string()),
  whyTarget: z.string(),
  notes: z.string(),
});

export const campaignSchema = z.object({
  ...base,
  name: z.string().min(1),
  startDate: z.string(),
  endDate: z.string().optional(),
  targetRoleIds: z.array(z.string()),
  targetCompanyIds: z.array(z.string()),
  weeklyApplicationTarget: z.number(),
  weeklyNetworkingTarget: z.number(),
  resumeVariantIds: z.array(z.string()),
  hypothesis: z.string(),
  retrospective: z.string(),
  status: z.enum(["Planned", "Active", "Completed"]),
});

export const achievementSchema = z.object({
  ...base,
  title: z.string().min(1),
  context: z.string(),
  action: z.string(),
  result: z.string(),
  technologies: z.array(z.string()),
  transferableCompetencies: z.array(z.string()),
  mappedRoleIds: z.array(z.string()),
  quantified: z.boolean(),
});

export const offerSchema = z.object({
  ...base,
  applicationId: z.string(),
  roleTitle: z.string(),
  company: z.string(),
  fixedCtc: z.number().optional(),
  variableCtc: z.number().optional(),
  joiningBonus: z.number().optional(),
  equityEstimatedAnnual: z.number().optional(),
  totalFirstYear: z.number().optional(),
  totalRecurring: z.number().optional(),
  location: z.string().optional(),
  workMode: z.enum(["Remote", "Hybrid", "Office"]).optional(),
  joiningDate: z.string().optional(),
  aiRoleAlignment: rating,
  learningPotential: rating,
  roleScope: rating,
  notes: z.string(),
});

export const researchSourceSchema = z.object({
  ...base,
  researchTopicId: z.string(),
  title: z.string().min(1),
  url: z.string().optional(),
  sourceType: z.enum(["Documentation", "Paper", "Book", "Course", "Repository", "Article", "Video", "Community", "Other"]),
  publishedDate: z.string().optional(),
  reviewedAt: z.string().optional(),
  credibility: z.enum(["Primary", "Strong Secondary", "Community", "Unverified"]),
  takeaway: z.string(),
});

export const activitySchema = z.object({
  ...base,
  occurredAt: z.string(),
  category: z.enum(["Skill", "Project", "Application", "Interview", "Networking", "Research", "Certification", "Sprint", "Evidence"]),
  action: z.string(),
  entityId: z.string().optional(),
  metadata: z.record(z.union([z.string(), z.number(), z.boolean()])).optional(),
});

export const snapshotSchema = z.object({
  id: z.string(),
  capturedAt: z.string(),
  globalReadiness: z.number(),
  capability: z.number(),
  evidence: z.number(),
  interview: z.number(),
  positioning: z.number(),
  marketExecution: z.number(),
  roleScores: z.record(z.number()),
});

export const uiSchema = z.object({
  onboardingComplete: z.boolean(),
  demoMode: z.boolean(),
  privacyMode: z.boolean(),
  transitionPhaseOverride: z
    .enum([
      "Foundation",
      "Building",
      "Evidence",
      "Market Activation",
      "Interview Conversion",
      "Offer Optimization",
      "Transition Complete",
    ])
    .optional(),
  sidebarCollapsed: z.boolean(),
});

export const careerAssetSchema = z.object({
  ...base,
  kind: z.enum(["Resume", "LinkedIn", "GitHub", "Portfolio", "Credential", "Recruiter Intro", "Transition Narrative"]),
  title: z.string(),
  targetRoleIds: z.array(z.string()),
  url: z.string().optional(),
  status: z.enum(["Draft", "Review", "Ready"]),
  lastReviewedAt: z.string().optional(),
  completeness: z.number(),
  notes: z.string(),
});

export const resumeBulletSchema = z.object({
  ...base,
  text: z.string(),
  projectId: z.string().optional(),
  achievementId: z.string().optional(),
  mappedRoleIds: z.array(z.string()),
  competencyIds: z.array(z.string()),
  quantified: z.boolean(),
});

export const negotiationSchema = z.object({
  ...base,
  offerId: z.string(),
  initialOffer: z.number().optional(),
  candidateExpectation: z.number().optional(),
  counter: z.number().optional(),
  recruiterResponse: z.string().optional(),
  final: z.number().optional(),
  decision: z.enum(["Pending", "Accepted", "Declined"]).optional(),
  notes: z.string(),
});

export const narrativeSchema = z.object({
  ...base,
  intro30s: z.string(),
  story90s: z.string(),
  whyAI: z.string(),
  whyNow: z.string(),
  whySenior: z.string(),
  howOpsStrengthens: z.string(),
  evidenceIds: z.array(z.string()),
});

export const attachmentSchema = z.object({
  ...base,
  name: z.string(),
  mimeType: z.string(),
  size: z.number(),
  linkedEntityId: z.string().optional(),
});

export const careerStateSchema: z.ZodType<CareerOSState> = z.object({
  version: z.number(),
  settings: settingsSchema,
  ui: uiSchema,
  meta: z.object({
    lastSavedAt: z.string().optional(),
    lastBackupAt: z.string().optional(),
    lastKnownGoodAt: z.string().optional(),
    updatedAt: z.string(),
  }),
  skills: z.array(skillSchema),
  projects: z.array(projectSchema),
  applications: z.array(applicationSchema),
  contacts: z.array(contactSchema),
  certifications: z.array(certificationSchema),
  starStories: z.array(starStorySchema),
  researchTopics: z.array(researchTopicSchema),
  weeklySprints: z.array(sprintSchema),
  tasks: z.array(taskSchema),
  interviewQuestions: z.array(interviewQuestionSchema),
  targetRoles: z.array(roleSchema),
  competencies: z.array(competencySchema),
  evidenceArtifacts: z.array(evidenceSchema),
  learningSessions: z.array(learningSessionSchema),
  projectMilestones: z.array(milestoneSchema),
  architectureDecisions: z.array(adrSchema),
  projectMetrics: z.array(metricSchema),
  resumeVariants: z.array(resumeSchema),
  jobDescriptions: z.array(jdSchema),
  interviewRounds: z.array(roundSchema),
  networkingInteractions: z.array(interactionSchema),
  targetCompanies: z.array(companySchema),
  campaigns: z.array(campaignSchema),
  achievements: z.array(achievementSchema),
  offers: z.array(offerSchema),
  researchSources: z.array(researchSourceSchema),
  activityEvents: z.array(activitySchema),
  scoreSnapshots: z.array(snapshotSchema),
  careerAssets: z.array(careerAssetSchema),
  resumeBullets: z.array(resumeBulletSchema),
  negotiationLogs: z.array(negotiationSchema),
  transitionNarratives: z.array(narrativeSchema),
  attachments: z.array(attachmentSchema),
});

export function parseCareerState(input: unknown) {
  return careerStateSchema.safeParse(input);
}

export function assertCareerState(input: unknown): CareerOSState {
  return careerStateSchema.parse(input);
}

export function isCurrentSchema(input: unknown): input is CareerOSState {
  const parsed = careerStateSchema.safeParse(input);
  return parsed.success && parsed.data.version === SCHEMA_VERSION;
}

const SENSITIVE_KEYS = ["apiKey", "api_key", "secret", "token", "OPENAI", "XAI_API_KEY", "password"];

export function stripSecrets<T>(value: T): T {
  if (Array.isArray(value)) return value.map(stripSecrets) as T;
  if (value && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      if (SENSITIVE_KEYS.some((s) => k.toLowerCase().includes(s.toLowerCase()))) continue;
      out[k] = stripSecrets(v);
    }
    return out as T;
  }
  return value;
}
