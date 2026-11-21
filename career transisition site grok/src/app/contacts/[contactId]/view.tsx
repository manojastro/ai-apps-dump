"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { createId, timestamps } from "@/lib/ids";
import { maskText } from "@/lib/currency";
import { useCareerStore } from "@/store/career-store";
import type { NetworkingContact } from "@/types/career";

export default function ContactDetailPage() {
  const { contactId: id } = useParams<{ contactId: string }>();
  const state = useCareerStore((s) => s.state);
  const update = useCareerStore((s) => s.updateContact);
  const archive = useCareerStore((s) => s.archiveContact);
  const addIx = useCareerStore((s) => s.addNetworkingInteraction);
  const contact = state.contacts.find((c) => c.id === id);
  if (!contact) return <p className="text-slate-400">Contact not found.</p>;
  const privacy = state.ui.privacyMode;
  const set = (patch: Partial<NetworkingContact>) => update({ ...contact, ...patch });
  const history = state.networkingInteractions.filter((i) => i.contactId === contact.id && !i.archivedAt).sort((a, b) => b.date.localeCompare(a.date));

  return (
    <div className="space-y-4">
      <Link href="/network" className="text-[12px] text-slate-500">← Network</Link>
      <h1 className="text-lg font-semibold">{privacy ? "Name hidden" : contact.name}</h1>
      <div className="grid gap-3 md:grid-cols-2">
        <Field label="Name"><Input value={privacy ? "Hidden" : contact.name} onChange={(e) => set({ name: e.target.value })} /></Field>
        <Field label="Designation"><Input value={contact.designation} onChange={(e) => set({ designation: e.target.value })} /></Field>
        <Field label="Company"><Input value={contact.company} onChange={(e) => set({ company: e.target.value })} /></Field>
        <Field label="Medium">
          <Select value={contact.medium} onChange={(e) => set({ medium: e.target.value as NetworkingContact["medium"] })}>
            {["LinkedIn", "Topmate", "Hackathon", "Email", "In-Person"].map((m) => <option key={m}>{m}</option>)}
          </Select>
        </Field>
        <Field label="Status">
          <Select value={contact.status} onChange={(e) => set({ status: e.target.value as NetworkingContact["status"] })}>
            {["Reached Out", "Connected", "Call Scheduled", "Mentorship Active"].map((m) => <option key={m}>{m}</option>)}
          </Select>
        </Field>
        <Field label="Helpful">
          <Select value={contact.helpfulRating} onChange={(e) => set({ helpfulRating: e.target.value as NetworkingContact["helpfulRating"] })}>
            {["High", "Medium", "Low", "Unresponsive"].map((m) => <option key={m}>{m}</option>)}
          </Select>
        </Field>
        <Field label="Email"><Input value={maskText(contact.email, privacy, "contact")} onChange={(e) => set({ email: e.target.value })} /></Field>
        <Field label="Next touchpoint"><Input type="date" value={contact.nextTouchpointDate ?? ""} onChange={(e) => set({ nextTouchpointDate: e.target.value })} /></Field>
        <Field label="Key takeaway" className="md:col-span-2"><Textarea value={contact.keyTakeaway} onChange={(e) => set({ keyTakeaway: e.target.value })} /></Field>
      </div>
      <section className="card p-4">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-semibold">Interaction history</h2>
          <Button size="sm" onClick={() => addIx({ id: createId("ix"), ...timestamps(), contactId: contact.id, date: new Date().toISOString().slice(0, 10), type: "Follow-Up", summary: "Follow-up" })}>
            Log interaction
          </Button>
        </div>
        {history.map((i) => (
          <p key={i.id} className="text-[13px] text-slate-300">
            {i.date} · {i.type} — {i.summary}
          </p>
        ))}
      </section>
      <Button variant="ghost" onClick={() => archive(contact.id)}>Archive</Button>
    </div>
  );
}
