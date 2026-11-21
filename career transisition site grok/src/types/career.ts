export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
  archivedAt?: string;
  tags?: string[];
}

export type SkillCategory =
  | "core_python"
  | "intermediate_python"
  | "llm_orchestration"
  | "agents"
  | "rag"
  | "serving_llmops";

export type SkillStatus = "to_learn" | "in_progress" | "mastered";

export interface SkillItem extends BaseEntity {
  category: SkillCategory;
  name: string;
  sourceLearned: string;
  sourceUrl: string;
  summary: string;
  whatNext: string;
  mappedRoles: string[];
  status: SkillStatus;
}

export type ProjectCategory =
  | "AIOps"
  | "RAG"
  | "Agents"
  | "Security_LLMOps"
  | "FullStack_SaaS";

export type ProjectStatus = "planned" | "in_progress" | "deployed";

export type ProjectMaturity =
  | "Tutorial"
  | "Prototype"
  | "Portfolio Ready"
  | "Production Grade";

export interface ProjectItem extends BaseEntity {
  title: string;
  category: ProjectCategory;
  targetRole: string;
  techStack: string[];
  useCase: string;
  architectureSummary: string;
  githubUrl: string;
  liveUrl: string;
  starPitch: string;
  status: ProjectStatus;
  maturity: ProjectMaturity;
  evaluationNotes: string;
  testingNotes: string;
  safetyNotes: string;
  observabilityNotes: string;
  failureHandlingNotes: string;
  documentationNotes: string;
  interviewDefense30s: string;
  interviewDefense2m: string;
  interviewDefenseDeep: string;
}

export type CompanyTier =
  | "GCC"
  | "Enterprise IT"
  | "AI Startup"
  | "Consulting"
  | "Product";

export type ApplicationStatus =
  | "Identified"
  | "Referred"
  | "Applied"
  | "Screening"
  | "Technical"
  | "Offer"
  | "Rejected";

export type ApplicationOutcomeReason =
  | "No Response"
  | "Role Closed"
  | "Skill Gap"
  | "Experience Mismatch"
  | "Compensation"
  | "Location"
  | "Failed Interview"
  | "Candidate Withdrew"
  | "Accepted Another Offer"
  | "Unknown"
  | "Other";

export interface JobApplication extends BaseEntity {
  company: string;
  tier: Exclude<CompanyTier, "Product">;
  role: string;
  platform: string;
  jobUrl?: string;
  referralContact?: string;
  referralContactId?: string;
  resumeVariantId?: string;
  dateApplied: string;
  nextFollowUpDate: string;
  status: ApplicationStatus;
  notes: string;
  outcomeReason?: ApplicationOutcomeReason;
  location?: string;
  compensationText?: string;
  interest?: 1 | 2 | 3 | 4 | 5;
  jdCaptured?: boolean;
  evidenceReviewed?: boolean;
  referralAttempted?: boolean;
  campaignId?: string;
  companyId?: string;
}

export type ContactMedium =
  | "LinkedIn"
  | "Topmate"
  | "Hackathon"
  | "Email"
  | "In-Person";

export type ContactStatus =
  | "Reached Out"
  | "Connected"
  | "Call Scheduled"
  | "Mentorship Active";

export type HelpfulRating = "High" | "Medium" | "Low" | "Unresponsive";

export interface NetworkingContact extends BaseEntity {
  name: string;
  designation: string;
  company: string;
  medium: ContactMedium;
  contactDate: string;
  outreachFormulaUsed: boolean;
  status: ContactStatus;
  helpfulRating: HelpfulRating;
  keyTakeaway: string;
  nextTouchpointDate?: string;
  email?: string;
  linkedinUrl?: string;
}

export type CertificationProvider =
  | "Microsoft"
  | "AWS"
  | "Azure"
  | "Databricks"
  | "NVIDIA";

export type CertificationStatus =
  | "Not Started"
  | "Studying"
  | "Scheduled"
  | "Certified";

export type CertificationTrack =
  | "Option A: Azure Enterprise"
  | "Option B: Cloud-Agnostic AWS"
  | "Option C: Agentic Specialist";

