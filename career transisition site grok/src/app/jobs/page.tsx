"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Input, Select } from "@/components/ui/field";
import { EmptyState, SectionHeader } from "@/components/shared/empty-state";
import { isOverdue } from "@/lib/dates";
import { findDuplicateJobs } from "@/lib/duplicates";
import { newJob } from "@/lib/factories";
import { TARGET_ROLE_NAMES } from "@/lib/constants";
import { active } from "@/lib/utils";
import { useCareerStore } from "@/store/career-store";
import type { ApplicationStatus, JobApplication } from "@/types/career";

const COLS: ApplicationStatus[] = ["Identified", "Referred", "Applied", "Screening", "Technical", "Offer", "Rejected"];

export default function JobsPage() {
  const state = useCareerStore((s) => s.state);
  const add = useCareerStore((s) => s.addApplication);
  const update = useCareerStore((s) => s.updateApplication);
  const [view, setView] = useState<"kanban" | "table">("kanban");
  const [q, setQ] = useState("");
  const [tier, setTier] = useState("all");
  const [draft, setDraft] = useState<JobApplication | null>(null);

  const items = useMemo(
    () =>
      active(state.applications).filter((j) => {
        if (tier !== "all" && j.tier !== tier) return false;
        if (q && !`${j.company} ${j.role} ${j.platform}`.toLowerCase().includes(q.toLowerCase())) return false;
        return true;
      }),
    [state.applications, q, tier],
  );

  const saveDraft = () => {
    if (!draft?.company || !draft.role) return toast.error("Company and role required");
    const dupes = findDuplicateJobs(draft, state.applications);
    if (dupes.length && !confirm(`Possible duplicate of ${dupes[0]?.company}. Add anyway?`)) return;
    add(draft);
    setDraft(null);
    toast.success("Job added");
  };

  return (
    <div>
      <SectionHeader
        title="Job Pipeline"
        description="Quality applications beat spray-and-pray. Counts never substitute for evidence and follow-up."
        actions={<Button onClick={() => setDraft(newJob())}>Add Job</Button>}
      />
      <div className="mb-4 flex flex-wrap gap-2">
        <Input className="max-w-xs" placeholder="Search" value={q} onChange={(e) => setQ(e.target.value)} />
        <Select value={tier} onChange={(e) => setTier(e.target.value)}>
          <option value="all">All tiers</option>
          {["GCC", "Enterprise IT", "AI Startup", "Consulting"].map((t) => <option key={t}>{t}</option>)}
        </Select>
        <Button variant="outline" size="sm" onClick={() => setView(view === "kanban" ? "table" : "kanban")}>
          {view === "kanban" ? "Table" : "Kanban"}
        </Button>
      </div>

      {items.length === 0 && !draft ? (
        <EmptyState title="No applications" detail="Identify a high-fit role, save the JD, pick a resume, then apply." />
      ) : null}

      {view === "kanban" ? (
        <div className="flex gap-3 overflow-x-auto pb-4">
          {COLS.map((col) => (
            <div key={col} className="card w-64 shrink-0 p-3">
              <p className="mb-2 text-[12px] text-slate-400">
                {col} · {items.filter((i) => i.status === col).length}
              </p>
              {items
                .filter((i) => i.status === col)
                .map((j) => (
                  <Link key={j.id} href={`/jobs/${j.id}`} className="card-2 mb-2 block p-2">
                    <p className="text-[13px] font-medium">{j.company}</p>
                    <p className="text-[12px] text-slate-400">{j.role}</p>
                    {j.nextFollowUpDate && isOverdue(j.nextFollowUpDate) && j.status !== "Rejected" ? (
                      <Badge tone="red">Follow-up overdue</Badge>
                    ) : null}
                  </Link>
                ))}
            </div>
          ))}
        </div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-[13px]">
            <thead className="text-[11px] text-slate-500 uppercase">
              <tr>
                {["Company", "Tier", "Role", "Source", "Applied", "Follow-up", "Resume", "Referral", "Status"].map((h) => (
                  <th key={h} className="px-3 py-2">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((j) => (
                <tr key={j.id} className="border-t border-white/5">
                  <td className="px-3 py-2"><Link href={`/jobs/${j.id}`} className="text-cyan-300">{j.company}</Link></td>
                  <td className="px-3 py-2">{j.tier}</td>
                  <td className="px-3 py-2">{j.role}</td>
                  <td className="px-3 py-2">{j.platform}</td>
                  <td className="px-3 py-2">{j.dateApplied}</td>
                  <td className="px-3 py-2">{j.nextFollowUpDate && isOverdue(j.nextFollowUpDate) ? <Badge tone="red">{j.nextFollowUpDate}</Badge> : j.nextFollowUpDate}</td>
                  <td className="px-3 py-2">{state.resumeVariants.find((r) => r.id === j.resumeVariantId)?.name ?? "—"}</td>
                  <td className="px-3 py-2">{state.ui.privacyMode ? "Hidden" : j.referralContact ?? "—"}</td>
                  <td className="px-3 py-2">
                    <Select value={j.status} onChange={(e) => update({ ...j, status: e.target.value as ApplicationStatus })}>
                      {COLS.map((c) => <option key={c}>{c}</option>)}
                    </Select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {draft ? (
        <div className="card mt-4 grid gap-3 p-4 md:grid-cols-2">
          <Field label="Company"><Input value={draft.company} onChange={(e) => setDraft({ ...draft, company: e.target.value })} /></Field>
          <Field label="Role">
            <Select value={draft.role} onChange={(e) => setDraft({ ...draft, role: e.target.value })}>
              {TARGET_ROLE_NAMES.map((r) => <option key={r}>{r}</option>)}
            </Select>
          </Field>
          <Field label="Tier">
            <Select value={draft.tier} onChange={(e) => setDraft({ ...draft, tier: e.target.value as JobApplication["tier"] })}>
              {["GCC", "Enterprise IT", "AI Startup", "Consulting"].map((t) => <option key={t}>{t}</option>)}
            </Select>
          </Field>
          <Field label="Platform"><Input value={draft.platform} onChange={(e) => setDraft({ ...draft, platform: e.target.value })} /></Field>
          <div className="md:col-span-2 flex gap-2">
            <Button onClick={saveDraft}>Save</Button>
            <Button variant="ghost" onClick={() => setDraft(null)}>Cancel</Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
