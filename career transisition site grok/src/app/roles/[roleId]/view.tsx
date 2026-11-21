"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Select, Textarea } from "@/components/ui/field";
import { ProgressBar } from "@/components/shared/metric-card";
import { analyzeRole } from "@/lib/role-readiness";
import { useCareerStore } from "@/store/career-store";
import type { TargetRoleProfile } from "@/types/career";

export default function RoleDetailPage() {
  const { roleId: id } = useParams<{ roleId: string }>();
  const state = useCareerStore((s) => s.state);
  const updateRole = useCareerStore((s) => s.updateRole);
  const role = state.targetRoles.find((r) => r.id === id);
  if (!role) return <p className="text-slate-400">Role not found.</p>;
  const analysis = analyzeRole(state, role);

  const groups = [
    { title: "Strong", items: analysis.strong, tone: "green" as const },
    { title: "Partial", items: analysis.partial, tone: "cyan" as const },
    { title: "Gap", items: analysis.missing, tone: "red" as const },
    { title: "Evidence Missing", items: analysis.evidenceMissing, tone: "amber" as const },
  ];

  return (
    <div className="space-y-4">
      <Link href="/roles" className="text-[12px] text-slate-500">← Roles</Link>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold">{role.name}</h1>
          <p className="text-[13px] text-slate-400">{role.notes}</p>
        </div>
        <Badge tone="indigo">{analysis.score}%</Badge>
      </div>
      <ProgressBar value={analysis.score} label="Role readiness" />
      <div className="grid gap-3 md:grid-cols-2">
        <Field label="Priority">
          <Select value={role.priority} onChange={(e) => updateRole({ ...role, priority: e.target.value as TargetRoleProfile["priority"] })}>
            {["Primary", "Secondary", "Stretch", "Parked"].map((p) => <option key={p}>{p}</option>)}
          </Select>
        </Field>
        <Field label="Seniority">
          <Select value={role.targetSeniority} onChange={(e) => updateRole({ ...role, targetSeniority: e.target.value as TargetRoleProfile["targetSeniority"] })}>
            {["Mid", "Senior", "Lead", "Architect"].map((p) => <option key={p}>{p}</option>)}
          </Select>
        </Field>
        <Field label="Notes" className="md:col-span-2">
          <Textarea value={role.notes} onChange={(e) => updateRole({ ...role, notes: e.target.value })} />
        </Field>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {groups.map((g) => (
          <section key={g.title} className="card p-4">
            <h2 className="text-sm font-semibold">{g.title}</h2>
            {g.items.length === 0 ? <p className="mt-2 text-[13px] text-slate-500">None</p> : null}
            {g.items.map((item) => (
              <div key={item.competency.id} className="mt-3 border-t border-white/5 pt-3">
                <div className="flex items-center justify-between">
                  <p className="text-[13px] font-medium">{item.competency.name}</p>
                  <Badge tone={g.tone}>{item.coverage}</Badge>
                </div>
                <p className="mt-1 text-[12px] text-slate-400">
                  Capability {Math.round(item.capability * 100)} · Evidence {Math.round(item.evidence * 100)}
                </p>
                <p className="mt-1 text-[12px] text-cyan-200">Next: {item.nextAction}</p>
              </div>
            ))}
          </section>
        ))}
      </div>
      <Button variant="outline" onClick={() => updateRole({ ...role, active: !role.active })}>
        {role.active ? "Deactivate" : "Activate"}
      </Button>
    </div>
  );
}
