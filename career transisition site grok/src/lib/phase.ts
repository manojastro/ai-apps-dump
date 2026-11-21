import type { CareerOSState, TransitionPhase } from "@/types/career";
import { computeReadiness } from "./scoring";
import { active } from "./utils";

export function derivePhase(state: CareerOSState): TransitionPhase {
  if (state.ui.transitionPhaseOverride) return state.ui.transitionPhaseOverride;
  const r = computeReadiness(state);
  const offers = active(state.offers);
  const accepted = active(state.negotiationLogs).some((n) => n.decision === "Accepted");
  if (accepted) return "Transition Complete";
  if (offers.length > 0) return "Offer Optimization";
  const technical = active(state.applications).filter((a) => a.status === "Technical" || a.status === "Offer");
  if (technical.length >= 1 && r.interview >= 40) return "Interview Conversion";
  const applied = active(state.applications).filter((a) => ["Applied", "Screening", "Technical", "Offer"].includes(a.status));
  if (applied.length >= 3 && r.evidence >= 35) return "Market Activation";
  const deployed = active(state.projects).filter((p) => p.status === "deployed");
  if (deployed.length >= 1 || r.evidence >= 40) return "Evidence";
  if (r.capability >= 25 || active(state.projects).some((p) => p.status === "in_progress")) return "Building";
  return "Foundation";
}

export const PHASES: TransitionPhase[] = [
  "Foundation",
  "Building",
  "Evidence",
  "Market Activation",
  "Interview Conversion",
  "Offer Optimization",
  "Transition Complete",
];
