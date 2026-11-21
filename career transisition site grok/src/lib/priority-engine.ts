import type { CareerOSState, CareerTask } from "@/types/career";
import { isDueToday, isOverdue, parseDate } from "./dates";
import { projectEvidenceMissing } from "./evidence";
import { currentBottleneck, detectRisks } from "./risks";
import { allRoleReadiness } from "./role-readiness";
import { projectProductionScore } from "./scoring";
import { active } from "./utils";

export interface RankedAction {
  id: string;
  title: string;
  priority: "Very High" | "High" | "Medium";
  why: string[];
  href: string;
  score: number;
  category: CareerTask["category"] | "Evidence" | "Follow-up";
}

function deadlineBoost(due?: string) {
  if (!due) return 0;
  if (isOverdue(due)) return 24;
  if (isDueToday(due)) return 18;
  const d = parseDate(due);
  if (!d) return 0;
  return 8;
}

export function rankActions(state: CareerOSState): RankedAction[] {
  const actions: RankedAction[] = [];
  const bottleneck = currentBottleneck(state);
  const risks = detectRisks(state);
  const wipProjects = active(state.projects).filter((p) => p.status === "in_progress").length;

  for (const project of active(state.projects)) {
    const score = projectProductionScore(state, project);
    const missing = projectEvidenceMissing(state, project);
    if (project.status === "in_progress" && score.total >= 55) {
      actions.push({
        id: `deploy-${project.id}`,
        title: `Finish and deploy ${project.title}`,
        priority: "Very High",
        why: [
          "major evidence gap" ,
          `directly supports ${project.targetRole || "target roles"}`,
          "creates interview material",
          `production score ${score.total}/100`,
        ],
        href: `/projects/${project.id}`,
        score: 90 + (100 - score.total) * 0.1 - (wipProjects > state.settings.maxActiveProjects ? 8 : 0),
        category: "Project",
      });
    } else if (missing.length && project.status !== "planned") {
      actions.push({
        id: `evidence-${project.id}`,
        title: `Close evidence gaps on ${project.title}`,
        priority: "High",
        why: missing.slice(0, 3),
        href: `/projects/${project.id}`,
        score: 70 + missing.length * 3,
        category: "Evidence",
      });
    }
  }

  for (const app of active(state.applications)) {
    if (app.nextFollowUpDate && isOverdue(app.nextFollowUpDate) && app.status !== "Rejected") {
      actions.push({
        id: `follow-${app.id}`,
        title: `Follow up: ${app.company} · ${app.role}`,
        priority: "Very High",
        why: ["overdue follow-up", `${app.status} stage`, "market conversion depends on hygiene"],
        href: `/jobs/${app.id}`,
        score: 88 + deadlineBoost(app.nextFollowUpDate),
        category: "Follow-up",
      });
    }
  }

  for (const contact of active(state.contacts)) {
    if (contact.nextTouchpointDate && isOverdue(contact.nextTouchpointDate)) {
      actions.push({
        id: `touch-${contact.id}`,
        title: `Networking touchpoint: ${contact.name}`,
        priority: "High",
        why: ["overdue relationship maintenance", contact.company],
        href: `/contacts/${contact.id}`,
        score: 76,
        category: "Networking",
      });
    }
  }

  for (const round of active(state.interviewRounds)) {
    if (round.outcome === "Upcoming" && round.scheduledAt) {
      actions.push({
        id: `prep-${round.id}`,
        title: `Prepare interview packet · round ${round.roundNumber}`,
        priority: "Very High",
        why: ["upcoming interview", round.type, "assemble evidence, STAR, and gaps"],
        href: `/jobs/${round.applicationId}`,
        score: 92 + deadlineBoost(round.scheduledAt),
        category: "Interview",
      });
    }
  }

  const roles = allRoleReadiness(state).filter((r) => r.role.priority === "Primary");
  for (const role of roles) {
    const gap = role.evidenceMissing[0] ?? role.missing[0];
    if (gap) {
      actions.push({
        id: `role-gap-${role.role.id}-${gap.competency.id}`,
        title: gap.nextAction,
        priority: "High",
        why: [`${role.role.name} readiness ${role.score}%`, `${gap.competency.name} is ${gap.band}`],
        href: `/roles/${role.role.id}`,
        score: 72 + gap.importance * 3,
        category: "Evidence",
      });
    }
  }

  for (const task of active(state.tasks).filter((t) => !t.completed)) {
    const blocked = (task.blockedByTaskIds ?? []).some((id) => {
      const other = state.tasks.find((t) => t.id === id);
      return other && !other.completed;
    });
    if (blocked) continue;
    const p = task.priority === "Critical" ? 20 : task.priority === "High" ? 12 : task.priority === "Medium" ? 5 : 0;
    actions.push({
      id: `task-${task.id}`,
      title: task.title,
      priority: task.priority === "Critical" || task.priority === "High" ? "High" : "Medium",
      why: [task.category, task.dueDate ? `due ${task.dueDate}` : "queued"],
      href: "/today",
      score: 50 + p + deadlineBoost(task.dueDate),
      category: task.category,
    });
  }

  if (bottleneck.kind === "Evidence") {
    actions.forEach((a) => {
      if (a.category === "Evidence" || a.category === "Project") a.score += 8;
    });
  }
  if (risks.some((r) => r.kind === "Follow-Up Debt")) {
    actions.forEach((a) => {
      if (a.category === "Follow-up" || a.category === "Networking") a.score += 6;
    });
  }

  const seen = new Set<string>();
  return actions
    .sort((a, b) => b.score - a.score)
    .filter((a) => {
      if (seen.has(a.title)) return false;
      seen.add(a.title);
      return true;
    })
    .slice(0, 5)
    .map((a) => ({
      ...a,
      priority: a.score >= 88 ? "Very High" : a.score >= 70 ? "High" : "Medium",
    }));
}

export function todayModel(state: CareerOSState) {
  const ranked = rankActions(state);
  const tasks = active(state.tasks);
  const dueToday = tasks.filter((t) => !t.completed && isDueToday(t.dueDate));
  const overdue = tasks.filter((t) => !t.completed && isOverdue(t.dueDate));
  const waiting = tasks.filter((t) => !t.completed && t.waitingOn);
  const completedToday = tasks.filter((t) => t.completed && t.completedAt && isDueToday(t.completedAt));
  return {
    top3: ranked.slice(0, 3),
    upNext: ranked.slice(3, 5),
    dueToday,
    overdue,
    waiting,
    completedToday,
  };
}
