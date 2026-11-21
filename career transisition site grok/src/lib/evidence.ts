import type {
  CareerOSState,
  CoverageLevel,
  EvidenceArtifact,
  EvidenceStrength,
  ProjectItem,
  SkillItem,
} from "@/types/career";
import { EVIDENCE_CONFIDENCE } from "./scoring-config";
import { active, clamp } from "./utils";

export function textDepth(text?: string) {
  const t = (text ?? "").trim();
  if (!t) return 0;
  if (t.length < 40) return 0.25;
  if (t.length < 120) return 0.55;
  if (t.length < 280) return 0.8;
  return 1;
}

export function strengthWeight(strength: EvidenceStrength) {
  if (strength === "Strong") return 1;
  if (strength === "Usable") return 0.6;
  return 0.25;
}

export function artifactsForSkill(state: CareerOSState, skillId: string) {
  return active(state.evidenceArtifacts).filter((e) => e.skillIds.includes(skillId));
}

export function projectsUsingSkill(state: CareerOSState, skill: SkillItem) {
  const name = skill.name.toLowerCase();
  return active(state.projects).filter((p) => {
    if (p.techStack.some((t) => t.toLowerCase() === name || t.toLowerCase().includes(name))) return true;
    return active(state.evidenceArtifacts).some(
      (e) => e.projectId === p.id && e.skillIds.includes(skill.id),
    );
  });
}

export function skillHasInterviewValidation(state: CareerOSState, skill: SkillItem) {
  const name = skill.name.toLowerCase();
  const qHit = active(state.interviewQuestions).some(
    (q) =>
      (q.confidence >= 4 || q.mastered) &&
      (q.question.toLowerCase().includes(name) || q.answer.toLowerCase().includes(name) || q.category.toLowerCase().includes(skill.category.replace("_", " "))),
  );
  const starHit = active(state.starStories).some(
    (s) =>
      s.techNotes.toLowerCase().includes(name) ||
      s.action.toLowerCase().includes(name) ||
      s.result.toLowerCase().includes(name),
  );
  return qHit || starHit;
}

export function skillEvidenceConfidence(state: CareerOSState, skill: SkillItem) {
  let conf = skill.status === "mastered" ? EVIDENCE_CONFIDENCE.masteredFloor : EVIDENCE_CONFIDENCE.baseNone;
  if (skill.sourceLearned.trim() && skill.summary.trim()) conf += EVIDENCE_CONFIDENCE.sourceNotes;
  if (projectsUsingSkill(state, skill).some((p) => p.status !== "planned")) {
    conf += EVIDENCE_CONFIDENCE.projectApplication;
  }
  const artifacts = artifactsForSkill(state, skill.id);
  if (artifacts.some((a) => a.strength !== "Draft")) conf += EVIDENCE_CONFIDENCE.artifact;
  if (skillHasInterviewValidation(state, skill)) conf += EVIDENCE_CONFIDENCE.interviewValidation;
  if (skill.mappedRoles.length > 0 || state.competencies.some((c) => c.skillIds.includes(skill.id))) {
    conf += EVIDENCE_CONFIDENCE.competencyMapping;
  }
  return clamp(conf, 0, 1);
}

export function evidenceLabel(confidence: number): "Low" | "Medium" | "High" {
  if (confidence >= 0.75) return "High";
  if (confidence >= 0.45) return "Medium";
  return "Low";
}

export function coverageFromSignals(capability: number, evidence: number): CoverageLevel {
  if (capability < 0.15 && evidence < 0.15) return "Gap";
  if (capability >= 0.55 && evidence >= 0.7) return "Strong Evidence";
  if (capability >= 0.4 && evidence >= 0.35) return "Partial Evidence";
  if (capability >= 0.4 && evidence < 0.35) return "Claimed / No Proof";
  return "Gap";
}

export function projectEvidenceMissing(state: CareerOSState, project: ProjectItem) {
  const missing: string[] = [];
  if (textDepth(project.architectureSummary) < 0.55) missing.push("Architecture write-up");
  if (textDepth(project.evaluationNotes) < 0.55) missing.push("Evaluation notes");
  if (!active(state.projectMetrics).some((m) => m.projectId === project.id && m.achieved)) {
    missing.push("Measured benchmark");
  }
  if (project.status !== "deployed" || !project.liveUrl) missing.push("Deployment / live demo");
  if (textDepth(project.observabilityNotes) < 0.4) missing.push("Observability");
  if (textDepth(project.testingNotes) < 0.4) missing.push("Testing");
  if (textDepth(project.safetyNotes) < 0.4) missing.push("Safety / guardrails");
  if (!project.githubUrl) missing.push("GitHub repository");
  const artifacts = active(state.evidenceArtifacts).filter((e) => e.projectId === project.id);
  if (!artifacts.some((a) => a.type === "Architecture Diagram")) missing.push("Architecture diagram");
  if (!artifacts.some((a) => a.type === "Evaluation Report" || a.type === "Benchmark")) {
    missing.push("Evaluation / benchmark artifact");
  }
  return missing;
}

export function artifactQualityPoints(artifacts: EvidenceArtifact[]) {
  const ranked = [...artifacts].sort((a, b) => strengthWeight(b.strength) - strengthWeight(a.strength));
  const top = ranked.slice(0, 8);
  const raw = top.reduce((sum, a) => sum + strengthWeight(a.strength) * 8, 0);
  return clamp(raw, 0, 40);
}
