"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { ProgressBar } from "@/components/shared/metric-card";
import { createId, timestamps } from "@/lib/ids";
import { projectEvidenceMissing } from "@/lib/evidence";
import { projectProductionScore } from "@/lib/scoring";
import { safeUrl, externalRel } from "@/lib/utils";
import { useCareerStore } from "@/store/career-store";
import type { ProjectItem } from "@/types/career";

export default function ProjectDetailPage() {
  const { projectId: id } = useParams<{ projectId: string }>();
  const state = useCareerStore((s) => s.state);
  const update = useCareerStore((s) => s.updateProject);
  const archive = useCareerStore((s) => s.archiveProject);
  const addMs = useCareerStore((s) => s.addProjectMilestone);
  const updateMs = useCareerStore((s) => s.updateProjectMilestone);
  const addAdr = useCareerStore((s) => s.addArchitectureDecision);
  const addMetric = useCareerStore((s) => s.addProjectMetric);
  const addEvidence = useCareerStore((s) => s.addEvidence);
  const project = state.projects.find((p) => p.id === id);
  const [tab, setTab] = useState("overview");
  const score = useMemo(
    () => (project ? projectProductionScore(state, project) : { total: 0, parts: [] }),
    [state, project],
  );

  if (!project) return <p className="text-slate-400">Project not found.</p>;

  const missing = projectEvidenceMissing(state, project);
  const milestones = state.projectMilestones.filter((m) => m.projectId === project.id && !m.archivedAt);
  const adrs = state.architectureDecisions.filter((m) => m.projectId === project.id && !m.archivedAt);
  const metrics = state.projectMetrics.filter((m) => m.projectId === project.id && !m.archivedAt);
  const evidence = state.evidenceArtifacts.filter((e) => e.projectId === project.id && !e.archivedAt);

  const set = (patch: Partial<ProjectItem>) => update({ ...project, ...patch });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link href="/projects" className="text-[12px] text-slate-500">
            ← Projects
          </Link>
          <h1 className="mt-1 text-lg font-semibold">{project.title}</h1>
          <div className="mt-2 flex flex-wrap gap-2">
            <StatusBadge value={project.status} />
            <Badge tone="indigo">{project.maturity}</Badge>
            <Badge>{project.category}</Badge>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => set({ status: "deployed" })}>
            Mark deployed
          </Button>
          <Button variant="ghost" onClick={() => archive(project.id)}>
            Archive
          </Button>
        </div>
      </div>

      <div className="card p-4">
        <ProgressBar value={score.total} label="Production-readiness" />
        <details className="mt-3">
          <summary className="cursor-pointer text-[13px] text-cyan-300">Why this score?</summary>
          <ul className="mt-2 space-y-1 text-[13px] text-slate-400">
            {score.parts.map((p) => (
              <li key={p.key} className="flex justify-between gap-3">
                <span>{p.label}</span>
                <span className="tabular">
                  {Math.round(p.score)}/{p.max}
                </span>
              </li>
            ))}
          </ul>
        </details>
      </div>

      <div className="flex flex-wrap gap-1">
        {["overview", "build", "evidence", "defense"].map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded-md px-3 py-1.5 text-[13px] ${tab === t ? "bg-white/10 text-white" : "text-slate-400"}`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "overview" ? (
        <div className="grid gap-3 md:grid-cols-2">
          <Field label="Title">
            <Input value={project.title} onChange={(e) => set({ title: e.target.value })} />
          </Field>
          <Field label="Target role">
            <Input value={project.targetRole} onChange={(e) => set({ targetRole: e.target.value })} />
          </Field>
          <Field label="Category">
            <Select value={project.category} onChange={(e) => set({ category: e.target.value as ProjectItem["category"] })}>
              {["AIOps", "RAG", "Agents", "Security_LLMOps", "FullStack_SaaS"].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </Select>
          </Field>
          <Field label="Maturity">
            <Select value={project.maturity} onChange={(e) => set({ maturity: e.target.value as ProjectItem["maturity"] })}>
              {["Tutorial", "Prototype", "Portfolio Ready", "Production Grade"].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </Select>
          </Field>
          <Field label="Status">
            <Select value={project.status} onChange={(e) => set({ status: e.target.value as ProjectItem["status"] })}>
              <option value="planned">planned</option>
              <option value="in_progress">in progress</option>
              <option value="deployed">deployed</option>
            </Select>
          </Field>
          <Field label="Tech stack (comma)">
            <Input value={project.techStack.join(", ")} onChange={(e) => set({ techStack: e.target.value.split(",").map((x) => x.trim()).filter(Boolean) })} />
          </Field>
          <Field label="GitHub" className="md:col-span-2">
            <Input value={project.githubUrl} onChange={(e) => set({ githubUrl: e.target.value })} />
            {safeUrl(project.githubUrl) ? (
              <a className="text-[12px] text-cyan-300" href={safeUrl(project.githubUrl)!} {...externalRel()}>
                Open
              </a>
            ) : null}
          </Field>
          <Field label="Live URL" className="md:col-span-2">
            <Input value={project.liveUrl} onChange={(e) => set({ liveUrl: e.target.value })} />
          </Field>
          <Field label="Problem / use case" className="md:col-span-2">
            <Textarea value={project.useCase} onChange={(e) => set({ useCase: e.target.value })} />
          </Field>
          <Field label="Architecture" className="md:col-span-2">
            <Textarea value={project.architectureSummary} onChange={(e) => set({ architectureSummary: e.target.value })} />
          </Field>
          <Field label="STAR pitch" className="md:col-span-2">
            <Textarea value={project.starPitch} onChange={(e) => set({ starPitch: e.target.value })} />
          </Field>
        </div>
      ) : null}

      {tab === "build" ? (
        <div className="space-y-4">
          {(["evaluationNotes", "testingNotes", "safetyNotes", "observabilityNotes", "failureHandlingNotes", "documentationNotes"] as const).map((key) => (
            <Field key={key} label={key.replace("Notes", "")}>
              <Textarea value={project[key]} onChange={(e) => set({ [key]: e.target.value })} />
            </Field>
          ))}
          <section className="card p-4">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold">Milestones</h3>
              <Button size="sm" variant="outline" onClick={() => addMs({ id: createId("ms"), ...timestamps(), projectId: project.id, title: "New milestone", category: "Implementation", status: "Not Started", notes: "" })}>
                Add
              </Button>
            </div>
            {milestones.map((m) => (
              <div key={m.id} className="mb-2 flex flex-wrap items-center gap-2">
                <Input className="max-w-xs" value={m.title} onChange={(e) => updateMs({ ...m, title: e.target.value })} />
                <Select value={m.status} onChange={(e) => updateMs({ ...m, status: e.target.value as typeof m.status })}>
                  {["Not Started", "In Progress", "Blocked", "Complete"].map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </Select>
              </div>
            ))}
          </section>
          <section className="card p-4">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold">Architecture decisions</h3>
              <Button size="sm" variant="outline" onClick={() => addAdr({ id: createId("adr"), ...timestamps(), projectId: project.id, title: "Decision", context: "", decision: "", alternativesConsidered: "", tradeOffs: "", consequences: "" })}>
                Add ADR
              </Button>
            </div>
            {adrs.map((a) => (
              <p key={a.id} className="text-[13px] text-slate-300">
                {a.title}: {a.decision}
              </p>
            ))}
          </section>
          <section className="card p-4">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold">Metrics</h3>
              <Button size="sm" variant="outline" onClick={() => addMetric({ id: createId("pm"), ...timestamps(), projectId: project.id, name: "Metric", methodology: "", notes: "", achieved: "" })}>
                Add metric
              </Button>
            </div>
            {metrics.map((m) => (
              <p key={m.id} className="text-[13px]">
                {m.name}: {m.baseline ?? "—"} → {m.achieved ?? "—"} {m.unit}
              </p>
            ))}
          </section>
        </div>
      ) : null}

      {tab === "evidence" ? (
        <div className="space-y-3">
          <div className="card p-4">
            <h3 className="text-sm font-semibold">Missing evidence</h3>
            <ul className="mt-2 list-disc pl-4 text-[13px] text-amber-200">
              {missing.map((m) => (
                <li key={m}>{m}</li>
              ))}
            </ul>
            {missing.length === 0 ? <p className="text-[13px] text-emerald-300">No major gaps on this system.</p> : null}
            <Button className="mt-3" size="sm" onClick={() => addEvidence({ id: createId("ev"), ...timestamps(), title: `${project.title} artifact`, type: "Architecture Diagram", description: "", projectId: project.id, skillIds: [], competencyIds: [], mappedRoleIds: [], strength: "Draft" })}>
              Attach evidence
            </Button>
          </div>
          {evidence.map((e) => (
            <div key={e.id} className="card-2 p-3 text-[13px]">
              {e.title} · {e.type} · {e.strength}
            </div>
          ))}
        </div>
      ) : null}

      {tab === "defense" ? (
        <div className="grid gap-3">
          <Field label="30-second answer">
            <Textarea value={project.interviewDefense30s} onChange={(e) => set({ interviewDefense30s: e.target.value })} />
          </Field>
          <Field label="2-minute explanation">
            <Textarea value={project.interviewDefense2m} onChange={(e) => set({ interviewDefense2m: e.target.value })} />
          </Field>
          <Field label="Deep dive">
            <Textarea value={project.interviewDefenseDeep} onChange={(e) => set({ interviewDefenseDeep: e.target.value })} />
          </Field>
          <div className="card p-4 text-[13px] text-slate-400">
            Cover: why this project, architecture, model choice, why agentic vs deterministic, evaluation, failure, recovery, scale, security, cost, rejected alternatives, redesign.
          </div>
        </div>
      ) : null}
    </div>
  );
}
