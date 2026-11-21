import type { CareerOSState, ProjectItem, ScoreSnapshot, SkillItem } from "@/types/career";
import {
  APPLICATION_COUNT_CAP,
  CERTIFICATION_CAP,
  PLANNED_PROJECT_CAP,
  PROJECT_SCORE_WEIGHTS,
  READINESS_WEIGHTS,
  SKILL_STATUS_SCORE,
} from "./scoring-config";
import { artifactQualityPoints, skillEvidenceConfidence, textDepth } from "./evidence";
import { active, clamp, round0, safeUrl } from "./utils";
import { createId, nowIso } from "./ids";

export interface ScorePart {
  key: string;
  label: string;
  score: number;
  max: number;
  why: string;
}

export interface ExplainedScore {
  total: number;
  parts: ScorePart[];
}

function depthScore(text: string | undefined, max: number): number {
  return textDepth(text) * max;
}

function milestoneBoost(state: CareerOSState, projectId: string, category: string) {
  const items = active(state.projectMilestones).filter((m) => m.projectId === projectId && m.category === category);
  if (items.length === 0) return 0;
  const complete = items.filter((m) => m.status === "Complete").length;
  return complete / items.length;
}

export function projectProductionScore(state: CareerOSState, project: ProjectItem): ExplainedScore {
  const w = PROJECT_SCORE_WEIGHTS;
  const adrs = active(state.architectureDecisions).filter((a) => a.projectId === project.id);
  const metrics = active(state.projectMetrics).filter((m) => m.projectId === project.id);
  const evalEvidence = active(state.evidenceArtifacts).filter(
    (e) => e.projectId === project.id && (e.type === "Evaluation Report" || e.type === "Benchmark"),
  );

  const aiComplexityBase =
    project.category === "Agents" || project.category === "AIOps" || project.category === "RAG"
      ? 0.9
      : project.category === "Security_LLMOps"
        ? 0.85
        : 0.55;
  const stackBoost = Math.min(1, project.techStack.length / 6);
  const aiComplexity = (aiComplexityBase * 0.7 + stackBoost * 0.3) * w.aiComplexity;

  const evalMix =
    (textDepth(project.evaluationNotes) * 0.5 +
      milestoneBoost(state, project.id, "Evaluation") * 0.25 +
      Math.min(1, evalEvidence.length) * 0.25) *
    w.evaluation;

  const parts: ScorePart[] = [
    {
      key: "problem",
      label: "Problem clarity",
      score: depthScore(project.useCase, w.problemClarity),
      max: w.problemClarity,
      why: project.useCase ? "Use case documented" : "Use case missing",
    },
    {
      key: "architecture",
      label: "Architecture depth",
      score: (textDepth(project.architectureSummary) * 0.7 + Math.min(1, adrs.length / 2) * 0.3) * w.architectureDepth,
      max: w.architectureDepth,
      why: adrs.length ? `${adrs.length} architecture decision(s)` : "Architecture narrative / ADRs",
    },
    {
      key: "ai",
      label: "AI engineering complexity",
      score: aiComplexity,
      max: w.aiComplexity,
      why: `${project.category} · ${project.techStack.length} technologies`,
    },
    {
      key: "evaluation",
      label: "Evaluation",
      score: evalMix,
      max: w.evaluation,
      why: evalEvidence.length ? "Evaluation artifacts present" : "Evaluation still thin",
    },
    {
      key: "testing",
      label: "Testing",
      score:
        (textDepth(project.testingNotes) * 0.7 + milestoneBoost(state, project.id, "Testing") * 0.3) * w.testing,
      max: w.testing,
      why: "Tests / quality notes",
    },
    {
      key: "safety",
      label: "Safety / guardrails",
      score: depthScore(project.safetyNotes, w.safety),
      max: w.safety,
      why: "Prompt injection, tool-abuse, human-in-the-loop",
    },
    {
      key: "observability",
      label: "Observability",
      score: depthScore(project.observabilityNotes, w.observability),
      max: w.observability,
      why: "Traces, eval dashboards, incident signals",
    },
    {
      key: "deployment",
      label: "Deployment",
      score:
        ((project.status === "deployed" ? 0.7 : project.status === "in_progress" ? 0.25 : 0) +
          (safeUrl(project.liveUrl) ? 0.3 : 0)) *
        w.deployment,
      max: w.deployment,
      why: project.status === "deployed" ? "Deployed" : "Not deployed",
    },
    {
      key: "failure",
      label: "Failure handling",
      score: depthScore(project.failureHandlingNotes, w.failureHandling),
      max: w.failureHandling,
      why: "Recovery, retries, fallbacks",
    },
    {
      key: "docs",
      label: "Documentation",
      score:
        (textDepth(project.documentationNotes) * 0.6 + (safeUrl(project.githubUrl) ? 0.4 : 0)) * w.documentation,
      max: w.documentation,
      why: safeUrl(project.githubUrl) ? "GitHub present" : "GitHub missing",
    },
    {
      key: "benchmark",
      label: "Measured benchmark",
      score: Math.min(1, metrics.filter((m) => m.achieved).length / 2) * w.measuredBenchmark,
      max: w.measuredBenchmark,
      why: metrics.some((m) => m.achieved) ? "Measured outcomes recorded" : "No measured benchmark",
    },
  ];

  const total = clamp(parts.reduce((s, p) => s + p.score, 0));
  return { total: round0(total), parts };
}

