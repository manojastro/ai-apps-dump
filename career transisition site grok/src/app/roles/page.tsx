"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { SectionHeader } from "@/components/shared/empty-state";
import { ProgressBar } from "@/components/shared/metric-card";
import { allRoleReadiness } from "@/lib/role-readiness";
import { useCareerStore } from "@/store/career-store";

export default function RolesPage() {
  const state = useCareerStore((s) => s.state);
  const roles = allRoleReadiness(state);
  return (
    <div>
      <SectionHeader title="Target Roles" description="Role readiness uses competencies → skills + research + project evidence + interview evidence. Not string matching alone." />
      <div className="grid gap-3 md:grid-cols-2">
        {roles.map((r) => (
          <Link key={r.role.id} href={`/roles/${r.role.id}`} className="card p-4">
            <div className="flex items-center justify-between">
              <p className="font-medium">{r.role.name}</p>
              <Badge tone={r.role.priority === "Primary" ? "cyan" : "slate"}>{r.role.priority}</Badge>
            </div>
            <p className="mt-1 text-[12px] text-slate-400">{r.role.targetSeniority} · {r.role.active ? "Active" : "Inactive"}</p>
            <div className="mt-3"><ProgressBar value={r.score} label="Readiness" /></div>
            <p className="mt-2 text-[12px] text-slate-500">
              Strong {r.strong.length} · Partial {r.partial.length} · Gap {r.missing.length} · Evidence missing {r.evidenceMissing.length}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