export interface CertificationItem extends BaseEntity {
  name: string;
  provider: CertificationProvider;
  code: string;
  status: CertificationStatus;
  examDate?: string;
  credentialUrl?: string;
  whatNext: string;
  mappedTrack: CertificationTrack;
}

export type StarCategory =
  | "Outage/RCA"
  | "System Architecture"
  | "Automation Impact"
  | "Conflict/Governance"
  | "LLM Trade-Offs";

export interface StarStory extends BaseEntity {
  category: StarCategory;
  title: string;
  situation: string;
  task: string;
  action: string;
  result: string;
  techNotes: string;
}

export interface ResearchTopic extends BaseEntity {
  title: string;
  coreConcept: string;
  mathOrFormula: string;
  tradeOffs: string;
  interviewTalkingPoints: string;
  isMastered: boolean;
  category?: string;
}

export interface CareerSettings {
  baselineCtc: number;
  targetMinCtc: number;
  targetMaxCtc: number;
  stretchCtc: number;
  targetRoles: string[];
  targetLocations: string[];
  transitionStartDate: string;
  targetSwitchDate?: string;
  weeklyLearningHoursTarget: number;
  weeklyApplicationsTarget: number;
  weeklyNetworkingTarget: number;
  weeklyInterviewPracticeTarget: number;
  weeklyAvailableHours: number;
  maxActiveProjects: number;
  maxActiveCourses: number;
  maxPrimaryRoles: number;
  locale: string;
  timezone: string;
  currency: string;
  linkedinUrl?: string;
  githubUrl?: string;
  portfolioUrl?: string;
  recruiterIntro?: string;
  offerWeightAlignment: number;
  offerWeightComp: number;
  offerWeightLearning: number;
  offerWeightScope: number;
  offerWeightLocation: number;
}

export type TaskCategory =
  | "Learning"
  | "Project"
  | "Application"
  | "Networking"
  | "Interview"
  | "Research";

export type TaskPriority = "Critical" | "High" | "Medium" | "Low";

export interface CareerTask extends BaseEntity {
  title: string;
  category: TaskCategory;
  priority: TaskPriority;
  dueDate?: string;
  completed: boolean;
  completedAt?: string;
  linkedEntityId?: string;
  linkedRoleIds?: string[];
  blockedByTaskIds?: string[];
  estimatedMinutes?: number;
  waitingOn?: string;
}

export interface WeeklySprint extends BaseEntity {
  weekStart: string;
  title: string;
  objectives: string[];
  completedObjectives: string[];
  learningHours: number;
  applicationsSubmitted: number;
  networkingActions: number;
  interviewSessions: number;
  buildingHours: number;
  jobSearchHours: number;
  availableHours: number;
  retrospective: string;
  movedForward?: string;
  blocked?: string;
  producedInterviews?: string;
  strengthenedCapability?: string;
  createdEvidence?: string;
  shouldStop?: string;
  nextWeekPriority?: string;
}

export type InterviewQuestionCategory =
  | "Python"
  | "LLM"
  | "RAG"
  | "Agents"
  | "System Design"
  | "Cloud"
  | "MLOps"
  | "Behavioral"
  | "Backend"
  | "Security"
  | "Observability"
  | "Evaluation";

export interface InterviewQuestion extends BaseEntity {
  category: InterviewQuestionCategory;
  question: string;
  answer: string;
  confidence: 1 | 2 | 3 | 4 | 5;
  lastPracticed?: string;
  nextReviewDate?: string;
  mastered: boolean;
}

export type RolePriority = "Primary" | "Secondary" | "Stretch" | "Parked";
export type Seniority = "Mid" | "Senior" | "Lead" | "Architect";

export interface RoleCompetencyRequirement {
  competencyId: string;
  importance: 1 | 2 | 3 | 4 | 5;
  targetLevel: 1 | 2 | 3 | 4 | 5;
  evidenceRequired: boolean;
}

