"use client";

import Link from "next/link";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState, SectionHeader } from "@/components/shared/empty-state";
import { newCompany } from "@/lib/factories";
import { active } from "@/lib/utils";
import { useCareerStore } from "@/store/career-store";

export default function CompaniesPage() {
  const state = useCareerStore((s) => s.state);
  const add = useCareerStore((s) => s.addTargetCompany);
  const companies = active(state.targetCompanies);
  const [q, setQ] = useState("");
  const filtered = companies.filter((c) => c.name.toLowerCase().includes(q.toLowerCase()));

  return (
    <div>
      <SectionHeader
        title="Target Companies"
        description="Company CRM: priority, roles, applications, contacts, referrals."
        actions={
          <Button
            onClick={() => {
              const c = newCompany({ name: "New target company" });
              add(c);
            }}
          >
            Add Company
          </Button>
        }
      />
      <input className="mb-4 h-9 w-full max-w-sm rounded-lg border border-white/10 bg-[#0d1320] px-3 text-[13px]" placeholder="Search companies" value={q} onChange={(e) => setQ(e.target.value)} />
      {filtered.length === 0 ? <EmptyState title="No companies" detail="Add GCCs, product companies, and AI startups you actually want." /> : (
        <div className="grid gap-3 md:grid-cols-2">
          {filtered.map((c) => {
            const apps = state.applications.filter((a) => !a.archivedAt && (a.companyId === c.id || a.company === c.name));
            const contacts = state.contacts.filter((x) => !x.archivedAt && x.company === c.name);
            return (
              <Link key={c.id} href={`/companies/${c.id}`} className="card p-4">
                <div className="flex items-center justify-between">
                  <p className="font-medium">{c.name}</p>
                  <Badge tone={c.priority === "Dream" ? "indigo" : "cyan"}>{c.priority}</Badge>
                </div>
                <p className="mt-1 text-[12px] text-slate-400">{c.tier} · {c.locations.join(", ")}</p>
                <p className="mt-2 text-[12px] text-slate-500">{apps.length} applications · {contacts.length} contacts</p>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
