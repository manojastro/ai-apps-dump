import { SMALL_SAMPLE_THRESHOLD } from "./constants";
import type { CareerOSState, JobApplication } from "@/types/career";
import { inRange } from "./dates";
import { computeReadiness } from "./scoring";
import { active } from "./utils";
import { applicationQualityValue } from "./scoring";

export type DateRange = { from?: string; to?: string; preset: "7d" | "30d" | "90d" | "all" | "custom" };

export function rangeFromPreset(preset: DateRange["preset"], custom?: { from?: string; to?: string }): DateRange {
  const now = new Date();
  const iso = now.toISOString();
  if (preset === "all") return { preset };
  if (preset === "custom") return { preset, from: custom?.from, to: custom?.to };
  const days = preset === "7d" ? 7 : preset === "30d" ? 30 : 90;
  const from = new Date(now.getTime() - days * 86400000).toISOString();
  return { preset, from, to: iso };
}

function inDateRange(iso: string, range: DateRange) {
  if (range.preset === "all") return true;
  return inRange(iso, range.from, range.to);
}

export function smallSample(n: number) {
  return n < SMALL_SAMPLE_THRESHOLD;
}

export function funnelMetrics(apps: JobApplication[]) {
  const counts = {
    Identified: 0,
    Referred: 0,
    Applied: 0,
    Screening: 0,
    Technical: 0,
    Offer: 0,
    Rejected: 0,
  };
  for (const a of apps) counts[a.status] += 1;
  const applied = counts.Applied + counts.Screening + counts.Technical + counts.Offer + counts.Rejected;
  const screening = counts.Screening + counts.Technical + counts.Offer;
  const technical = counts.Technical + counts.Offer;
  const conv = (num: number, den: number) =>
    den === 0 ? { rate: null as number | null, warning: "Insufficient Data" } : smallSample(den)
      ? { rate: num / den, warning: "Insufficient Data" }
      : { rate: num / den, warning: null as string | null };
  return {
    counts,
    appliedToScreening: conv(screening, Math.max(applied, 1)),
    screeningToTechnical: conv(technical, Math.max(screening, 1)),
    technicalToOffer: conv(counts.Offer, Math.max(technical, 1)),
  };
}

export function groupConversion(apps: JobApplication[], keyFn: (a: JobApplication) => string) {
  const groups = new Map<string, JobApplication[]>();
  for (const a of apps) {
    const key = keyFn(a) || "Unknown";
    groups.set(key, [...(groups.get(key) ?? []), a]);
  }
  return [...groups.entries()].map(([key, rows]) => {
    const applied = rows.filter((a) => a.status !== "Identified").length;
    const screening = rows.filter((a) => ["Screening", "Technical", "Offer"].includes(a.status)).length;
    const technical = rows.filter((a) => ["Technical", "Offer"].includes(a.status)).length;
    const offer = rows.filter((a) => a.status === "Offer").length;
    return {
      key,
      apps: rows.length,
      applied,
      screening,
      technical,
      offer,
      warning: smallSample(applied) ? "Insufficient Data" : null,
    };
  });
}

export function resumePerformance(state: CareerOSState) {
  return active(state.resumeVariants).map((resume) => {
    const apps = active(state.applications).filter((a) => a.resumeVariantId === resume.id);
    const screening = apps.filter((a) => ["Screening", "Technical", "Offer"].includes(a.status)).length;
    const technical = apps.filter((a) => ["Technical", "Offer"].includes(a.status)).length;
    return {
      resume,
      apps: apps.length,
      screening,
      technical,
      warning: smallSample(apps.length) ? "Insufficient Data" : null,
    };
  });
}

export function analyticsModel(state: CareerOSState, range: DateRange) {
  const apps = active(state.applications).filter((a) => inDateRange(a.dateApplied || a.createdAt, range));
  const events = state.activityEvents.filter((e) => inDateRange(e.occurredAt, range));
  const readiness = computeReadiness(state);
  const snapshots = state.scoreSnapshots.filter((s) => inDateRange(s.capturedAt, range));
  const qualityAvg = apps.length ? apps.reduce((s, a) => s + applicationQualityValue(a, state), 0) / apps.length : 0;
  return {
    readiness,
    snapshots,
    funnel: funnelMetrics(apps),
    byRole: groupConversion(apps, (a) => a.role),
    byTier: groupConversion(apps, (a) => a.tier),
    bySource: groupConversion(apps, (a) => a.platform),
    byReferral: groupConversion(apps, (a) => (a.referralContactId || a.referralContact ? "Referral" : "Direct")),
    byMonth: groupConversion(apps, (a) => (a.dateApplied || a.createdAt).slice(0, 7)),
    resumes: resumePerformance(state),
    events: events.length,
    qualityAvg,
  };
}

export function velocitySeries(state: CareerOSState) {
  return [...state.scoreSnapshots]
    .sort((a, b) => a.capturedAt.localeCompare(b.capturedAt))
    .map((s) => ({
      date: s.capturedAt.slice(0, 10),
      readiness: s.globalReadiness,
      evidence: s.evidence,
      capability: s.capability,
      interview: s.interview,
      market: s.marketExecution,
    }));
}

export function hoursBreakdown(state: CareerOSState, range: DateRange) {
  const sessions = active(state.learningSessions).filter((s) => inDateRange(s.date, range));
  const learning = sessions.filter((s) => ["Course", "Reading", "Revision"].includes(s.activity)).reduce((n, s) => n + s.durationMinutes, 0) / 60;
  const building = sessions.filter((s) => ["Coding", "Lab"].includes(s.activity)).reduce((n, s) => n + s.durationMinutes, 0) / 60;
  const interview = sessions.filter((s) => s.activity === "Interview Practice").reduce((n, s) => n + s.durationMinutes, 0) / 60;
  const sprints = active(state.weeklySprints);
  const jobSearch = sprints.reduce((n, s) => n + s.jobSearchHours, 0);
  return { learning, building, interview, jobSearch };
}
