import type { CareerOSState } from "@/types/career";
import { currentBottleneck, detectRisks } from "./risks";
import { rankActions } from "./priority-engine";
import { computeReadiness } from "./scoring";
import { active } from "./utils";

export function learningBuildingRatio(state: CareerOSState, from?: string, to?: string) {
  const sessions = active(state.learningSessions).filter((s) => {
    if (from && s.date < from) return false;
    if (to && s.date > to) return false;
    return true;
  });
  const learning = sessions
    .filter((s) => s.activity === "Course" || s.activity === "Reading" || s.activity === "Revision")
    .reduce((n, s) => n + s.durationMinutes, 0);
  const building = sessions
    .filter((s) => s.activity === "Coding" || s.activity === "Lab")
    .reduce((n, s) => n + s.durationMinutes, 0);
  const interview = sessions
    .filter((s) => s.activity === "Interview Practice")
    .reduce((n, s) => n + s.durationMinutes, 0);
  const sprints = active(state.weeklySprints);
  const jobSearch = sprints.reduce((n, s) => n + s.jobSearchHours, 0) * 60;
  return { learning, building, interview, jobSearch };
}

export function careerInsights(state: CareerOSState) {
  const ratio = learningBuildingRatio(state);
  const insights: { title: string; detail: string; trust: "Recommendation" }[] = [];
  if (ratio.learning > ratio.building * 2 && ratio.learning > 8 * 60) {
    insights.push({
      title: "Over-learning, under-building",
      detail: "Learning hours dominate building hours. Convert study into a deployed artifact this week.",
      trust: "Recommendation",
    });
  }
  const r = computeReadiness(state);
  if (r.evidence < 40 && active(state.projects).filter((p) => p.status === "planned").length >= 4) {
    insights.push({
      title: "Planned-project inflation",
      detail: "A stack of planned projects is not a portfolio. One production system outruns ten outlines.",
      trust: "Recommendation",
    });
  }
  const bottleneck = currentBottleneck(state);
  insights.push({ title: `Bottleneck: ${bottleneck.kind}`, detail: bottleneck.detail, trust: "Recommendation" });
  return { insights, bottleneck, risks: detectRisks(state), actions: rankActions(state), readiness: r };
}
