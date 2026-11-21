import type { BottleneckKind, CareerOSState, RiskKind } from "@/types/career";
import { isOverdue } from "./dates";
import { computeReadiness } from "./scoring";
import { active } from "./utils";

export interface RiskItem {
  kind: RiskKind;
  severity: "high" | "medium" | "low";
  title: string;
  detail: string;
  trust: "Recommendation";
}

export function detectRisks(state: CareerOSState): RiskItem[] {
  const risks: RiskItem[] = [];
  const skills = active(state.skills);
  const inProgress = skills.filter((s) => s.status === "in_progress");
  const mastered = skills.filter((s) => s.status === "mastered");
  if (inProgress.length >= 8 && mastered.length < 3) {
    risks.push({
      kind: "Skill Sprawl",
      severity: "high",
      title: "Skill sprawl",
      detail: `${inProgress.length} skills are in progress while only ${mastered.length} are mastered. Finish a cluster before opening another.`,
      trust: "Recommendation",
    });
  }

  const activeProjects = active(state.projects).filter((p) => p.status === "in_progress");
  if (activeProjects.length > state.settings.maxActiveProjects) {
    risks.push({
      kind: "Project Sprawl",
      severity: "high",
      title: "Project sprawl",
      detail: `${activeProjects.length} projects are in progress. Limit is ${state.settings.maxActiveProjects}. Finishing one is worth more than starting another.`,
      trust: "Recommendation",
    });
  }

  const recentApps = active(state.applications).filter((a) => ["Applied", "Screening", "Technical", "Offer"].includes(a.status));
  if (recentApps.length < 3 && state.ui.onboardingComplete) {
    risks.push({
      kind: "Market Starvation",
      severity: "medium",
      title: "Market starvation",
      detail: "Few quality applications are in motion. Capability without market exposure will not convert.",
      trust: "Recommendation",
    });
  }

  const upcoming = active(state.interviewRounds).filter((r) => r.outcome === "Upcoming");
  const readiness = computeReadiness(state);
  if (upcoming.length > 0 && readiness.interview < 45) {
    risks.push({
      kind: "Interview Preparation Lag",
      severity: "high",
      title: "Interview preparation lag",
      detail: `${upcoming.length} upcoming round(s) while interview readiness is ${readiness.interview}. Practice weak areas before the next loop.`,
      trust: "Recommendation",
    });
  }

  if (readiness.capability - readiness.evidence >= 18) {
    risks.push({
      kind: "Evidence Gap",
      severity: "high",
      title: "Evidence gap",
      detail: "Skill readiness is ahead of production evidence. Deploy, evaluate, and write architecture notes before starting another course.",
      trust: "Recommendation",
    });
  }

  const overdueFollow = active(state.applications).filter((a) => a.nextFollowUpDate && isOverdue(a.nextFollowUpDate) && a.status !== "Rejected" && a.status !== "Offer");
  const overdueNet = active(state.contacts).filter((c) => c.nextTouchpointDate && isOverdue(c.nextTouchpointDate));
  if (overdueFollow.length + overdueNet.length >= 3) {
    risks.push({
      kind: "Follow-Up Debt",
      severity: "high",
      title: "Follow-up debt",
      detail: `${overdueFollow.length} job follow-ups and ${overdueNet.length} networking touchpoints are overdue.`,
      trust: "Recommendation",
    });
  }

  const primary = active(state.targetRoles).filter((r) => r.priority === "Primary" && r.active);
  if (primary.length > state.settings.maxPrimaryRoles) {
    risks.push({
      kind: "Positioning Dilution",
      severity: "medium",
      title: "Positioning dilution",
      detail: `${primary.length} primary roles are active. The OS works best with at most ${state.settings.maxPrimaryRoles} headline identities.`,
      trust: "Recommendation",
    });
  }

  const certified = active(state.certifications).filter((c) => c.status === "Certified" || c.status === "Studying");
  const deployed = active(state.projects).filter((p) => p.status === "deployed");
  if (certified.length >= 4 && deployed.length === 0) {
    risks.push({
      kind: "Certification Overfocus",
      severity: "medium",
      title: "Certification overfocus",
      detail: "Certificates are accumulating faster than production evidence. They remain a modest readiness signal.",
      trust: "Recommendation",
    });
  }

  return risks;
}

export function currentBottleneck(state: CareerOSState): { kind: BottleneckKind; detail: string } {
  const r = computeReadiness(state);
  const apps = active(state.applications);
  const applied = apps.filter((a) => ["Applied", "Screening", "Technical", "Offer", "Rejected"].includes(a.status));
  const screening = apps.filter((a) => ["Screening", "Technical", "Offer"].includes(a.status) || a.status === "Rejected");
  const technical = apps.filter((a) => a.status === "Technical" || a.status === "Offer");
  const offers = apps.filter((a) => a.status === "Offer");

  if (r.capability - r.evidence >= 15) {
    return {
      kind: "Evidence",
      detail: "Your skill readiness is ahead of your production evidence. Complete deployment and evaluation work before starting another major course.",
    };
  }
  if (r.capability < 40) {
    return { kind: "Capability", detail: "Core AI engineering capability is still the constraint. Focus on Python + agents/RAG depth with evidence, not title spray." };
  }
  if (r.positioning < 40 && r.evidence >= 45) {
    return { kind: "Positioning", detail: "Evidence exists but the narrative, resume variants, and role focus are not yet recruiter-ready." };
  }
  if (applied.length < 5) {
    return { kind: "Market Exposure", detail: "Too few high-quality applications are in the market. Capability will not convert without targeted outreach." };
  }
  if (applied.length >= 8 && screening.filter((a) => a.status !== "Rejected" || a.outcomeReason === "Failed Interview").length / Math.max(1, applied.length) < 0.15) {
    return { kind: "Screening Conversion", detail: "Applications are not converting to screens. Tighten JD fit, resume variant, and referral quality — not volume." };
  }
  if (screening.length >= 4 && technical.length / Math.max(1, screening.length) < 0.25) {
    return { kind: "Interview Conversion", detail: "Screens are happening but technical conversion is weak. Feed interview weaknesses back into practice and projects." };
  }
  if (technical.length >= 3 && offers.length === 0) {
    return { kind: "Offer Conversion", detail: "Technical loops are not producing offers. Compare round notes, close evidence gaps, and tighten role targeting." };
  }
  const dims: { kind: BottleneckKind; value: number }[] = [
    { kind: "Capability", value: r.capability },
    { kind: "Evidence", value: r.evidence },
    { kind: "Positioning", value: r.positioning },
    { kind: "Market Exposure", value: r.marketExecution },
  ];
  dims.sort((a, b) => a.value - b.value);
  const lowest = dims[0] ?? { kind: "Capability" as const, value: 0 };
  return { kind: lowest.kind, detail: `${lowest.kind} is the lowest executive dimension at ${Math.round(lowest.value)}.` };
}
