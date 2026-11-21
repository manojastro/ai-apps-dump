"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { SectionHeader } from "@/components/shared/empty-state";
import { PHASES, derivePhase } from "@/lib/phase";
import { dataHealth } from "@/lib/data-health";
import { exportContactsCsv, exportJobsCsv, exportProjectsCsv, exportSkillsCsv, previewJobCsv, rowsToApplications } from "@/lib/csv";
import { diagnosticExport } from "@/lib/export-import";
import { downloadText } from "@/lib/utils";
import { createId, timestamps } from "@/lib/ids";
import { useCareerStore } from "@/store/career-store";
import type { TransitionPhase } from "@/types/career";

export default function SettingsPage() {
  const state = useCareerStore((s) => s.state);
  const updateSettings = useCareerStore((s) => s.updateSettings);
  const setUi = useCareerStore((s) => s.setUi);
  const addCampaign = useCareerStore((s) => s.addCampaign);
  const updateCampaign = useCareerStore((s) => s.updateCampaign);
  const addApplication = useCareerStore((s) => s.addApplication);
  const loadDemo = useCareerStore((s) => s.loadDemo);
  const convertDemo = useCareerStore((s) => s.convertDemo);
  const resetState = useCareerStore((s) => s.resetState);
  const s = state.settings;
  const phase = derivePhase(state);
  const issues = dataHealth(state);
  const [csv, setCsv] = useState("");
  const preview = csv ? previewJobCsv(csv, { company: "company", role: "role", platform: "platform", status: "status", dateApplied: "dateApplied", jobUrl: "jobUrl", tier: "tier", location: "location" }, state.applications) : [];

  const milestones = [
    { label: "Transition started", ok: Boolean(s.transitionStartDate) },
    { label: "First AI skill mastered", ok: state.skills.some((x) => x.status === "mastered") },
    { label: "First production project", ok: state.projects.some((p) => p.status === "deployed" || p.maturity === "Production Grade") },
    { label: "First deployment", ok: state.projects.some((p) => p.status === "deployed") },
    { label: "First architecture case study", ok: state.architectureDecisions.length > 0 },
    { label: "First referral", ok: state.networkingInteractions.some((i) => i.type === "Referral") },
    { label: "First screening", ok: state.applications.some((a) => ["Screening", "Technical", "Offer"].includes(a.status)) },
    { label: "First AI technical interview", ok: state.interviewRounds.some((r) => r.type === "Technical" || r.type === "AI / ML") },
    { label: "First offer", ok: state.offers.length > 0 || state.applications.some((a) => a.status === "Offer") },
    { label: "Target compensation achieved", ok: state.offers.some((o) => (o.fixedCtc ?? 0) >= s.targetMinCtc) },
  ].filter((m) => m.ok);

  return (
    <div className="space-y-5">
      <SectionHeader title="Settings" description="Personal OS configuration. Data stays in this browser." />

      {state.ui.demoMode ? (
        <div className="card border-amber-500/30 p-4">
          <p className="font-medium text-amber-200">DEMO MODE</p>
          <p className="mt-1 text-[13px] text-slate-400">Demo records are labeled and must not be mixed into real analytics until converted.</p>
          <div className="mt-3 flex gap-2">
            <Button size="sm" onClick={() => convertDemo()}>Convert to My Workspace</Button>
            <Button size="sm" variant="danger" onClick={() => resetState()}>Reset and Start Clean</Button>
          </div>
        </div>
      ) : null}

      <section className="card p-4">
        <h2 className="text-sm font-semibold">Career targets</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-4">
          <Field label="Baseline LPA"><Input type="number" value={s.baselineCtc} onChange={(e) => updateSettings({ baselineCtc: Number(e.target.value) })} /></Field>
          <Field label="Target min"><Input type="number" value={s.targetMinCtc} onChange={(e) => updateSettings({ targetMinCtc: Number(e.target.value) })} /></Field>
          <Field label="Target max"><Input type="number" value={s.targetMaxCtc} onChange={(e) => updateSettings({ targetMaxCtc: Number(e.target.value) })} /></Field>
          <Field label="Stretch"><Input type="number" value={s.stretchCtc} onChange={(e) => updateSettings({ stretchCtc: Number(e.target.value) })} /></Field>
        </div>
        <div className="mt-3 grid gap-3 md:grid-cols-4">
          <Field label="Weekly hours"><Input type="number" value={s.weeklyAvailableHours} onChange={(e) => updateSettings({ weeklyAvailableHours: Number(e.target.value) })} /></Field>
          <Field label="Max active projects"><Input type="number" value={s.maxActiveProjects} onChange={(e) => updateSettings({ maxActiveProjects: Number(e.target.value) })} /></Field>
          <Field label="Max primary roles"><Input type="number" value={s.maxPrimaryRoles} onChange={(e) => updateSettings({ maxPrimaryRoles: Number(e.target.value) })} /></Field>
          <Field label="Apps / week"><Input type="number" value={s.weeklyApplicationsTarget} onChange={(e) => updateSettings({ weeklyApplicationsTarget: Number(e.target.value) })} /></Field>
        </div>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">Transition phase</h2>
        <p className="text-[13px] text-slate-400">Derived: {phase}. Manual override allowed.</p>
        <Select
          className="mt-2 max-w-sm"
          value={state.ui.transitionPhaseOverride ?? ""}
          onChange={(e) => setUi({ transitionPhaseOverride: (e.target.value || undefined) as TransitionPhase | undefined })}
        >
          <option value="">Use derived phase</option>
          {PHASES.map((p) => <option key={p}>{p}</option>)}
        </Select>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">Privacy</h2>
        <p className="mt-2 text-[13px] text-slate-400">
          Privacy Mode hides data visually. It does not encrypt stored information.
        </p>
        <p className="mt-2 text-[13px] text-slate-400">
          This app stores career data in the browser. A public Vercel URL does not automatically sync or back up that data. Use JSON Backup / Restore.
        </p>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">Data Health</h2>
        {issues.length === 0 ? <p className="mt-2 text-[13px] text-slate-500">No issues detected.</p> : null}
        {issues.map((i) => (
          <div key={i.id} className="mt-2 flex items-center justify-between text-[13px]">
            <span>{i.title} — {i.detail}</span>
            <Badge tone={i.severity === "high" ? "red" : "amber"}>{i.severity}</Badge>
          </div>
        ))}
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">Milestone timeline</h2>
        <p className="text-[12px] text-slate-500">Only milestones backed by data are shown.</p>
        <ul className="mt-2 list-disc pl-4 text-[13px] text-slate-300">
          {milestones.map((m) => <li key={m.label}>{m.label}</li>)}
        </ul>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">Campaigns</h2>
        <Button className="mt-2" size="sm" onClick={() => addCampaign({ id: createId("camp"), ...timestamps(), name: "New campaign", startDate: new Date().toISOString().slice(0, 10), targetRoleIds: [], targetCompanyIds: [], weeklyApplicationTarget: 6, weeklyNetworkingTarget: 4, resumeVariantIds: [], hypothesis: "", retrospective: "", status: "Active" })}>
          Add campaign
        </Button>
        {state.campaigns.filter((c) => !c.archivedAt).map((c) => (
          <div key={c.id} className="mt-3">
            <Input value={c.name} onChange={(e) => updateCampaign({ ...c, name: e.target.value })} />
            <Textarea className="mt-2" value={c.hypothesis} onChange={(e) => updateCampaign({ ...c, hypothesis: e.target.value })} placeholder="Hypothesis" />
          </div>
        ))}
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">CSV</h2>
        <div className="mt-2 flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={() => downloadText("jobs.csv", exportJobsCsv(state), "text/csv")}>Export jobs</Button>
          <Button size="sm" variant="outline" onClick={() => downloadText("contacts.csv", exportContactsCsv(state), "text/csv")}>Export contacts</Button>
          <Button size="sm" variant="outline" onClick={() => downloadText("skills.csv", exportSkillsCsv(state), "text/csv")}>Export skills</Button>
          <Button size="sm" variant="outline" onClick={() => downloadText("projects.csv", exportProjectsCsv(state), "text/csv")}>Export projects</Button>
        </div>
        <Field label="Import job applications CSV" className="mt-3">
          <Textarea rows={5} value={csv} placeholder="company,role,platform,status,dateApplied" onChange={(e) => setCsv(e.target.value)} />
        </Field>
        {preview.length > 0 ? (
          <div className="mt-2 text-[12px] text-slate-400">
            {preview.filter((r) => r.kind === "new").length} new · {preview.filter((r) => r.kind === "update").length} duplicates/updates · {preview.filter((r) => r.kind === "invalid").length} invalid
            <Button
              className="ml-2"
              size="sm"
              onClick={() => {
                rowsToApplications(preview, state.applications).forEach(addApplication);
                toast.success("CSV imported");
                setCsv("");
              }}
            >
              Import valid rows
            </Button>
          </div>
        ) : null}
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">Diagnostics</h2>
        <Button
          className="mt-2"
          size="sm"
          variant="outline"
          onClick={() => {
            const include = confirm("Include career records in the diagnostic file? Cancel for metadata only.");
            downloadText("ai-career-os-diagnostic.json", diagnosticExport(include, { state }));
          }}
        >
          Export diagnostic information
        </Button>
        <Button className="ml-2 mt-2" size="sm" variant="ghost" onClick={() => loadDemo()}>
          Load demo workspace
        </Button>
      </section>
    </div>
  );
}
