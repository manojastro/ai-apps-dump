"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { formatDate } from "@/lib/dates";
import { createId, nowIso, timestamps } from "@/lib/ids";
import { jdCoverage, opportunityFit } from "@/lib/opportunity-fit";
import { applicationQualityValue } from "@/lib/scoring";
import { maskText } from "@/lib/currency";
import { useCareerStore } from "@/store/career-store";
import type { ApplicationStatus, JobApplication, RoundOutcome } from "@/types/career";
import { nextReviewForConfidence, newQuestion, newTask } from "@/lib/factories";

export default function JobDetailPage() {
  const { jobId: id } = useParams<{ jobId: string }>();
  const state = useCareerStore((s) => s.state);
  const update = useCareerStore((s) => s.updateApplication);
  const addJd = useCareerStore((s) => s.addJobDescription);
  const addRound = useCareerStore((s) => s.addInterviewRound);
  const updateRound = useCareerStore((s) => s.updateInterviewRound);
  const addQ = useCareerStore((s) => s.addInterviewQuestion);
  const addTask = useCareerStore((s) => s.addTask);
  const job = state.applications.find((j) => j.id === id);
  if (!job) return <p className="text-slate-400">Job not found.</p>;

  const set = (patch: Partial<JobApplication>) => update({ ...job, ...patch });
  const privacy = state.ui.privacyMode;
  const jd = state.jobDescriptions.find((j) => j.applicationId === job.id);
  const fit = opportunityFit(state, job);
  const coverage = jdCoverage(state, job);
  const quality = applicationQualityValue(job, state);
  const rounds = state.interviewRounds.filter((r) => r.applicationId === job.id && !r.archivedAt).sort((a, b) => a.roundNumber - b.roundNumber);
  const resume = state.resumeVariants.find((r) => r.id === job.resumeVariantId);
  const company = state.targetCompanies.find((c) => c.id === job.companyId || c.name === job.company);
  const contacts = state.contacts.filter((c) => !c.archivedAt && c.company === job.company);

  const checklist = [
    { ok: Boolean(jd?.rawText || job.jdCaptured), label: "JD saved" },
    { ok: Boolean(fit.label), label: "Role fit reviewed" },
    { ok: Boolean(job.resumeVariantId), label: "Resume selected" },
    { ok: Boolean(job.evidenceReviewed), label: "Projects / evidence mapped" },
    { ok: Boolean(job.referralAttempted || job.referralContactId), label: "Referral checked" },
    { ok: Boolean(job.nextFollowUpDate), label: "Follow-up date set" },
  ];

  return (
    <div className="space-y-4">
      <Link href="/jobs" className="text-[12px] text-slate-500">← Jobs</Link>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold">{job.company} · {job.role}</h1>
          <div className="mt-2 flex flex-wrap gap-2">
            <StatusBadge value={job.status} />
            <Badge tone="indigo">{fit.label}</Badge>
            <Badge>Quality {Math.round(quality)}</Badge>
          </div>
        </div>
        <Select value={job.status} onChange={(e) => set({ status: e.target.value as ApplicationStatus })}>
          {["Identified", "Referred", "Applied", "Screening", "Technical", "Offer", "Rejected"].map((s) => <option key={s}>{s}</option>)}
        </Select>
      </div>

      {job.status === "Identified" ? (
        <section className="card p-4">
          <h2 className="text-sm font-semibold">Application preparation</h2>
          <p className="mt-1 text-[12px] text-slate-500">Optional — does not block moving to Applied.</p>
          <ul className="mt-2 space-y-1 text-[13px]">
            {checklist.map((c) => (
              <li key={c.label}>{c.ok ? "✓" : "□"} {c.label}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <div className="grid gap-3 md:grid-cols-2">
        <Field label="Platform"><Input value={job.platform} onChange={(e) => set({ platform: e.target.value })} /></Field>
        <Field label="Job URL"><Input value={job.jobUrl ?? ""} onChange={(e) => set({ jobUrl: e.target.value })} /></Field>
        <Field label="Location"><Input value={job.location ?? ""} onChange={(e) => set({ location: e.target.value })} /></Field>
        <Field label="Compensation text"><Input value={privacy ? "••••" : job.compensationText ?? ""} onChange={(e) => set({ compensationText: e.target.value })} /></Field>
        <Field label="Date applied"><Input type="date" value={job.dateApplied.slice(0, 10)} onChange={(e) => set({ dateApplied: e.target.value })} /></Field>
        <Field label="Next follow-up"><Input type="date" value={job.nextFollowUpDate.slice(0, 10)} onChange={(e) => set({ nextFollowUpDate: e.target.value })} /></Field>
        <Field label="Resume">
          <Select value={job.resumeVariantId ?? ""} onChange={(e) => set({ resumeVariantId: e.target.value || undefined })}>
            <option value="">—</option>
            {state.resumeVariants.filter((r) => !r.archivedAt).map((r) => <option key={r.id} value={r.id}>{r.name} {r.versionLabel}</option>)}
          </Select>
        </Field>
        <Field label="Referral">
          <Input value={maskText(job.referralContact, privacy, "name")} onChange={(e) => set({ referralContact: e.target.value, referralAttempted: true })} />
        </Field>
        <Field label="Notes" className="md:col-span-2">
          <Textarea value={privacy ? "Private note hidden" : job.notes} onChange={(e) => set({ notes: e.target.value })} />
        </Field>
        {job.status === "Rejected" ? (
          <Field label="Outcome reason (never inferred)">
            <Select value={job.outcomeReason ?? "Unknown"} onChange={(e) => set({ outcomeReason: e.target.value as JobApplication["outcomeReason"] })}>
              {["No Response","Role Closed","Skill Gap","Experience Mismatch","Compensation","Location","Failed Interview","Candidate Withdrew","Accepted Another Offer","Unknown","Other"].map((r) => <option key={r}>{r}</option>)}
            </Select>
          </Field>
        ) : null}
      </div>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">Opportunity fit</h2>
        <p className="mt-1 text-[13px] text-slate-300">{fit.label} · score {fit.score}</p>
        <ul className="mt-2 list-disc pl-4 text-[13px] text-slate-400">
          {fit.reasons.map((r) => <li key={r}>{r}</li>)}
          {fit.constraints.map((r) => <li key={r} className="text-amber-300">{r}</li>)}
        </ul>
        <p className="mt-2 text-[12px] text-slate-500">Constraint conflict is not an auto-reject.</p>
      </section>

      <section className="card p-4">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-semibold">JD snapshot</h2>
          <Button size="sm" variant="outline" onClick={() => addJd({ id: createId("jd"), ...timestamps(), applicationId: job.id, capturedAt: nowIso(), rawText: "", requiredSkills: [], preferredSkills: [], responsibilities: [], notes: "" })}>
            {jd ? "New version" : "Paste JD"}
          </Button>
        </div>
        {jd ? (
          <div className="grid gap-3">
            <Textarea
              value={jd.rawText}
              onChange={(e) => {
                const raw = e.target.value;
                const requiredSkills = raw.split(/[,\n]/).map((s) => s.trim()).filter((s) => s.length > 2 && s.length < 24).slice(0, 8);
                addJd({ ...jd, rawText: raw, requiredSkills, capturedAt: nowIso() });
                set({ jdCaptured: true });
              }}
            />
            <Input placeholder="Required skills, comma-separated" value={jd.requiredSkills.join(", ")} onChange={(e) => addJd({ ...jd, requiredSkills: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })} />
          </div>
        ) : <p className="text-[13px] text-slate-500">Paste a JD. No scraping.</p>}
        {coverage.length > 0 ? (
          <table className="mt-3 w-full text-left text-[13px]">
            <thead className="text-[11px] text-slate-500"><tr><th className="py-1">Requirement</th><th>Coverage</th></tr></thead>
            <tbody>
              {coverage.map((c) => (
                <tr key={c.requirement} className="border-t border-white/5">
                  <td className="py-1">{c.requirement}</td>
                  <td>{c.coverage}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
        <p className="mt-2 text-[11px] text-slate-500">This is evidence coverage, not an ATS score.</p>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">Timeline</h2>
        <ol className="mt-2 space-y-1 text-[13px] text-slate-300">
          <li>{formatDate(job.createdAt)} Identified</li>
          {job.status !== "Identified" ? <li>{formatDate(job.dateApplied)} {job.status === "Referred" ? "Referred" : "Applied / progressed"}</li> : null}
          {rounds.map((r) => (
            <li key={r.id}>{formatDate(r.scheduledAt ?? r.createdAt)} {r.type} · {r.outcome}</li>
          ))}
        </ol>
      </section>

      <section className="card p-4">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-semibold">Interview rounds</h2>
          <Button size="sm" onClick={() => addRound({ id: createId("ir"), ...timestamps(), applicationId: job.id, roundNumber: rounds.length + 1, type: "Technical", outcome: "Upcoming", questionsAsked: [], strongAreas: [], weakAreas: [], notes: "" })}>
            Add round
          </Button>
        </div>
        {rounds.map((r) => (
          <div key={r.id} className="card-2 mb-3 p-3">
            <div className="flex flex-wrap gap-2">
              <span className="text-[13px] font-medium">Round {r.roundNumber} · {r.type}</span>
              <Select value={r.outcome} onChange={(e) => updateRound({ ...r, outcome: e.target.value as RoundOutcome })}>
                {["Upcoming", "Passed", "Failed", "Pending", "Cancelled"].map((o) => <option key={o}>{o}</option>)}
              </Select>
            </div>
            <div className="mt-2 grid gap-2 md:grid-cols-2">
              <Field label="Scheduled"><Input type="datetime-local" value={r.scheduledAt?.slice(0, 16) ?? ""} onChange={(e) => updateRound({ ...r, scheduledAt: e.target.value })} /></Field>
              <Field label="Interviewer"><Input value={privacy ? "Hidden" : r.interviewerName ?? ""} onChange={(e) => updateRound({ ...r, interviewerName: e.target.value })} /></Field>
              <Field label="What went well"><Textarea value={r.wentWell ?? ""} onChange={(e) => updateRound({ ...r, wentWell: e.target.value })} /></Field>
              <Field label="What was difficult"><Textarea value={r.difficult ?? ""} onChange={(e) => updateRound({ ...r, difficult: e.target.value })} /></Field>
              <Field label="What exposed a gap"><Textarea value={r.exposedGap ?? ""} onChange={(e) => updateRound({ ...r, exposedGap: e.target.value })} /></Field>
              <Field label="What should be revised"><Textarea value={r.shouldRevise ?? ""} onChange={(e) => updateRound({ ...r, shouldRevise: e.target.value })} /></Field>
            </div>
            {r.exposedGap ? (
              <div className="mt-2 flex flex-wrap gap-2">
                <Button size="sm" variant="outline" onClick={() => addQ(newQuestion({ question: r.exposedGap, category: "Agents", nextReviewDate: nextReviewForConfidence(2) }))}>Convert to question</Button>
                <Button size="sm" variant="outline" onClick={() => addTask(newTask({ title: `Close gap: ${r.exposedGap}`, category: "Interview", linkedEntityId: job.id }))}>Convert to task</Button>
              </div>
            ) : null}
          </div>
        ))}
      </section>

      {["Screening", "Technical"].includes(job.status) ? (
        <section className="card p-4">
          <h2 className="text-sm font-semibold">Company interview packet</h2>
          <p className="mt-1 text-[13px] text-slate-400">Assembled from stored data only.</p>
          <ul className="mt-2 list-disc pl-4 text-[13px] text-slate-300">
            <li>{job.company} · {job.role}</li>
            <li>Resume: {resume?.name ?? "not selected"}</li>
            <li>Company priority: {company?.priority ?? "unlisted"}</li>
            <li>Contacts: {contacts.map((c) => (privacy ? "Hidden" : c.name)).join(", ") || "none"}</li>
            <li>STAR stories: {state.starStories.filter((s) => !s.archivedAt).length}</li>
            <li>Projects: {state.projects.filter((p) => !p.archivedAt && p.status !== "planned").map((p) => p.title).join("; ") || "none deployed"}</li>
          </ul>
        </section>
      ) : null}
    </div>
  );
}