function statusMultiplier(status: ProjectItem["status"]) {
  if (status === "deployed") return 1;
  if (status === "in_progress") return 0.55;
  return 0.2;
}

function maturityMultiplier(maturity: ProjectItem["maturity"]) {
  if (maturity === "Production Grade") return 1;
  if (maturity === "Portfolio Ready") return 0.82;
  if (maturity === "Prototype") return 0.5;
  return 0.22;
}

export function skillMasteryScore(state: CareerOSState, skill: SkillItem) {
  const mastery = SKILL_STATUS_SCORE[skill.status];
  const evidence = skillEvidenceConfidence(state, skill);
  return { mastery, evidence, combined: mastery * evidence };
}

export function capabilityScore(state: CareerOSState): ExplainedScore {
  const skills = active(state.skills);
  if (skills.length === 0) {
    return {
      total: 0,
      parts: [{ key: "skills", label: "Skills", score: 0, max: 100, why: "No skills recorded" }],
    };
  }
  const rows = skills.map((s) => skillMasteryScore(state, s));
  const avg = rows.reduce((s, r) => s + r.combined, 0) / rows.length;
  const mastered = skills.filter((s) => s.status === "mastered").length;
  const evidenced = rows.filter((r) => r.evidence >= 0.6).length;
  const total = clamp(avg * 100);
  return {
    total: round0(total),
    parts: [
      { key: "avg", label: "Evidence-adjusted mastery", score: total, max: 100, why: `${mastered} mastered · ${evidenced} with medium+ evidence` },
    ],
  };
}

export function evidenceIndex(state: CareerOSState): ExplainedScore {
  const projects = active(state.projects);
  const scored = projects
    .map((p) => {
      const raw = projectProductionScore(state, p).total;
      const weighted = raw * statusMultiplier(p.status) * maturityMultiplier(p.maturity);
      return { project: p, raw, weighted };
    })
    .sort((a, b) => b.weighted - a.weighted);

  const top = scored.slice(0, 3);
  const topAvg = top.length ? top.reduce((s, r) => s + r.weighted, 0) / top.length : 0;
  let projectPoints = topAvg;
  if (scored[0]?.project.status === "planned") {
    projectPoints = Math.min(projectPoints, PLANNED_PROJECT_CAP);
  }
  const extraProd = scored.filter((s) => s.project.status === "deployed" && s.raw >= 70).length;
  const bonus = extraProd > 1 ? Math.min(6, (extraProd - 1) * 3) : 0;

  const artifacts = artifactQualityPoints(active(state.evidenceArtifacts));
  const stars = active(state.starStories).filter((s) => textDepth(s.result) >= 0.55).length;
  const starPoints = Math.min(10, stars * 3);

  const projectShare = projectPoints * 0.7;
  const artifactShare = artifacts * 0.55;
  const total = clamp(projectShare + artifactShare + starPoints + bonus);

  return {
    total: round0(total),
    parts: [
      { key: "projects", label: "Top production projects", score: round0(projectShare), max: 70, why: top.length ? top.map((t) => t.project.title).join(" · ") : "No projects" },
      { key: "artifacts", label: "Evidence artifacts", score: round0(artifactShare), max: 22, why: `${active(state.evidenceArtifacts).length} artifacts (quality-weighted)` },
      { key: "star", label: "STAR stories", score: starPoints, max: 10, why: `${stars} quantified-enough stories` },
      { key: "bonus", label: "Additional production systems", score: bonus, max: 6, why: extraProd > 1 ? "More than one production-grade system" : "No extra production bonus" },
    ],
  };
}