export interface TargetRoleProfile extends BaseEntity {
  name: string;
  priority: RolePriority;
  active: boolean;
  targetSeniority: Seniority;
  competencyRequirements: RoleCompetencyRequirement[];
  notes: string;
}

export type CompetencyDomain =
  | "Python"
  | "LLM"
  | "RAG"
  | "Agents"
  | "Evaluation"
  | "LLMOps"
  | "Cloud"
  | "System Design"
  | "Security"
  | "Data"
  | "Backend"
  | "Observability"
  | "Communication";

export interface Competency extends BaseEntity {
  name: string;
  domain: CompetencyDomain;
  description: string;
  skillIds: string[];
  researchTopicIds: string[];
}

export type EvidenceType =
  | "GitHub Repository"
  | "Live Demo"
  | "Architecture Diagram"
  | "Benchmark"
  | "Evaluation Report"
  | "Case Study"
  | "Resume Bullet"
  | "STAR Story"
  | "Technical Article"
  | "Credential"
  | "Presentation"
  | "Other";

export type EvidenceStrength = "Draft" | "Usable" | "Strong";

export interface EvidenceArtifact extends BaseEntity {
  title: string;
  type: EvidenceType;
  url?: string;
  description: string;
  projectId?: string;
  skillIds: string[];
  competencyIds: string[];
  mappedRoleIds: string[];
  strength: EvidenceStrength;
  lastVerifiedAt?: string;
}

export type LearningActivity =
  | "Course"
  | "Reading"
  | "Coding"
  | "Lab"
  | "Revision"
  | "Interview Practice";

export interface LearningSession extends BaseEntity {
  skillId?: string;
  researchTopicId?: string;
  date: string;
  durationMinutes: number;
  activity: LearningActivity;
  notes: string;
  evidenceCreated?: string;
}

export type MilestoneCategory =
  | "Architecture"
  | "Implementation"
  | "Evaluation"
  | "Testing"
  | "Deployment"
  | "Documentation"
  | "Demo";

export type MilestoneStatus = "Not Started" | "In Progress" | "Blocked" | "Complete";

export interface ProjectMilestone extends BaseEntity {
  projectId: string;
  title: string;
  category: MilestoneCategory;
  dueDate?: string;
  status: MilestoneStatus;
  notes: string;
}

export interface ArchitectureDecision extends BaseEntity {
  projectId: string;
  title: string;
  context: string;
  decision: string;
  alternativesConsidered: string;
  tradeOffs: string;
  consequences: string;
}

export interface ProjectMetric extends BaseEntity {
  projectId: string;
  name: string;
  baseline?: string;
  achieved?: string;
  unit?: string;
  methodology: string;
  notes: string;
}

export interface ResumeVariant extends BaseEntity {
  name: string;
  targetRoleIds: string[];
  versionLabel: string;
  externalUrl?: string;
  summary: string;
  selectedProjectIds: string[];
  selectedEvidenceIds: string[];
  notes: string;
  isActive: boolean;
}

export interface JobDescriptionSnapshot extends BaseEntity {
  applicationId: string;
  sourceUrl?: string;
  capturedAt: string;
  rawText: string;
  requiredSkills: string[];
  preferredSkills: string[];
  responsibilities: string[];
  locationText?: string;
  compensationText?: string;
  notes: string;
}

export type InterviewRoundType =
  | "Recruiter"
  | "Hiring Manager"
  | "Technical"
  | "Coding"
  | "System Design"
  | "AI / ML"
  | "Project Discussion"
  | "Behavioral"
  | "Assignment"
  | "HR"
  | "Other";

export type RoundOutcome = "Upcoming" | "Passed" | "Failed" | "Pending" | "Cancelled";

export interface InterviewRound extends BaseEntity {
  applicationId: string;
  roundNumber: number;
  type: InterviewRoundType;
  scheduledAt?: string;
  completedAt?: string;
  interviewerName?: string;
  interviewerRole?: string;
  outcome: RoundOutcome;
  questionsAsked: string[];
  strongAreas: string[];
  weakAreas: string[];
  notes: string;
  followUpDate?: string;
  wentWell?: string;
  difficult?: string;
  exposedGap?: string;
  shouldRevise?: string;
}

