export const READINESS_WEIGHTS = {
  capability: 0.25,
  evidence: 0.25,
  interview: 0.15,
  marketExecution: 0.15,
  positioning: 0.1,
  networking: 0.05,
  researchCerts: 0.05,
} as const;

export const SKILL_STATUS_SCORE = {
  to_learn: 0,
  in_progress: 0.5,
  mastered: 1,
} as const;

export const PROJECT_SCORE_WEIGHTS = {
  problemClarity: 5,
  architectureDepth: 10,
  aiComplexity: 10,
  evaluation: 15,
  testing: 10,
  safety: 10,
  observability: 10,
  deployment: 10,
  failureHandling: 5,
  documentation: 5,
  measuredBenchmark: 10,
} as const;

export const EVIDENCE_CONFIDENCE = {
  baseNone: 0.2,
  masteredFloor: 0.4,
  sourceNotes: 0.1,
  projectApplication: 0.2,
  artifact: 0.2,
  interviewValidation: 0.15,
  competencyMapping: 0.1,
} as const;

export const CERTIFICATION_CAP = 40;
export const APPLICATION_COUNT_CAP = 55;
export const PLANNED_PROJECT_CAP = 18;