export function interviewReadiness(state: CareerOSState): ExplainedScore {
  const questions = active(state.interviewQuestions);
  const confAvg = questions.length ? questions.reduce((s, q) => s + q.confidence, 0) / questions.length / 5 : 0;
  const mastered = questions.filter((q) => q.mastered).length;
  const practiced = questions.filter((q) => q.lastPracticed).length;
  const stars = active(state.starStories);
  const starComplete = stars.filter((s) => s.situation && s.task && s.action && s.result).length;
  const quantified = stars.filter((s) => /\d/.test(s.result)).length;
  const rounds = active(state.interviewRounds).filter((r) => r.outcome === "Passed" || r.completedAt);
  const qScore = Math.min(45, confAvg * 35 + Math.min(10, mastered * 2) + Math.min(8, practiced));
  const starScore = Math.min(30, starComplete * 6 + quantified * 3);
  const roundScore = Math.min(25, rounds.length * 8);
  const total = clamp(qScore + starScore + roundScore);
  return {
    total: round0(total),
    parts: [
      { key: "questions", label: "Practice bank", score: round0(qScore), max: 45, why: `${questions.length} questions · ${mastered} mastered` },
      { key: "star", label: "STAR completeness", score: round0(starScore), max: 30, why: `${starComplete} complete · ${quantified} quantified` },
      { key: "rounds", label: "Interview reps", score: round0(roundScore), max: 25, why: `${rounds.length} completed rounds` },
    ],
  };
}

export function marketExecution(state: CareerOSState): ExplainedScore {
  const apps = active(state.applications);
  const progressed = apps.filter((a) => ["Screening", "Technical", "Offer"].includes(a.status)).length;
  const offers = apps.filter((a) => a.status === "Offer").length;
  const applied = apps.filter((a) => ["Applied", "Screening", "Technical", "Offer", "Rejected"].includes(a.status));
  const quality = applied.length
    ? applied.reduce((s, a) => s + applicationQualityValue(a, state), 0) / applied.length
    : 0;
  const countPoints = Math.min(APPLICATION_COUNT_CAP * 0.25, Math.log2(applied.length + 1) * 8);
  const qualityPoints = quality * 0.45;
  const funnelPoints = Math.min(30, progressed * 8 + offers * 10);
  const followUps = apps.filter((a) => a.nextFollowUpDate).length;
  const hygiene = apps.length ? (followUps / apps.length) * 12 : 0;
  const total = clamp(countPoints + qualityPoints + funnelPoints + hygiene);
  return {
    total: round0(total),
    parts: [
      { key: "quality", label: "Application quality", score: round0(qualityPoints), max: 45, why: "JD, resume, referral, follow-up — not raw volume" },
      { key: "funnel", label: "Pipeline progress", score: round0(funnelPoints), max: 30, why: `${progressed} screening+ · ${offers} offer` },
      { key: "volume", label: "Diminishing volume signal", score: round0(countPoints), max: 14, why: `${applied.length} submitted (log-scaled)` },
      { key: "hygiene", label: "Follow-up hygiene", score: round0(hygiene), max: 12, why: `${followUps} with follow-up dates` },
    ],
  };
}

export function applicationQualityValue(
  app: CareerOSState["applications"][number],
  state: CareerOSState,
) {
  const jd = state.jobDescriptions.some((j) => j.applicationId === app.id && j.rawText.trim());
  const checks = [
    jd || app.jdCaptured,
    Boolean(app.resumeVariantId),
    app.evidenceReviewed,
    app.referralAttempted || Boolean(app.referralContactId) || Boolean(app.referralContact),
    Boolean(app.nextFollowUpDate),
    Boolean(app.interest && app.interest >= 3),
  ];
  return (checks.filter(Boolean).length / checks.length) * 100;
}

export function positioningScore(state: CareerOSState): ExplainedScore {
  const roles = active(state.targetRoles);
  const primary = roles.filter((r) => r.priority === "Primary" && r.active);
  const focus = primary.length === 0 ? 20 : primary.length <= state.settings.maxPrimaryRoles ? 35 : 18;
  const resumes = active(state.resumeVariants).filter((r) => r.isActive);
  const resumeCover = primary.filter((p) => resumes.some((r) => r.targetRoleIds.includes(p.id))).length;
  const resumePts = primary.length ? (resumeCover / primary.length) * 30 : resumes.length ? 18 : 8;
  const narrative = active(state.transitionNarratives)[0];
  const narPts = narrative
    ? [narrative.intro30s, narrative.story90s, narrative.whyAI, narrative.whyNow, narrative.whySenior, narrative.howOpsStrengthens].filter((x) => textDepth(x) >= 0.55).length * 5
    : 0;
  const assets = active(state.careerAssets).filter((a) => a.status === "Ready").length;
  const assetPts = Math.min(15, assets * 4);
  const total = clamp(focus + resumePts + narPts + assetPts);
  return {
    total: round0(total),
    parts: [
      { key: "focus", label: "Role focus", score: focus, max: 35, why: `${primary.length} primary roles` },
      { key: "resume", label: "Resume coverage", score: round0(resumePts), max: 30, why: `${resumeCover}/${primary.length || 0} primary roles have a resume` },
      { key: "narrative", label: "Transition narrative", score: narPts, max: 30, why: narrative ? "Narrative present" : "Narrative missing" },
      { key: "assets", label: "Career assets ready", score: assetPts, max: 15, why: `${assets} ready assets` },
    ],
  };
}