export type InteractionType =
  | "Message"
  | "Reply"
  | "Call"
  | "Referral Ask"
  | "Referral"
  | "Meeting"
  | "Follow-Up";

export interface NetworkingInteraction extends BaseEntity {
  contactId: string;
  date: string;
  type: InteractionType;
  summary: string;
  nextAction?: string;
  nextActionDate?: string;
}

export type CompanyPriority = "Dream" | "High" | "Medium" | "Watch";

export interface TargetCompany extends BaseEntity {
  name: string;
  tier: CompanyTier;
  priority: CompanyPriority;
  targetRoleIds: string[];
  careerUrl?: string;
  locations: string[];
  whyTarget: string;
  notes: string;
}

export type CampaignStatus = "Planned" | "Active" | "Completed";

export interface CareerCampaign extends BaseEntity {
  name: string;
  startDate: string;
  endDate?: string;
  targetRoleIds: string[];
  targetCompanyIds: string[];
  weeklyApplicationTarget: number;
  weeklyNetworkingTarget: number;
  resumeVariantIds: string[];
  hypothesis: string;
  retrospective: string;
  status: CampaignStatus;
}

export interface AchievementItem extends BaseEntity {
  title: string;
  context: string;
  action: string;
  result: string;
  technologies: string[];
  transferableCompetencies: string[];
  mappedRoleIds: string[];
  quantified: boolean;
}

export type WorkMode = "Remote" | "Hybrid" | "Office";

export interface OfferItem extends BaseEntity {
  applicationId: string;
  roleTitle: string;
  company: string;
  fixedCtc?: number;
  variableCtc?: number;
  joiningBonus?: number;
  equityEstimatedAnnual?: number;
  totalFirstYear?: number;
  totalRecurring?: number;
  location?: string;
  workMode?: WorkMode;
  joiningDate?: string;
  aiRoleAlignment: 1 | 2 | 3 | 4 | 5;
  learningPotential: 1 | 2 | 3 | 4 | 5;
  roleScope: 1 | 2 | 3 | 4 | 5;
  notes: string;
}

export type ResearchSourceType =
  | "Documentation"
  | "Paper"
  | "Book"
  | "Course"
  | "Repository"
  | "Article"
  | "Video"
  | "Community"
  | "Other";

export type SourceCredibility =
  | "Primary"
  | "Strong Secondary"
  | "Community"
  | "Unverified";

export interface ResearchSource extends BaseEntity {
  researchTopicId: string;
  title: string;
  url?: string;
  sourceType: ResearchSourceType;
  publishedDate?: string;
  reviewedAt?: string;
  credibility: SourceCredibility;
  takeaway: string;
}

export type ActivityCategory =
  | "Skill"
  | "Project"
  | "Application"
  | "Interview"
  | "Networking"
  | "Research"
  | "Certification"
  | "Sprint"
  | "Evidence";

export interface ActivityEvent extends BaseEntity {
  occurredAt: string;
  category: ActivityCategory;
  action: string;
  entityId?: string;
  metadata?: Record<string, string | number | boolean>;
}

export interface ScoreSnapshot {
  id: string;
  capturedAt: string;
  globalReadiness: number;
  capability: number;
  evidence: number;
  interview: number;
  positioning: number;
  marketExecution: number;
  roleScores: Record<string, number>;
}

export type TransitionPhase =
  | "Foundation"
  | "Building"
  | "Evidence"
  | "Market Activation"
  | "Interview Conversion"
  | "Offer Optimization"
  | "Transition Complete";

export type CareerAssetKind =
  | "Resume"
  | "LinkedIn"
  | "GitHub"
  | "Portfolio"
  | "Credential"
  | "Recruiter Intro"
  | "Transition Narrative";

export type AssetStatus = "Draft" | "Review" | "Ready";

export interface CareerAsset extends BaseEntity {
  kind: CareerAssetKind;
  title: string;
  targetRoleIds: string[];
  url?: string;
  status: AssetStatus;
  lastReviewedAt?: string;
  completeness: number;
  notes: string;
}

