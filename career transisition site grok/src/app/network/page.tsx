"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState, SectionHeader } from "@/components/shared/empty-state";
import { isOverdue, isDueToday } from "@/lib/dates";
import { newContact } from "@/lib/factories";
import { active } from "@/lib/utils";
import { useCareerStore } from "@/store/career-store";

export default function NetworkPage() {
  const state = useCareerStore((s) => s.state);
  const add = useCareerStore((s) => s.addContact);
  const privacy = state.ui.privacyMode;
  const contacts = active(state.contacts);
  const interactions = active(state.networkingInteractions);
  const outreach = contacts.length;
  const connected = contacts.filter((c) => c.status !== "Reached Out").length;
  const calls = interactions.filter((i) => i.type === "Call" || i.type === "Meeting").length;
  const referrals = interactions.filter((i) => i.type === "Referral").length;
  const mentors = contacts.filter((c) => c.status === "Mentorship Active").length;

  const due = contacts.filter((c) => c.nextTouchpointDate && (isDueToday(c.nextTouchpointDate) || isOverdue(c.nextTouchpointDate)));

  return (
    <div>
      <SectionHeader
        title="Networking CRM"
        description="Relationship history, not a contact dump."
        actions={<Button onClick={() => add(newContact({ name: "New contact" }))}>Add Contact</Button>}
      />
      <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-5">
        {[
          ["Outreach", outreach],
          ["Connected", connected],
          ["Calls", calls],
          ["Referrals", referrals],
          ["Mentors", mentors],
        ].map(([k, v]) => (
          <div key={String(k)} className="card p-3">
            <p className="text-[11px] text-slate-500">{k}</p>
            <p className="tabular text-lg">{v as number}</p>
          </div>
        ))}
      </div>
      {due.length > 0 ? (
        <p className="mb-3 text-[13px] text-amber-300">{due.length} touchpoint(s) due or overdue.</p>
      ) : null}
      {contacts.length === 0 ? (
        <EmptyState title="No contacts" detail="Track people who can actually create interviews." />
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {contacts.map((c) => (
            <Link key={c.id} href={`/contacts/${c.id}`} className="card p-4">
              <div className="flex items-center justify-between">
                <p className="font-medium">{privacy ? "Name hidden" : c.name}</p>
                <Badge>{c.status}</Badge>
              </div>
              <p className="mt-1 text-[12px] text-slate-400">{c.designation} · {c.company}</p>
              {c.nextTouchpointDate && isOverdue(c.nextTouchpointDate) ? <Badge tone="red">Overdue</Badge> : null}
              {c.nextTouchpointDate && isDueToday(c.nextTouchpointDate) ? <Badge tone="amber">Due today</Badge> : null}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
