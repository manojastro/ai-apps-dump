"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { SectionHeader } from "@/components/shared/empty-state";
import { createId, timestamps } from "@/lib/ids";
import { formatLpa } from "@/lib/currency";
import { active } from "@/lib/utils";
import { useCareerStore } from "@/store/career-store";
import type { CareerAsset } from "@/types/career";

export default function AssetsPage() {
  const state = useCareerStore((s) => s.state);
  const addResume = useCareerStore((s) => s.addResumeVariant);
  const updateResume = useCareerStore((s) => s.updateResumeVariant);
  const addAsset = useCareerStore((s) => s.addAsset);
  const updateAsset = useCareerStore((s) => s.updateAsset);
  const addAch = useCareerStore((s) => s.addAchievement);
  const addOffer = useCareerStore((s) => s.addOffer);
  const updateOffer = useCareerStore((s) => s.updateOffer);
  const addNeg = useCareerStore((s) => s.addNegotiation);
  const addBullet = useCareerStore((s) => s.addResumeBullet);
  const privacy = state.ui.privacyMode;
  const [tab, setTab] = useState<"assets" | "resumes" | "pack" | "offers">("assets");

  const packMd = useMemo(() => {
    const projects = active(state.projects).filter((p) => p.status === "deployed" || p.maturity === "Production Grade" || p.maturity === "Portfolio Ready");
    const skills = active(state.skills).filter((s) => s.status !== "to_learn").map((s) => s.name);
    const n = active(state.transitionNarratives)[0];
    return [
      `# ${n?.intro30s || "AI Engineer — Agentic / GenAI / AIOps"}`,
      "",
      n?.story90s ?? "",
      "",
      "## Skills",
      skills.join(", "),
      "",
      "## Projects",
      ...projects.map((p) => `- ${p.title} — ${p.starPitch || p.useCase} ${p.githubUrl}`),
      "",
      "## Achievements",
      ...active(state.achievements).map((a) => `- ${a.title}: ${a.result}`),
    ].join("\n");
  }, [state]);

  return (
    <div>
      <SectionHeader title="Career Assets" description="Resumes, public profiles, recruiter pack. Private pipeline data stays out of the pack." />
      <div className="mb-4 flex gap-1">
        {(["assets", "resumes", "pack", "offers"] as const).map((t) => (
          <button key={t} type="button" className={`rounded-md px-3 py-1.5 text-[13px] ${tab === t ? "bg-white/10" : "text-slate-400"}`} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>

      {tab === "assets" ? (
        <div className="space-y-3">
          <Button size="sm" onClick={() => addAsset({ id: createId("as"), ...timestamps(), kind: "GitHub", title: "GitHub", targetRoleIds: [], status: "Draft", completeness: 40, notes: "" })}>Add asset</Button>
          {active(state.careerAssets).map((a) => (
            <div key={a.id} className="card grid gap-2 p-3 md:grid-cols-4">
              <Input value={a.title} onChange={(e) => updateAsset({ ...a, title: e.target.value })} />
              <Select value={a.status} onChange={(e) => updateAsset({ ...a, status: e.target.value as CareerAsset["status"] })}>
                {["Draft", "Review", "Ready"].map((s) => <option key={s}>{s}</option>)}
              </Select>
              <Input value={a.url ?? ""} onChange={(e) => updateAsset({ ...a, url: e.target.value })} placeholder="URL" />
              <Input type="number" value={a.completeness} onChange={(e) => updateAsset({ ...a, completeness: Number(e.target.value) })} />
            </div>
          ))}
          <section className="card p-4">
            <h2 className="text-sm font-semibold">Achievement bank</h2>
            <Button className="mt-2" size="sm" variant="outline" onClick={() => addAch({ id: createId("ach"), ...timestamps(), title: "Achievement", context: "", action: "", result: "", technologies: [], transferableCompetencies: [], mappedRoleIds: [], quantified: false })}>
              Add achievement
            </Button>
            {active(state.achievements).map((a) => (
              <p key={a.id} className="mt-2 text-[13px] text-slate-300">{a.title} — {a.result}</p>
            ))}
          </section>
        </div>
      ) : null}

      {tab === "resumes" ? (
        <div className="space-y-3">
          <Button size="sm" onClick={() => addResume({ id: createId("cv"), ...timestamps(), name: "New resume", versionLabel: "v1", targetRoleIds: [], summary: "", selectedProjectIds: [], selectedEvidenceIds: [], notes: "", isActive: true })}>
            Add resume version
          </Button>
          {active(state.resumeVariants).map((r) => (
            <div key={r.id} className="card p-4">
              <div className="grid gap-2 md:grid-cols-3">
                <Field label="Name"><Input value={r.name} onChange={(e) => updateResume({ ...r, name: e.target.value })} /></Field>
                <Field label="Version"><Input value={r.versionLabel} onChange={(e) => updateResume({ ...r, versionLabel: e.target.value })} /></Field>
                <Field label="URL"><Input value={r.externalUrl ?? ""} onChange={(e) => updateResume({ ...r, externalUrl: e.target.value })} /></Field>
              </div>
              <Field label="Summary" className="mt-2"><Textarea value={r.summary} onChange={(e) => updateResume({ ...r, summary: e.target.value })} /></Field>
              <Button className="mt-2" size="sm" variant="outline" onClick={() => addBullet({ id: createId("rb"), ...timestamps(), text: "Evidence-backed bullet", mappedRoleIds: r.targetRoleIds, competencyIds: [], quantified: false, projectId: r.selectedProjectIds[0] })}>
                Add resume bullet
              </Button>
            </div>
          ))}
        </div>
      ) : null}

      {tab === "pack" ? (
        <div className="card p-4">
          <div className="mb-3 flex gap-2 no-print">
            <Button size="sm" onClick={() => void navigator.clipboard.writeText(packMd)}>Copy Markdown</Button>
            <Button size="sm" variant="outline" onClick={() => window.print()}>Printable view</Button>
          </div>
          <pre className="whitespace-pre-wrap text-[13px] text-slate-200">{packMd}</pre>
        </div>
      ) : null}

      {tab === "offers" ? (
        <div className="space-y-3">
          <Button size="sm" onClick={() => addOffer({ id: createId("of"), ...timestamps(), applicationId: state.applications[0]?.id ?? "", roleTitle: "AI Engineer", company: "Company", aiRoleAlignment: 4, learningPotential: 4, roleScope: 3, notes: "" })}>
            Add offer
          </Button>
          {active(state.offers).map((o) => (
            <div key={o.id} className="card p-4">
              <div className="grid gap-2 md:grid-cols-3">
                <Field label="Company"><Input value={o.company} onChange={(e) => updateOffer({ ...o, company: e.target.value })} /></Field>
                <Field label="Fixed CTC LPA"><Input type="number" value={o.fixedCtc ?? ""} onChange={(e) => updateOffer({ ...o, fixedCtc: Number(e.target.value) })} /></Field>
                <Field label="First year"><Input type="number" value={o.totalFirstYear ?? ""} onChange={(e) => updateOffer({ ...o, totalFirstYear: Number(e.target.value) })} /></Field>
              </div>
              <p className="mt-2 text-[13px] text-slate-400">
                {formatLpa(o.fixedCtc, privacy)} · alignment {o.aiRoleAlignment}/5 · learning {o.learningPotential}/5 · scope {o.roleScope}/5
              </p>
              <Button className="mt-2" size="sm" variant="outline" onClick={() => addNeg({ id: createId("neg"), ...timestamps(), offerId: o.id, notes: "Initial conversation", decision: "Pending" })}>
                Log negotiation
              </Button>
            </div>
          ))}
          {state.offers.length >= 2 ? (
            <p className="text-[13px] text-slate-400">
              Compare using your weights: alignment {state.settings.offerWeightAlignment}% · comp {state.settings.offerWeightComp}% · learning {state.settings.offerWeightLearning}% · scope {state.settings.offerWeightScope}% · location {state.settings.offerWeightLocation}%. The OS does not pick for you.
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
