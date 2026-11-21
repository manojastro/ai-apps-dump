import type { CareerOSState, Competency, CoverageLevel, TargetRoleProfile } from "@/types/career";
import { coverageFromSignals, skillEvidenceConfidence, strengthWeight, textDepth } from "./evidence";
import { SKILL_STATUS_SCORE } from "./scoring-config";
import { active, clamp, round0 } from "./utils";

export interface CompetencyGap {
  competency: Competency;
  importance: number;
  targetLevel: number;
  capability: number;
  evidence: number;
  interview: number;
  coverage: CoverageLevel;
  band: "Strong" | "Partial" | "Gap" | "Evidence Missing";
  nextAction: string;
}

export interface RoleReadinessResult {
  role: TargetRoleProfile;
  score: number;
  gaps: CompetencyGap[];
  strong: CompetencyGap[];
  partial: CompetencyGap[];
  missing: CompetencyGap[];
  evidenceMissing: CompetencyGap[];
}

function competencyCapability(state: CareerOSState, competency: Competency) {
  const linkedSkills = active(state.skills).filter(
    (s) => competency.skillIds.includes(s.id) || s.mappedRoles.includes(competency.name),
  );
  if (linkedSkills.length === 0) {
    const name = competency.name.toLowerCase();
    const weak = active(state.skills).filter((s) => s.name.toLowerCase().includes(name.split(" ")[0] ?? "___"));
    if (weak.length === 0) return 0;
    const avg = weak.reduce((sum, s) => sum + SKILL_STATUS_SCORE[s.status] * 0.35, 0) / weak.length;
    return clamp(avg, 0, 0.45);
  }
  const avg =
    linkedSkills.reduce((sum, s) => sum + SKILL_STATUS_SCORE[s.status] * skillEvidenceConfidence(state, s), 0) /
    linkedSkills.length;
  return clamp(avg);
}

function competencyEvidence(state: CareerOSState, competency: Competency, roleId: string) {
  const artifacts = active(state.evidenceArtifacts).filter(
    (e) => e.competencyIds.includes(competency.id) || e.mappedRoleIds.includes(roleId),
  );
  const relatedProjects = active(state.projects).filter((p) =>
    artifacts.some((a) => a.projectId === p.id) || p.targetRole.toLowerCase().includes(competency.domain.toLowerCase()),
  );
  const artifactScore = artifacts.length
    ? artifacts.reduce((s, a) => s + strengthWeight(a.strength), 0) / Math.max(2, artifacts.length)
    : 0;
  const projectScore = relatedProjects.some((p) => p.status === "deployed")
    ? 0.7
    : relatedProjects.some((p) => p.status === "in_progress")
      ? 0.35
      : 0;
  const research = active(state.researchTopics).filter((t) => competency.researchTopicIds.includes(t.id) && t.isMastered);
  const researchScore = research.length ? 0.2 : 0;
  return clamp(artifactScore * 0.5 + projectScore * 0.4 + researchScore);
}

function competencyInterview(state: CareerOSState, competency: Competency) {
  const domain = competency.domain.toLowerCase();
  const qs = active(state.interviewQuestions).filter(
    (q) => q.category.toLowerCase().includes(domain) || q.question.toLowerCase().includes(competency.name.toLowerCase()),
  );
  if (qs.length === 0) return 0;
  return clamp(qs.reduce((s, q) => s + q.confidence / 5, 0) / qs.length);
}

