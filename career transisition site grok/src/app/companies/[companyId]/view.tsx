"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { useCareerStore } from "@/store/career-store";
import type { TargetCompany } from "@/types/career";

export default function CompanyDetailPage() {
  const { companyId: id } = useParams<{ companyId: string }>();
  const state = useCareerStore((s) => s.state);
  const update = useCareerStore((s) => s.updateTargetCompany);
  const archive = useCareerStore((s) => s.archiveTargetCompany);
  const company = state.targetCompanies.find((c) => c.id === id);
  if (!company) return <p className="text-slate-400">Company not found.</p>;
  const set = (patch: Partial<TargetCompany>) => update({ ...company, ...patch });
  const apps = state.applications.filter((a) => !a.archivedAt && (a.companyId === company.id || a.company === company.name));
  const contacts = state.contacts.filter((c) => !c.archivedAt && c.company === company.name);
  const rounds = state.interviewRounds.filter((r) => apps.some((a) => a.id === r.applicationId));

  return (
    <div className="space-y-4">
      <Link href="/companies" className="text-[12px] text-slate-500">← Companies</Link>
      <h1 className="text-lg font-semibold">{company.name}</h1>
      <div className="grid gap-3 md:grid-cols-2">
        <Field label="Name"><Input value={company.name} onChange={(e) => set({ name: e.target.value })} /></Field>
        <Field label="Priority">
          <Select value={company.priority} onChange={(e) => set({ priority: e.target.value as TargetCompany["priority"] })}>
            {["Dream", "High", "Medium", "Watch"].map((p) => <option key={p}>{p}</option>)}
          </Select>
        </Field>
        <Field label="Tier">
          <Select value={company.tier} onChange={(e) => set({ tier: e.target.value as TargetCompany["tier"] })}>
            {["GCC", "Enterprise IT", "AI Startup", "Consulting", "Product"].map((p) => <option key={p}>{p}</option>)}
          </Select>
        </Field>
        <Field label="Career URL"><Input value={company.careerUrl ?? ""} onChange={(e) => set({ careerUrl: e.target.value })} /></Field>
        <Field label="Locations (comma)" className="md:col-span-2">
          <Input value={company.locations.join(", ")} onChange={(e) => set({ locations: e.target.value.split(",").map((x) => x.trim()).filter(Boolean) })} />
        </Field>
        <Field label="Why target" className="md:col-span-2"><Textarea value={company.whyTarget} onChange={(e) => set({ whyTarget: e.target.value })} /></Field>
        <Field label="Notes" className="md:col-span-2"><Textarea value={company.notes} onChange={(e) => set({ notes: e.target.value })} /></Field>
      </div>
      <section className="card p-4 text-[13px]">
        <h2 className="font-semibold">Applications</h2>
        {apps.map((a) => (
          <Link key={a.id} href={`/jobs/${a.id}`} className="mt-1 block text-cyan-300">{a.role} · {a.status}</Link>
        ))}
        <h2 className="mt-4 font-semibold">Contacts</h2>
        {contacts.map((c) => (
          <Link key={c.id} href={`/contacts/${c.id}`} className="mt-1 block text-cyan-300">{c.name} · {c.status}</Link>
        ))}
        <h2 className="mt-4 font-semibold">Interview history</h2>
        {rounds.map((r) => (
          <p key={r.id} className="mt-1 text-slate-400">Round {r.roundNumber} {r.type} · {r.outcome}</p>
        ))}
      </section>
      <Button variant="ghost" onClick={() => archive(company.id)}>Archive</Button>
    </div>
  );
}