export function networkingScore(state: CareerOSState): ExplainedScore {
  const contacts = active(state.contacts);
  const interactions = active(state.networkingInteractions);
  const connected = contacts.filter((c) => c.status !== "Reached Out").length;
  const referrals = interactions.filter((i) => i.type === "Referral" || i.type === "Referral Ask").length;
  const calls = interactions.filter((i) => i.type === "Call" || i.type === "Meeting").length;
  const rate = contacts.length ? connected / contacts.length : 0;
  const total = clamp(Math.min(35, connected * 6) + rate * 25 + Math.min(20, referrals * 7) + Math.min(20, calls * 5));
  return {
    total: round0(total),
    parts: [
      { key: "connect", label: "Connection quality", score: round0(rate * 25 + Math.min(35, connected * 6)), max: 60, why: `${connected}/${contacts.length} progressed` },
      { key: "referral", label: "Referral motion", score: Math.min(20, referrals * 7), max: 20, why: `${referrals} referral actions` },
      { key: "calls", label: "Conversations", score: Math.min(20, calls * 5), max: 20, why: `${calls} calls/meetings` },
    ],
  };
}

export function researchCertScore(state: CareerOSState): ExplainedScore {
  const topics = active(state.researchTopics);
  const mastered = topics.filter((t) => t.isMastered).length;
  const sources = active(state.researchSources);
  const primary = sources.filter((s) => s.credibility === "Primary" || s.credibility === "Strong Secondary").length;
  const researchPts = Math.min(60, mastered * 8 + Math.min(20, primary * 3) + Math.min(10, topics.length));
  const certs = active(state.certifications);
  const certified = certs.filter((c) => c.status === "Certified").length;
  const studying = certs.filter((c) => c.status === "Studying" || c.status === "Scheduled").length;
  const certPts = Math.min(CERTIFICATION_CAP, certified * 12 + studying * 4);
  const total = clamp(researchPts * 0.7 + certPts * 0.3);
  return {
    total: round0(total),
    parts: [
      { key: "research", label: "Research mastery", score: round0(researchPts * 0.7), max: 70, why: `${mastered} topics mastered · ${primary} strong sources` },
      { key: "certs", label: "Certifications (capped)", score: round0(certPts * 0.3), max: 30, why: `${certified} certified — modest signal only` },
    ],
  };
}

export interface ReadinessBreakdown {
  global: number;
  capability: number;
  evidence: number;
  interview: number;
  marketExecution: number;
  positioning: number;
  networking: number;
  researchCerts: number;
  explain: {
    capability: ExplainedScore;
    evidence: ExplainedScore;
    interview: ExplainedScore;
    marketExecution: ExplainedScore;
    positioning: ExplainedScore;
    networking: ExplainedScore;
    researchCerts: ExplainedScore;
  };
}

export function computeReadiness(state: CareerOSState): ReadinessBreakdown {
  const capability = capabilityScore(state);
  const evidence = evidenceIndex(state);
  const interview = interviewReadiness(state);
  const market = marketExecution(state);
  const positioning = positioningScore(state);
  const networking = networkingScore(state);
  const researchCerts = researchCertScore(state);
  const w = READINESS_WEIGHTS;
  const global = round0(
    capability.total * w.capability +
      evidence.total * w.evidence +
      interview.total * w.interview +
      market.total * w.marketExecution +
      positioning.total * w.positioning +
      networking.total * w.networking +
      researchCerts.total * w.researchCerts,
  );
  return {
    global,
    capability: capability.total,
    evidence: evidence.total,
    interview: interview.total,
    marketExecution: market.total,
    positioning: positioning.total,
    networking: networking.total,
    researchCerts: researchCerts.total,
    explain: { capability, evidence, interview, marketExecution: market, positioning, networking, researchCerts },
  };
}

export function captureSnapshot(state: CareerOSState, roleScores: Record<string, number>): ScoreSnapshot {
  const r = computeReadiness(state);
  return {
    id: createId("snap"),
    capturedAt: nowIso(),
    globalReadiness: r.global,
    capability: r.capability,
    evidence: r.evidence,
    interview: r.interview,
    positioning: r.positioning,
    marketExecution: r.marketExecution,
    roleScores,
  };
}

export { READINESS_WEIGHTS };
