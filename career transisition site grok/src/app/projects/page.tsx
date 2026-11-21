"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/field";
import { EmptyState, SectionHeader } from "@/components/shared/empty-state";
import { ProgressBar } from "@/components/shared/metric-card";
import { newProject } from "@/lib/factories";
import { projectProductionScore } from "@/lib/scoring";
import { active } from "@/lib/utils";
import { useCareerStore } from "@/store/career-store";

export default function ProjectsPage() {
  const state = useCareerStore((s) => s.state);
  const add = useCareerStore((s) => s.addProject);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");
  const items = useMemo(
    () =>
      active(state.projects).filter((p) => {
        if (status !== "all" && p.status !== status) return false;
        if (q && !`${p.title} ${p.category} ${p.targetRole}`.toLowerCase().includes(q.toLowerCase())) return false;
        return true;
      }),
    [state.projects, q, status],
  );
  const wip = items.filter((p) => p.status === "in_progress").length;

  return (
    <div>
      <SectionHeader
        title="Projects"
        description="Prefer three exceptional production AI systems over fifteen shallow tutorials."
        actions={
          <Button
            onClick={() => {
              const p = newProject({ title: "New production system" });
              add(p);
            }}
          >
            Add Project
          </Button>
        }
      />
      {wip > state.settings.maxActiveProjects ? (
        <p className="mb-3 text-[13px] text-amber-300">
          {wip} projects are in progress. Limit is {state.settings.maxActiveProjects}. This is a warning, not a hard block.
        </p>
      ) : null}
      <div className="mb-4 flex flex-wrap gap-2">
        <Input className="max-w-xs" placeholder="Search projects" value={q} onChange={(e) => setQ(e.target.value)} />
        <Select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="all">All statuses</option>
          <option value="planned">planned</option>
          <option value="in_progress">in progress</option>
          <option value="deployed">deployed</option>
        </Select>
      </div>
      {items.length === 0 ? (
        <EmptyState title="No projects" detail="Start one production-grade agent, RAG, or AIOps system with evaluation." />
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {items.map((p) => {
            const score = projectProductionScore(state, p);
            return (
              <Link key={p.id} href={`/projects/${p.id}`} className="card p-4 hover:border-cyan-400/30">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium text-white">{p.title}</p>
                    <p className="mt-1 text-[12px] text-slate-400">
                      {p.category} · {p.targetRole}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <StatusBadge value={p.status} />
                    <Badge tone="indigo">{p.maturity}</Badge>
                  </div>
                </div>
                <div className="mt-3">
                  <ProgressBar value={score.total} label="Production readiness" />
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
