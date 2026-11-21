import type { CareerOSState, JobApplication, OpportunityFit } from "@/types/career";
import { coverageFromSignals } from "./evidence";
import { tokenize } from "./utils";
import { applicationQualityValue } from "./scoring";
import { analyzeRole } from "./role-readiness";

export interface FitResult {
  label: OpportunityFit;
  score: number;
  reasons: string[];
  constraints: string[];
}

function parseLpa(text?: string) {
  if (!text) return null;
  const m = text.replace(/,/g, "").match(/(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lacs)?/i);
  if (!m) return null;
  const n = Number(m[1]);
  if (Number.isNaN(n)) return null;
  if (n > 100) return n / 100000;
  return n;
}

export function opportunityFit(state: CareerOSState, job: JobApplication): FitResult {
  const reasons: string[] = [];
  const constraints: string[] = [];
  const roles = state.targetRoles.filter((r) => r.active && !r.archivedAt);
  const matchedRole = roles.find((r) => r.name.toLowerCase() === job.role.toLowerCase())
    ?? roles.find((r) => job.role.toLowerCase().includes(r.name.toLowerCase().split(" ")[0] ?? "___"));
  const roleAlignment = matchedRole
    ? matchedRole.priority === "Primary"
      ? 1
      : matchedRole.priority === "Secondary"
        ? 0.75
        : matchedRole.priority === "Stretch"
          ? 0.5
          : 0.25
    : 0.2;
  if (matchedRole) reasons.push(`Aligns to ${matchedRole.name} (${matchedRole.priority})`);
  else reasons.push("Role title is not one of the active target roles");

  const jd = state.jobDescriptions.find((j) => j.applicationId === job.id);
  const required = jd?.requiredSkills ?? [];
  let skillCover = 0.4;
  if (required.length) {
    const skills = state.skills.filter((s) => !s.archivedAt);
    const hits = required.filter((req) =>
      skills.some((s) => s.name.toLowerCase().includes(req.toLowerCase()) || tokenize(s.summary).includes(req.toLowerCase())),
    );
    skillCover = hits.length / required.length;
    reasons.push(`JD skill coverage ${hits.length}/${required.length}`);
  }

  const evidence = matchedRole ? analyzeRole(state, matchedRole).score / 100 : 0.3;
  const seniorityBoost = /senior|lead|staff|principal|architect/i.test(job.role) ? 0.1 : 0;
  const loc = (job.location ?? jd?.locationText ?? "").toLowerCase();
  const locOk =
    !loc ||
    state.settings.targetLocations.some((l) => loc.includes(l.toLowerCase())) ||
    loc.includes("remote") ||
    loc.includes("hybrid");
  if (!locOk) constraints.push(`Location "${job.location ?? loc}" is outside the target set`);

  const lpa = parseLpa(job.compensationText ?? jd?.compensationText);
  if (lpa !== null && lpa + 0.5 < state.settings.baselineCtc) {
    constraints.push(`Listed compensation (~₹${lpa} LPA) is below baseline ₹${state.settings.baselineCtc} LPA`);
  }
  const company = state.targetCompanies.find((c) => c.id === job.companyId || c.name.toLowerCase() === job.company.toLowerCase());
  const companyBoost = company ? (company.priority === "Dream" ? 0.12 : company.priority === "High" ? 0.08 : 0.04) : 0;
  const referralBoost = job.referralContactId || job.referralContact ? 0.08 : 0;
  const interest = (job.interest ?? 3) / 5;

  let score =
    roleAlignment * 28 +
    skillCover * 18 +
    evidence * 18 +
    seniorityBoost * 100 * 0.08 +
    (locOk ? 8 : 0) +
    companyBoost * 100 +
    referralBoost * 100 +
    interest * 10;

  if (lpa !== null && lpa >= state.settings.targetMinCtc) score += 6;
  if (constraints.length) score -= 12;

  let label: OpportunityFit = "Apply";
  if (constraints.length >= 2) label = "Constraint Conflict";
  else if (score >= 78 && roleAlignment >= 0.75) label = "Strong Apply";
  else if (score >= 62) label = "Apply";
  else if (score >= 45) label = "Stretch";
  else label = "Low Priority";

  if (label === "Constraint Conflict") reasons.push("Constraints recorded — not auto-rejected");
  return { label, score: Math.round(score), reasons, constraints };
}

export function jdCoverage(state: CareerOSState, job: JobApplication) {
  const jd = state.jobDescriptions.find((j) => j.applicationId === job.id);
  const reqs = [...(jd?.requiredSkills ?? []), ...(jd?.preferredSkills ?? [])];
  const unique = [...new Set(reqs.map((r) => r.trim()).filter(Boolean))];
  return unique.map((req) => {
    const skill = state.skills.find((s) => !s.archivedAt && s.name.toLowerCase().includes(req.toLowerCase()));
    const artifact = state.evidenceArtifacts.find(
      (e) => !e.archivedAt && (e.title.toLowerCase().includes(req.toLowerCase()) || e.description.toLowerCase().includes(req.toLowerCase())),
    );
    const capability = skill ? (skill.status === "mastered" ? 0.9 : skill.status === "in_progress" ? 0.5 : 0.15) : 0;
    const evidence = artifact ? 0.7 : skill && skill.status === "mastered" ? 0.2 : 0;
    return {
      requirement: req,
      coverage: coverageFromSignals(capability, evidence),
      skillId: skill?.id,
      evidenceId: artifact?.id,
    };
  });
}

export { applicationQualityValue };
