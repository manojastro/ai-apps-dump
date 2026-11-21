"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Input, Select } from "@/components/ui/field";
import { SectionHeader } from "@/components/shared/empty-state";
import { newCert } from "@/lib/factories";
import { active } from "@/lib/utils";
import { useCareerStore } from "@/store/career-store";
import type { CertificationItem } from "@/types/career";

const TRACKS = ["Option A: Azure Enterprise", "Option B: Cloud-Agnostic AWS", "Option C: Agentic Specialist"] as const;

export default function CertificationsPage() {
  const state = useCareerStore((s) => s.state);
  const add = useCareerStore((s) => s.addCertification);
  const update = useCareerStore((s) => s.updateCertification);
  const items = active(state.certifications);

  return (
    <div>
      <SectionHeader
        title="Certification Roadmap"
        description="Certificates are a modest readiness signal. They must not dominate project and evidence scoring."
        actions={<Button onClick={() => add(newCert({ name: "New certification" }))}>Add</Button>}
      />
      <div className="grid gap-4 md:grid-cols-3">
        {TRACKS.map((track) => (
          <section key={track} className="card p-4">
            <h2 className="text-sm font-semibold">{track}</h2>
            {items.filter((c) => c.mappedTrack === track).map((c) => (
              <div key={c.id} className="mt-3 space-y-2 border-t border-white/5 pt-3">
                <Field label="Name"><Input value={c.name} onChange={(e) => update({ ...c, name: e.target.value })} /></Field>
                <Field label="Code"><Input value={c.code} onChange={(e) => update({ ...c, code: e.target.value })} /></Field>
                <Field label="Status">
                  <Select value={c.status} onChange={(e) => update({ ...c, status: e.target.value as CertificationItem["status"] })}>
                    {["Not Started", "Studying", "Scheduled", "Certified"].map((s) => <option key={s}>{s}</option>)}
                  </Select>
                </Field>
                <Badge>{c.provider}</Badge>
              </div>
            ))}
          </section>
        ))}
      </div>
    </div>
  );
}
