import type { CareerOSState } from "@/types/career";
import { isOverdue } from "./dates";
import { findDuplicateJobs } from "./duplicates";
import { safeUrl } from "./utils";

export interface HealthIssue {
  id: string;
  severity: "high" | "medium" | "low";
  title: string;
  detail: string;
  href?: string;
  repair?: "archive-duplicate" | "clear-url" | "none";
  entityId?: string;
}

export function dataHealth(state: CareerOSState): HealthIssue[] {
  const issues: HealthIssue[] = [];
  state.applications.forEach((job) => {
    if (job.jobUrl && !safeUrl(job.jobUrl)) {
      issues.push({
        id: `url-job-${job.id}`,
        severity: "medium",
        title: "Invalid job URL",
        detail: `${job.company} · ${job.role}`,
        href: `/jobs/${job.id}`,
        repair: "clear-url",
        entityId: job.id,
      });
    }
    const dupes = findDuplicateJobs(job, state.applications);
    if (dupes.length) {
      issues.push({
        id: `dup-job-${job.id}`,
        severity: "low",
        title: "Possible duplicate application",
        detail: `${job.company} · ${job.role} matches ${dupes.length} other record(s).`,
        href: `/jobs/${job.id}`,
        repair: "none",
        entityId: job.id,
      });
    }
    if (job.resumeVariantId && !state.resumeVariants.some((r) => r.id === job.resumeVariantId)) {
      issues.push({
        id: `orphan-resume-${job.id}`,
        severity: "medium",
        title: "Application points at a missing resume",
        detail: `${job.company} · ${job.role}`,
        href: `/jobs/${job.id}`,
        entityId: job.id,
      });
    }
  });

  state.evidenceArtifacts.forEach((e) => {
    if (e.projectId && !state.projects.some((p) => p.id === e.projectId)) {
      issues.push({
        id: `orphan-ev-${e.id}`,
        severity: "medium",
        title: "Evidence linked to missing project",
        detail: e.title,
        href: "/evidence",
        entityId: e.id,
      });
    }
    if (e.url && !safeUrl(e.url)) {
      issues.push({
        id: `url-ev-${e.id}`,
        severity: "low",
        title: "Invalid evidence URL",
        detail: e.title,
        href: "/evidence",
      });
    }
  });

  state.projectMilestones.forEach((m) => {
    if (!state.projects.some((p) => p.id === m.projectId)) {
      issues.push({
        id: `orphan-ms-${m.id}`,
        severity: "low",
        title: "Milestone linked to missing project",
        detail: m.title,
      });
    }
  });

  state.applications.forEach((job) => {
    if (job.nextFollowUpDate && isOverdue(job.nextFollowUpDate) && job.status !== "Rejected" && job.status !== "Offer") {
      issues.push({
        id: `stale-job-${job.id}`,
        severity: "high",
        title: "Overdue follow-up",
        detail: `${job.company} · ${job.role}`,
        href: `/jobs/${job.id}`,
      });
    }
  });

  return issues;
}