export interface ResumeBullet extends BaseEntity {
  text: string;
  projectId?: string;
  achievementId?: string;
  mappedRoleIds: string[];
  competencyIds: string[];
  quantified: boolean;
}

export type NegotiationDecision = "Pending" | "Accepted" | "Declined";

export interface NegotiationLog extends BaseEntity {
  offerId: string;
  initialOffer?: number;
  candidateExpectation?: number;
  counter?: number;
  recruiterResponse?: string;
  final?: number;
  decision?: NegotiationDecision;
  notes: string;
}

export interface TransitionNarrative extends BaseEntity {
  intro30s: string;
  story90s: string;
  whyAI: string;
  whyNow: string;
  whySenior: string;
  howOpsStrengthens: string;
  evidenceIds: string[];
}

export interface AttachmentMeta extends BaseEntity {
  name: string;
  mimeType: string;
  size: number;
  linkedEntityId?: string;
}

export interface AppUIState {
  onboardingComplete: boolean;
  demoMode: boolean;
  privacyMode: boolean;
  transitionPhaseOverride?: TransitionPhase;
  sidebarCollapsed: boolean;
}

export interface CareerOSMeta {
  lastSavedAt?: string;
  lastBackupAt?: string;
  lastKnownGoodAt?: string;
  updatedAt: string;
}

export interface CareerOSState {
  version: number;
  settings: CareerSettings;
  ui: AppUIState;
  meta: CareerOSMeta;
  skills: SkillItem[];
  projects: ProjectItem[];
  applications: JobApplication[];
  contacts: NetworkingContact[];
  certifications: CertificationItem[];
  starStories: StarStory[];
  researchTopics: ResearchTopic[];
  weeklySprints: WeeklySprint[];
  tasks: CareerTask[];
  interviewQuestions: InterviewQuestion[];
  targetRoles: TargetRoleProfile[];
  competencies: Competency[];
  evidenceArtifacts: EvidenceArtifact[];
  learningSessions: LearningSession[];
  projectMilestones: ProjectMilestone[];
  architectureDecisions: ArchitectureDecision[];
  projectMetrics: ProjectMetric[];
  resumeVariants: ResumeVariant[];
  jobDescriptions: JobDescriptionSnapshot[];
  interviewRounds: InterviewRound[];
  networkingInteractions: NetworkingInteraction[];
  targetCompanies: TargetCompany[];
  campaigns: CareerCampaign[];
  achievements: AchievementItem[];
  offers: OfferItem[];
  researchSources: ResearchSource[];
  activityEvents: ActivityEvent[];
  scoreSnapshots: ScoreSnapshot[];
  careerAssets: CareerAsset[];
  resumeBullets: ResumeBullet[];
  negotiationLogs: NegotiationLog[];
  transitionNarratives: TransitionNarrative[];
  attachments: AttachmentMeta[];
}

export type SaveStatus = "idle" | "saving" | "saved" | "failed";

export type RecoveryAction =
  | "restore_lkg"
  | "import_backup"
  | "export_corrupted"
  | "reset";

export interface RecoveryPayload {
  reason: string;
  corruptedJson?: string;
  canRestoreLkg: boolean;
}

export type OpportunityFit =
  | "Strong Apply"
  | "Apply"
  | "Stretch"
  | "Low Priority"
  | "Constraint Conflict";

export type CoverageLevel =
  | "Strong Evidence"
  | "Partial Evidence"
  | "Claimed / No Proof"
  | "Gap"
  | "Not Relevant";

export type BottleneckKind =
  | "Capability"
  | "Evidence"
  | "Positioning"
  | "Market Exposure"
  | "Screening Conversion"
  | "Interview Conversion"
  | "Offer Conversion";

export type RiskKind =
  | "Skill Sprawl"
  | "Project Sprawl"
  | "Market Starvation"
  | "Interview Preparation Lag"
  | "Evidence Gap"
  | "Follow-Up Debt"
  | "Positioning Dilution"
  | "Certification Overfocus";

export type TrustKind = "Fact" | "Derived" | "Recommendation";
