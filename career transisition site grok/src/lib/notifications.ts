import type { CareerOSState } from "@/types/career";
import { daysUntil, isOverdue, isUpcoming, weekStartIso } from "./dates";
import { active } from "./utils";

export interface AppNotification {
  id: string;
  title: string;
  detail: string;
  href: string;
  tone: "amber" | "red" | "cyan";
}

export function deriveNotifications(state: CareerOSState): AppNotification[] {
  const out: AppNotification[] = [];
  for (const job of active(state.applications)) {
    if (job.nextFollowUpDate && isOverdue(job.nextFollowUpDate) && job.status !== "Rejected") {
      out.push({
        id: `fu-${job.id}`,
        title: "Follow-up overdue",
        detail: `${job.company} · ${job.role}`,
        href: `/jobs/${job.id}`,
        tone: "red",
      });
    }
  }
  for (const round of active(state.interviewRounds)) {
    if (round.outcome === "Upcoming" && round.scheduledAt && isUpcoming(round.scheduledAt, 2)) {
      const d = daysUntil(round.scheduledAt);
      out.push({
        id: `int-${round.id}`,
        title: d === 0 ? "Interview today" : "Interview approaching",
        detail: `${round.type} round ${round.roundNumber}`,
        href: `/jobs/${round.applicationId}`,
        tone: "amber",
      });
    }
  }
  for (const cert of active(state.certifications)) {
    if (cert.examDate && isUpcoming(cert.examDate, 14)) {
      out.push({
        id: `cert-${cert.id}`,
        title: "Certification approaching",
        detail: `${cert.name} (${cert.code})`,
        href: "/certifications",
        tone: "cyan",
      });
    }
  }
  for (const c of active(state.contacts)) {
    if (c.nextTouchpointDate && (isOverdue(c.nextTouchpointDate) || isUpcoming(c.nextTouchpointDate, 1))) {
      out.push({
        id: `net-${c.id}`,
        title: isOverdue(c.nextTouchpointDate) ? "Networking touchpoint overdue" : "Networking touchpoint due",
        detail: `${c.name} · ${c.company}`,
        href: `/contacts/${c.id}`,
        tone: isOverdue(c.nextTouchpointDate) ? "red" : "amber",
      });
    }
  }
  const week = weekStartIso();
  const sprint = active(state.weeklySprints).find((s) => s.weekStart === week);
  if (sprint && !sprint.retrospective && new Date().getDay() === 0) {
    out.push({
      id: "retro",
      title: "Weekly retrospective due",
      detail: sprint.title || `Week of ${week}`,
      href: "/execution",
      tone: "amber",
    });
  }
  return out.slice(0, 20);
}
