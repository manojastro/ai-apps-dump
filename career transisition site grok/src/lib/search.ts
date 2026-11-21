import type { CareerOSState } from "@/types/career";
import { active } from "./utils";

export interface SearchHit {
  id: string;
  entity: string;
  title: string;
  subtitle: string;
  href: string;
}

function match(q: string, ...parts: Array<string | undefined>) {
  const hay = parts.filter(Boolean).join(" ").toLowerCase();
  return hay.includes(q);
}

export function searchState(state: CareerOSState, query: string): SearchHit[] {
  const q = query.trim().toLowerCase();
  if (q.length < 2) return [];
  const hits: SearchHit[] = [];

  for (const j of active(state.applications)) {
    if (match(q, j.company, j.role, j.platform, j.notes)) {
      hits.push({ id: j.id, entity: "Job", title: `${j.company} · ${j.role}`, subtitle: j.status, href: `/jobs/${j.id}` });
    }
  }
  for (const c of active(state.targetCompanies)) {
    if (match(q, c.name, c.whyTarget, c.notes)) {
      hits.push({ id: c.id, entity: "Company", title: c.name, subtitle: c.priority, href: `/companies/${c.id}` });
    }
  }
  for (const r of active(state.targetRoles)) {
    if (match(q, r.name, r.notes)) {
      hits.push({ id: r.id, entity: "Role", title: r.name, subtitle: r.priority, href: `/roles/${r.id}` });
    }
  }
  for (const s of active(state.skills)) {
    if (match(q, s.name, s.summary, s.whatNext)) {
      hits.push({ id: s.id, entity: "Skill", title: s.name, subtitle: s.status, href: "/skills" });
    }
  }
  for (const p of active(state.projects)) {
    if (match(q, p.title, p.useCase, p.architectureSummary, p.targetRole)) {
      hits.push({ id: p.id, entity: "Project", title: p.title, subtitle: p.status, href: `/projects/${p.id}` });
    }
  }
  for (const e of active(state.evidenceArtifacts)) {
    if (match(q, e.title, e.description, e.type)) {
      hits.push({ id: e.id, entity: "Evidence", title: e.title, subtitle: e.type, href: "/evidence" });
    }
  }
  for (const c of active(state.contacts)) {
    if (match(q, c.name, c.company, c.designation, c.keyTakeaway)) {
      hits.push({ id: c.id, entity: "Contact", title: c.name, subtitle: c.company, href: `/contacts/${c.id}` });
    }
  }
  for (const i of active(state.interviewQuestions)) {
    if (match(q, i.question, i.answer, i.category)) {
      hits.push({ id: i.id, entity: "Interview", title: i.question, subtitle: i.category, href: "/interview" });
    }
  }
  for (const t of active(state.researchTopics)) {
    if (match(q, t.title, t.coreConcept, t.interviewTalkingPoints)) {
      hits.push({ id: t.id, entity: "Research", title: t.title, subtitle: t.isMastered ? "Mastered" : "Open", href: "/research" });
    }
  }
  for (const s of active(state.starStories)) {
    if (match(q, s.title, s.situation, s.result)) {
      hits.push({ id: s.id, entity: "STAR", title: s.title, subtitle: s.category, href: "/interview" });
    }
  }
  for (const a of active(state.achievements)) {
    if (match(q, a.title, a.context, a.result)) {
      hits.push({ id: a.id, entity: "Achievement", title: a.title, subtitle: "Achievement bank", href: "/assets" });
    }
  }
  return hits.slice(0, 40);
}
