"use client";

import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { EmptyState, SectionHeader } from "@/components/shared/empty-state";
import { newEvidence } from "@/lib/factories";
import { evidenceGraph } from "@/lib/role-readiness";
import { active, safeUrl, externalRel } from "@/lib/utils";
import { useCareerStore } from "@/store/career-store";
import type { EvidenceArtifact } from "@/types/career";

const TYPES = [
  "GitHub Repository",
  "Live Demo",
  "Architecture Diagram",
  "Benchmark",
  "Evaluation Report",
  "Case Study",
  "Resume Bullet",
  "STAR Story",
  "Technical Article",
  "Credential",
  "Presentation",
  "Other",
] as const;

export default function EvidencePage() {
  const state = useCareerStore((s) => s.state);
  const add = useCareerStore((s) => s.addEvidence);
  const update = useCareerStore((s) => s.updateEvidence);
  const archive = useCareerStore((s) => s.archiveEvidence);
  const [q, setQ] = useState("");
  const [editing, setEditing] = useState<EvidenceArtifact | null>(null);
  const items = useMemo(
    () => active(state.evidenceArtifacts).filter((e) => `${e.title} ${e.type} ${e.description}`.toLowerCase().includes(q.toLowerCase())),
    [state.evidenceArtifacts, q],
  );
  const primary = active(state.targetRoles).find((r) => r.priority === "Primary" && r.active);
  const graph = primary ? evidenceGraph(state, primary) : [];

  return (
    <div>
      <SectionHeader
        title="Evidence Library"
        description="Evidence connects projects, skills, competencies, and roles. Claims without artifacts stay partial."
        actions={<Button onClick={() => setEditing(newEvidence())}>Add Evidence</Button>}
      />
      <Input className="mb-4 max-w-sm" placeholder="Search evidence" value={q} onChange={(e) => setQ(e.target.value)} />

      {primary ? (
        <section className="card mb-4 p-4">
          <h2 className="text-sm font-semibold">Evidence graph · {primary.name}</h2>
          <div className="mt-3 space-y-3 text-[13px]">
            {graph.map((g) => (
              <div key={g.competency.id}>
                <p className="font-medium">
                  {g.competency.name} <Badge tone={g.band === "Strong" ? "green" : g.band === "Gap" ? "red" : "amber"}>{g.band}</Badge>
                </p>
                <ul className="mt-1 list-disc pl-5 text-slate-400">
                  {g.skills.map((s) => (
                    <li key={s.id}>Skill: {s.name}</li>
                  ))}
                  {g.projects.map((p) => (
                    <li key={p.id}>Project: {p.title}</li>
                  ))}
                  {g.artifacts.map((a) => (
                    <li key={a.id}>{a.type}: {a.title}</li>
                  ))}
                  {g.skills.length + g.projects.length + g.artifacts.length === 0 ? <li>GAP: {g.nextAction}</li> : null}
                </ul>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {items.length === 0 ? (
        <EmptyState title="No evidence yet" detail="Attach GitHub, live demos, architecture, benchmarks, and evaluation reports." />
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {items.map((e) => (
            <button key={e.id} type="button" className="card p-4 text-left" onClick={() => setEditing(e)}>
              <div className="flex items-start justify-between gap-2">
                <p className="font-medium">{e.title}</p>
                <Badge tone={e.strength === "Strong" ? "green" : e.strength === "Usable" ? "cyan" : "amber"}>{e.strength}</Badge>
              </div>
              <p className="mt-1 text-[12px] text-slate-400">{e.type}</p>
              {safeUrl(e.url) ? (
                <a className="mt-2 inline-block text-[12px] text-cyan-300" href={safeUrl(e.url)!} {...externalRel()} onClick={(ev) => ev.stopPropagation()}>
                  Open
                </a>
              ) : null}
            </button>
          ))}
        </div>
      )}

      {editing ? (
        <Dialog open onOpenChange={() => setEditing(null)}>
          <DialogContent title="Evidence">
            <div className="grid gap-3">
              <Field label="Title"><Input value={editing.title} onChange={(e) => setEditing({ ...editing, title: e.target.value })} /></Field>
              <Field label="Type">
                <Select value={editing.type} onChange={(e) => setEditing({ ...editing, type: e.target.value as EvidenceArtifact["type"] })}>
                  {TYPES.map((t) => (
                    <option key={t}>{t}</option>
                  ))}
                </Select>
              </Field>
              <Field label="Strength">
                <Select value={editing.strength} onChange={(e) => setEditing({ ...editing, strength: e.target.value as EvidenceArtifact["strength"] })}>
                  <option>Draft</option>
                  <option>Usable</option>
                  <option>Strong</option>
                </Select>
              </Field>
              <Field label="URL"><Input value={editing.url ?? ""} onChange={(e) => setEditing({ ...editing, url: e.target.value })} /></Field>
              <Field label="Description"><Textarea value={editing.description} onChange={(e) => setEditing({ ...editing, description: e.target.value })} /></Field>
              <Field label="Project">
                <Select value={editing.projectId ?? ""} onChange={(e) => setEditing({ ...editing, projectId: e.target.value || undefined })}>
                  <option value="">—</option>
                  {active(state.projects).map((p) => (
                    <option key={p.id} value={p.id}>{p.title}</option>
                  ))}
                </Select>
              </Field>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="ghost" onClick={() => archive(editing.id)}>Archive</Button>
              <Button onClick={() => { if (state.evidenceArtifacts.some((x) => x.id === editing.id)) update(editing); else add(editing); setEditing(null); }}>Save</Button>
            </div>
          </DialogContent>
        </Dialog>
      ) : null}
    </div>
  );
}
