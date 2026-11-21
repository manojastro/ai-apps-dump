"use client";

import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { SectionHeader } from "@/components/shared/empty-state";
import { weekStartIso } from "@/lib/dates";
import { newTask } from "@/lib/factories";
import { createId, timestamps } from "@/lib/ids";
import { active } from "@/lib/utils";
import { useCareerStore } from "@/store/career-store";
import type { CareerTask, WeeklySprint } from "@/types/career";

export default function ExecutionPage() {
  const state = useCareerStore((s) => s.state);
  const addTask = useCareerStore((s) => s.addTask);
  const updateTask = useCareerStore((s) => s.updateTask);
  const addSprint = useCareerStore((s) => s.addSprint);
  const updateSprint = useCareerStore((s) => s.updateSprint);
  const tasks = active(state.tasks);
  const week = weekStartIso();
  let sprint = active(state.weeklySprints).find((s) => s.weekStart === week);
  if (!sprint) {
    sprint = {
      id: createId("sp"),
      ...timestamps(),
      weekStart: week,
      title: `Week of ${week}`,
      objectives: ["Ship evidence", "Quality applications", "Interview reps"],
      completedObjectives: [],
      learningHours: 0,
      applicationsSubmitted: 0,
      networkingActions: 0,
      interviewSessions: 0,
      buildingHours: 0,
      jobSearchHours: 0,
      availableHours: state.settings.weeklyAvailableHours,
      retrospective: "",
    };
  }

  const setSprint = (patch: Partial<WeeklySprint>) => {
    const next = { ...sprint!, ...patch };
    if (state.weeklySprints.some((s) => s.id === next.id)) updateSprint(next);
    else addSprint(next);
  };

  const planned = sprint.learningHours + sprint.buildingHours + sprint.interviewSessions + sprint.jobSearchHours;
  return (
    <div className="space-y-5">
      <SectionHeader title="Weekly Execution" description="Engineering-style sprints. Outputs vs outcomes. Do not reward overwork." />
      <section className="card p-4">
        <h2 className="text-sm font-semibold">{sprint.title}</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-4">
          <Field label="Learning hours"><Input type="number" value={sprint.learningHours} onChange={(e) => setSprint({ learningHours: Number(e.target.value) })} /></Field>
          <Field label="Building hours"><Input type="number" value={sprint.buildingHours} onChange={(e) => setSprint({ buildingHours: Number(e.target.value) })} /></Field>
          <Field label="Applications"><Input type="number" value={sprint.applicationsSubmitted} onChange={(e) => setSprint({ applicationsSubmitted: Number(e.target.value) })} /></Field>
          <Field label="Networking actions"><Input type="number" value={sprint.networkingActions} onChange={(e) => setSprint({ networkingActions: Number(e.target.value) })} /></Field>
        </div>
        <p className="mt-2 text-[12px] text-slate-500">
          Planned/logged {planned}h vs available {sprint.availableHours}h
          {planned > sprint.availableHours ? " · overwork is not scored as progress" : ""}
        </p>
        <div className="mt-3">
          {sprint.objectives.map((o) => (
            <label key={o} className="mb-1 flex items-center gap-2 text-[13px]">
              <input
                type="checkbox"
                checked={sprint!.completedObjectives.includes(o)}
                onChange={(e) => {
                  const next = e.target.checked
                    ? [...sprint!.completedObjectives, o]
                    : sprint!.completedObjectives.filter((x) => x !== o);
                  setSprint({ completedObjectives: next });
                }}
              />
              {o}
            </label>
          ))}
        </div>
      </section>

      <section className="card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold">Tasks</h2>
          <Button size="sm" onClick={() => addTask(newTask({ title: "New task" }))}>Add task</Button>
        </div>
        {tasks.map((t) => (
          <div key={t.id} className="mb-2 flex flex-wrap items-center gap-2">
            <input type="checkbox" checked={t.completed} onChange={(e) => updateTask({ ...t, completed: e.target.checked, completedAt: e.target.checked ? new Date().toISOString() : undefined })} />
            <Input className="max-w-sm" value={t.title} onChange={(e) => updateTask({ ...t, title: e.target.value })} />
            <Select value={t.priority} onChange={(e) => updateTask({ ...t, priority: e.target.value as CareerTask["priority"] })}>
              {["Critical", "High", "Medium", "Low"].map((p) => <option key={p}>{p}</option>)}
            </Select>
            <Input type="date" className="w-40" value={t.dueDate ?? ""} onChange={(e) => updateTask({ ...t, dueDate: e.target.value })} />
          </div>
        ))}
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">Weekly retrospective</h2>
        <p className="mb-2 text-[12px] text-slate-500">Distinguish outputs from outcomes.</p>
        {(["movedForward", "blocked", "producedInterviews", "strengthenedCapability", "createdEvidence", "shouldStop", "nextWeekPriority"] as const).map((k) => (
          <Field key={k} label={k} className="mt-2">
            <Textarea value={sprint[k] ?? ""} onChange={(e) => setSprint({ [k]: e.target.value })} />
          </Field>
        ))}
        <Field label="Retrospective notes" className="mt-2">
          <Textarea value={sprint.retrospective} onChange={(e) => setSprint({ retrospective: e.target.value })} />
        </Field>
      </section>
    </div>
  );
}