export function analyzeRole(state: CareerOSState, role: TargetRoleProfile): RoleReadinessResult {
  const gaps: CompetencyGap[] = role.competencyRequirements.map((req) => {
    const competency = state.competencies.find((c) => c.id === req.competencyId);
    if (!competency) {
      return {
        competency: {
          id: req.competencyId,
          name: req.competencyId,
          domain: "LLM",
          description: "",
          skillIds: [],
          researchTopicIds: [],
          createdAt: "",
          updatedAt: "",
        },
        importance: req.importance,
        targetLevel: req.targetLevel,
        capability: 0,
        evidence: 0,
        interview: 0,
        coverage: "Gap",
        band: "Gap",
        nextAction: "Map this competency to skills and evidence.",
      };
    }
    const capability = competencyCapability(state, competency);
    const evidence = competencyEvidence(state, competency, role.id);
    const interview = competencyInterview(state, competency);
    const coverage = coverageFromSignals(capability, evidence);
    let band: CompetencyGap["band"] = "Gap";
    if (capability >= 0.7 && evidence >= 0.55) band = "Strong";
    else if (capability >= 0.45 && evidence < 0.4 && req.evidenceRequired) band = "Evidence Missing";
    else if (capability >= 0.4 || evidence >= 0.35) band = "Partial";
    const nextAction =
      band === "Evidence Missing"
        ? `Add benchmark or architecture evidence for ${competency.name}.`
        : band === "Gap"
          ? `Build capability in ${competency.name} via a production project, not another course.`
          : band === "Partial"
            ? `Deepen ${competency.name} with evaluation notes and an interview defense.`
            : `Keep ${competency.name} interview-ready.`;
    return {
      competency,
      importance: req.importance,
      targetLevel: req.targetLevel,
      capability,
      evidence,
      interview,
      coverage,
      band,
      nextAction,
    };
  });

  const weightSum = role.competencyRequirements.reduce((s, r) => s + r.importance, 0) || 1;
  let acc = 0;
  for (const gap of gaps) {
    const req = role.competencyRequirements.find((r) => r.competencyId === gap.competency.id);
    const target = (req?.targetLevel ?? 3) / 5;
    let cell = gap.capability * 0.45 + gap.evidence * 0.4 + gap.interview * 0.15;
    if (req?.evidenceRequired && gap.evidence < 0.3) cell = Math.min(cell, gap.capability * 0.6);
    const vsTarget = target === 0 ? cell : Math.min(1, cell / target);
    acc += vsTarget * gap.importance;
  }
  const score = round0(clamp((acc / weightSum) * 100));

  return {
    role,
    score,
    gaps,
    strong: gaps.filter((g) => g.band === "Strong"),
    partial: gaps.filter((g) => g.band === "Partial"),
    missing: gaps.filter((g) => g.band === "Gap"),
    evidenceMissing: gaps.filter((g) => g.band === "Evidence Missing"),
  };
}

export function allRoleReadiness(state: CareerOSState) {
  return active(state.targetRoles)
    .filter((r) => r.active)
    .map((r) => analyzeRole(state, r))
    .sort((a, b) => {
      const order = { Primary: 0, Secondary: 1, Stretch: 2, Parked: 3 };
      return order[a.role.priority] - order[b.role.priority] || b.score - a.score;
    });
}

export function roleScoreMap(state: CareerOSState): Record<string, number> {
  const out: Record<string, number> = {};
  for (const row of allRoleReadiness(state)) out[row.role.id] = row.score;
  return out;
}

export function evidenceGraph(state: CareerOSState, role: TargetRoleProfile) {
  const analysis = analyzeRole(state, role);
  return analysis.gaps.map((g) => {
    const skills = active(state.skills).filter((s) => g.competency.skillIds.includes(s.id));
    const projects = active(state.projects).filter((p) =>
      active(state.evidenceArtifacts).some(
        (e) => e.projectId === p.id && (e.competencyIds.includes(g.competency.id) || e.mappedRoleIds.includes(role.id)),
      ),
    );
    const artifacts = active(state.evidenceArtifacts).filter(
      (e) => e.competencyIds.includes(g.competency.id) || e.mappedRoleIds.includes(role.id),
    );
    const stars = active(state.starStories).filter((s) => textDepth(s.result) > 0 && s.techNotes.toLowerCase().includes(g.competency.domain.toLowerCase()));
    return { competency: g.competency, band: g.band, skills, projects, artifacts, stars, nextAction: g.nextAction };
  });
}
