"use client";

import Link from "next/link";
import { useMemo } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState, SectionHeader } from "@/components/shared/empty-state";
import { todayModel } from "@/lib/priority-engine";
import { useCareerStore } from "@/store/career-store";

export default function TodayPage() {
  const state = useCareerStore((s) => s.state);
  const updateTask = useCareerStore((s) => s.updateTask);
  const model = useMemo(() => todayModel(state), [state]);

  return (
    <div>
      <SectionHeader title="Today" description="A focused execution surface — not the full task dump." />
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card p-4">
          <h2 className="mb-3 text-sm font-semibold">Top 3</h2>
          {model.top3.length === 0 ? <p className="text-[13px] text-slate-500">Nothing ranked yet.</p> : null}
          <ol className="space-y-2">
            {model.top3.map((a, i) => (
              <li key={a.id} className="card-2 p-3">
                <div className="flex items-start justify-between gap-2">
                  <Link href={a.href} className="text-[13px] font-medium text-white hover:text-cyan-300">
                    {i + 1}. {a.title}
                  </Link>
                  <Badge tone="amber">{a.priority}</Badge>
                </div>
                <p className="mt-1 text-[12px] text-slate-400">{a.why.join(" · ")}</p>
              </li>
            ))}
          </ol>
        </section>
        <section className="card p-4">
          <h2 className="mb-3 text-sm font-semibold">Up Next</h2>
          {model.upNext.length === 0 ? <p className="text-[13px] text-slate-500">Queue is empty.</p> : null}
          {model.upNext.map((a) => (
            <Link key={a.id} href={a.href} className="mb-2 block text-[13px] text-slate-300 hover:text-white">
              {a.title}
            </Link>
          ))}
        </section>
        <section className="card p-4">
          <h2 className="mb-3 text-sm font-semibold">Due Today</h2>
          {model.dueToday.length === 0 ? <p className="text-[13px] text-slate-500">Nothing due today.</p> : null}
          {model.dueToday.map((t) => (
            <TaskRow key={t.id} title={t.title} onDone={() => updateTask({ ...t, completed: true, completedAt: new Date().toISOString() })} />
          ))}
        </section>
        <section className="card p-4">
          <h2 className="mb-3 text-sm font-semibold">Overdue</h2>
          {model.overdue.length === 0 ? <p className="text-[13px] text-slate-500">No overdue tasks.</p> : null}
          {model.overdue.map((t) => (
            <TaskRow key={t.id} title={t.title} overdue onDone={() => updateTask({ ...t, completed: true, completedAt: new Date().toISOString() })} />
          ))}
        </section>
        <section className="card p-4">
          <h2 className="mb-3 text-sm font-semibold">Waiting</h2>
          {model.waiting.length === 0 ? <p className="text-[13px] text-slate-500">Nothing blocked.</p> : null}
          {model.waiting.map((t) => (
            <p key={t.id} className="text-[13px] text-slate-300">
              {t.title} — {t.waitingOn}
            </p>
          ))}
        </section>
        <section className="card p-4">
          <h2 className="mb-3 text-sm font-semibold">Completed Today</h2>
          {model.completedToday.length === 0 ? <p className="text-[13px] text-slate-500">No completions yet.</p> : null}
          {model.completedToday.map((t) => (
            <p key={t.id} className="text-[13px] text-emerald-300">
              {t.title}
            </p>
          ))}
        </section>
      </div>
      {activeHint(state)}
    </div>
  );
}

function TaskRow({ title, onDone, overdue }: { title: string; onDone: () => void; overdue?: boolean }) {
  return (
    <div className="mb-2 flex items-center justify-between gap-2">
      <p className={`text-[13px] ${overdue ? "text-rose-300" : "text-slate-200"}`}>{title}</p>
      <Button size="sm" variant="outline" onClick={onDone}>
        Done
      </Button>
    </div>
  );
}

function activeHint(state: { settings: { maxActiveProjects: number }; projects: { status: string; archivedAt?: string }[] }) {
  const n = state.projects.filter((p) => !p.archivedAt && p.status === "in_progress").length;
  if (n <= state.settings.maxActiveProjects) return null;
  return (
    <div className="mt-4">
      <EmptyState
        title="WIP warning"
        detail={`${n} projects are currently in progress. Finishing one is likely more valuable than starting another.`}
      />
    </div>
  );
}
