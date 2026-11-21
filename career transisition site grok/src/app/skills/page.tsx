"use client";

import { useMemo, useState } from "react";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { EmptyState, SectionHeader } from "@/components/shared/empty-state";
import { SKILL_CATEGORIES, TARGET_ROLE_NAMES } from "@/lib/constants";
import { evidenceLabel, skillEvidenceConfidence } from "@/lib/evidence";
import { newSkill } from "@/lib/factories";
import { skillMasteryScore } from "@/lib/scoring";
import { active } from "@/lib/utils";
import { useCareerStore } from "@/store/career-store";
import type { SkillItem } from "@/types/career";

export default function SkillsPage() {
  const state = useCareerStore((s) => s.state);
  const add = useCareerStore((s) => s.addSkill);
  const update = useCareerStore((s) => s.updateSkill);
  const archive = useCareerStore((s) => s.archiveSkill);
  const addSession = useCareerStore((s) => s.addLearningSession);
  const [q, setQ] = useState("");
  const [cat, setCat] = useState("all");
  const [status, setStatus] = useState("all");
  const [view, setView] = useState<"table" | "cards">("table");
  const [editing, setEditing] = useState<SkillItem | null>(null);

  const items = useMemo(() => {
    return active(state.skills).filter((s) => {
      if (cat !== "all" && s.category !== cat) return false;
      if (status !== "all" && s.status !== status) return false;
      if (q && !`${s.name} ${s.summary} ${s.mappedRoles.join(" ")}`.toLowerCase().includes(q.toLowerCase())) return false;
      return true;
    });
  }, [state.skills, q, cat, status]);

  return (
    <div>
      <SectionHeader
        title="Skills"
        description="Mastery is separate from evidence confidence. A mastered skill with no artifact is not fully scored."
        actions={
          <Button onClick={() => setEditing(newSkill())}>Add Skill</Button>
        }
      />
      <div className="mb-4 flex flex-wrap gap-2">
        <Input className="max-w-xs" placeholder="Search skills" value={q} onChange={(e) => setQ(e.target.value)} />
        <Select value={cat} onChange={(e) => setCat(e.target.value)}>
          <option value="all">All categories</option>
          {SKILL_CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </Select>
        <Select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="all">All statuses</option>
          <option value="to_learn">to learn</option>
          <option value="in_progress">in progress</option>
          <option value="mastered">mastered</option>
        </Select>
        <Button variant="outline" size="sm" onClick={() => setView(view === "table" ? "cards" : "table")}>
          {view === "table" ? "Cards" : "Table"}
        </Button>
      </div>

      {items.length === 0 ? (
        <EmptyState title="No skills yet" detail="Add Python, agents, RAG, and LLMOps skills mapped to target roles." actionLabel="Add Skill" onAction={() => setEditing(newSkill())} />
      ) : view === "table" ? (
        <div className="card overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-[13px]">
            <thead className="text-[11px] tracking-wide text-slate-500 uppercase">
              <tr>
                <th className="px-3 py-2">Skill</th>
                <th className="px-3 py-2">Category</th>
                <th className="px-3 py-2">Mastery</th>
                <th className="px-3 py-2">Evidence</th>
                <th className="px-3 py-2">Roles</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((s) => {
                const conf = skillEvidenceConfidence(state, s);
                const scored = skillMasteryScore(state, s);
                return (
                  <tr key={s.id} className="border-t border-white/5">
                    <td className="px-3 py-2">
                      <button type="button" className="text-left font-medium text-white" onClick={() => setEditing(s)}>
                        {s.name}
                      </button>
                      <div className="text-[12px] text-slate-500">{s.whatNext || s.summary}</div>
                    </td>
                    <td className="px-3 py-2 text-slate-400">{SKILL_CATEGORIES.find((c) => c.value === s.category)?.label}</td>
                    <td className="px-3 py-2">
                      <StatusBadge value={s.status} />
                    </td>
                    <td className="px-3 py-2">
                      <Badge tone={conf >= 0.75 ? "green" : conf >= 0.45 ? "amber" : "red"}>{evidenceLabel(conf)}</Badge>
                      <span className="tabular ml-2 text-slate-500">{Math.round(scored.combined * 100)}</span>
                    </td>
                    <td className="px-3 py-2 text-slate-400">{s.mappedRoles.slice(0, 2).join(", ")}</td>
                    <td className="px-3 py-2 text-right">
                      <Button variant="ghost" size="sm" onClick={() => archive(s.id)}>
                        Archive
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {items.map((s) => (
            <button key={s.id} type="button" className="card p-4 text-left" onClick={() => setEditing(s)}>
              <div className="flex items-center justify-between">
                <p className="font-medium">{s.name}</p>
                <StatusBadge value={s.status} />
              </div>
              <p className="mt-2 text-[12px] text-slate-400">{s.summary}</p>
            </button>
          ))}
        </div>
      )}

      {editing ? (
        <Dialog open onOpenChange={() => setEditing(null)}>
          <DialogContent title={editing.name || "New skill"}>
            <div className="grid gap-3">
              <Field label="Name">
                <Input value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
              </Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Category">
                  <Select value={editing.category} onChange={(e) => setEditing({ ...editing, category: e.target.value as SkillItem["category"] })}>
                    {SKILL_CATEGORIES.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </Select>
                </Field>
                <Field label="Mastery">
                  <Select value={editing.status} onChange={(e) => setEditing({ ...editing, status: e.target.value as SkillItem["status"] })}>
                    <option value="to_learn">to learn</option>
                    <option value="in_progress">in progress</option>
                    <option value="mastered">mastered</option>
                  </Select>
                </Field>
              </div>
              <Field label="Source learned">
                <Input value={editing.sourceLearned} onChange={(e) => setEditing({ ...editing, sourceLearned: e.target.value })} />
              </Field>
              <Field label="Source URL">
                <Input value={editing.sourceUrl} onChange={(e) => setEditing({ ...editing, sourceUrl: e.target.value })} />
              </Field>
              <Field label="Summary">
                <Textarea value={editing.summary} onChange={(e) => setEditing({ ...editing, summary: e.target.value })} />
              </Field>
              <Field label="What next">
                <Textarea value={editing.whatNext} onChange={(e) => setEditing({ ...editing, whatNext: e.target.value })} />
              </Field>
              <Field label="Mapped roles">
                <Select
                  value={editing.mappedRoles[0] ?? ""}
                  onChange={(e) => setEditing({ ...editing, mappedRoles: e.target.value ? [e.target.value] : [] })}
                >
                  <option value="">—</option>
                  {TARGET_ROLE_NAMES.map((r) => (
                    <option key={r}>{r}</option>
                  ))}
                </Select>
              </Field>
              {state.skills.some((s) => s.id === editing.id) ? (
                <p className="text-[12px] text-slate-400">
                  Evidence confidence: {evidenceLabel(skillEvidenceConfidence(state, editing))} · Mastery: {editing.status}
                </p>
              ) : null}
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setEditing(null)}>
                Cancel
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  addSession({
                    id: crypto.randomUUID(),
                    createdAt: new Date().toISOString(),
                    updatedAt: new Date().toISOString(),
                    date: new Date().toISOString().slice(0, 10),
                    durationMinutes: 45,
                    activity: "Coding",
                    notes: `Session on ${editing.name}`,
                    skillId: editing.id,
                  });
                }}
              >
                Log 45m session
              </Button>
              <Button
                onClick={() => {
                  if (state.skills.some((s) => s.id === editing.id)) update(editing);
                  else add(editing);
                  setEditing(null);
                }}
              >
                Save
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      ) : null}
    </div>
  );
}
