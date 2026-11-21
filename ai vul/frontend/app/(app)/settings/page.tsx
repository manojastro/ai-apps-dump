"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Save } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { StatusBadge } from "@/components/badges";
import { ErrorState, KeyValue, LoadingState, PageHeader } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useCan } from "@/hooks/use-me";
import { api } from "@/lib/api";
import { fmtRelative } from "@/lib/format";

interface Policy {
  version: number;
  weights: Record<string, number>;
  epss_bands: { min_probability: number; points_fraction: number }[];
  criticality_fractions: Record<string, number>;
  level_thresholds: Record<string, number>;
  priority_by_level: Record<string, string>;
  sla_days: Record<string, number>;
  missing_factor_assumption: number;
  min_coverage_for_auto_routing: number;
  policy_version: string;
}
interface SettingsData { risk_policy: Policy; environment: Record<string, unknown>; roles: Record<string, string[]> }
interface UserRow { id: string; email: string; full_name: string; role: string; is_active: boolean; last_login_at: string | null }

function PolicyEditor({ policy, canEdit }: { policy: Policy; canEdit: boolean }) {
  const qc = useQueryClient();
  const [weights, setWeights] = useState(policy.weights);
  const [thresholds, setThresholds] = useState(policy.level_thresholds);
  const [missing, setMissing] = useState(policy.missing_factor_assumption);
  const total = Object.values(weights).reduce((a, b) => a + b, 0);
  const save = useMutation({
    mutationFn: () => {
      const { policy_version: _ignored, ...rest } = policy;
      void _ignored;
      return api.put<Policy>("/settings/risk-policy", { ...rest, weights, level_thresholds: thresholds, missing_factor_assumption: missing });
    },
    onSuccess: (p) => { toast.success(`Risk policy v${p.version} saved`, { description: "New assessments use the new version; existing ones keep their recorded version." }); qc.invalidateQueries(); },
    onError: (e: Error) => toast.error("Policy rejected", { description: e.message }),
  });
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-5">
        {Object.entries(weights).map(([k, v]) => (
          <div key={k} className="space-y-1">
            <Label htmlFor={`w-${k}`} className="text-xs capitalize">{k.replaceAll("_", " ")}</Label>
            <Input id={`w-${k}`} type="number" min={0} max={100} value={v} disabled={!canEdit} onChange={(e) => setWeights({ ...weights, [k]: Number(e.target.value) })} />
          </div>
        ))}
      </div>
      <p className={`text-xs ${total === 100 ? "text-muted-foreground" : "text-risk-critical"}`}>Weights total {total} / 100</p>
      <div className="grid gap-3 sm:grid-cols-4">
        {Object.entries(thresholds).map(([k, v]) => (
          <div key={k} className="space-y-1">
            <Label htmlFor={`t-${k}`} className="text-xs capitalize">{k} threshold ≥</Label>
            <Input id={`t-${k}`} type="number" min={0} max={100} value={v} disabled={!canEdit} onChange={(e) => setThresholds({ ...thresholds, [k]: Number(e.target.value) })} />
          </div>
        ))}
        <div className="space-y-1">
          <Label htmlFor="missing" className="text-xs">Missing-factor assumption</Label>
          <Input id="missing" type="number" step={0.05} min={0} max={1} value={missing} disabled={!canEdit} onChange={(e) => setMissing(Number(e.target.value))} />
        </div>
      </div>
      <KeyValue cols={3} items={[
        ["EPSS bands", policy.epss_bands.map((b) => `≥${b.min_probability}: ${b.points_fraction * 100}%`).join(" · ")],
        ["Criticality fractions", Object.entries(policy.criticality_fractions).map(([k, v]) => `${k} ${v}`).join(" · ")],
        ["SLA days", Object.entries(policy.sla_days).map(([k, v]) => `${k} ${v}d`).join(" · ")],
      ]} />
      <div className="flex items-center gap-3">
        <Button size="sm" disabled={!canEdit || total !== 100 || save.isPending} onClick={() => save.mutate()}><Save /> Save new policy version</Button>
        <span className="font-mono text-[11px] text-muted-foreground">{policy.policy_version}</span>
      </div>
      {!canEdit && <p className="text-xs text-muted-foreground">Only administrators can change the risk policy.</p>}
    </div>
  );
}

export default function SettingsPage() {
  const canEdit = useCan("settings:manage");
  const { data, error, isLoading, refetch } = useQuery({ queryKey: ["settings"], queryFn: () => api.get<SettingsData>("/settings") });
  const users = useQuery({ queryKey: ["users"], queryFn: () => api.get<UserRow[]>("/users") });
  return (
    <>
      <PageHeader title="Settings" description="Risk policy, runtime configuration and role permissions. Secrets are configured through environment variables and never displayed." />
      {isLoading && <LoadingState />}
      {error && <ErrorState error={error} onRetry={refetch} />}
      {data && (
        <div className="space-y-4">
          <Card className="gap-3">
            <CardHeader><CardTitle className="text-sm">Deterministic risk policy</CardTitle><CardDescription className="text-xs">A demonstration policy, not an industry standard. Changes are versioned and audited.</CardDescription></CardHeader>
            <CardContent><PolicyEditor key={data.risk_policy.policy_version} policy={data.risk_policy} canEdit={canEdit} /></CardContent>
          </Card>
          <Card className="gap-3">
            <CardHeader><CardTitle className="text-sm">Runtime configuration</CardTitle></CardHeader>
            <CardContent><KeyValue cols={3} items={Object.entries(data.environment).map(([k, v]) => [k.replaceAll("_", " "), String(v ?? "—")])} /></CardContent>
          </Card>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="gap-3">
              <CardHeader><CardTitle className="text-sm">Role permissions (enforced server-side)</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {Object.entries(data.roles).map(([role, perms]) => (
                  <div key={role}><div className="mb-1 text-xs font-semibold capitalize">{role}</div><div className="flex flex-wrap gap-1">{perms.map((p) => <code key={p} className="rounded bg-muted px-1.5 text-[10px]">{p}</code>)}</div></div>
                ))}
              </CardContent>
            </Card>
            <Card className="gap-3">
              <CardHeader><CardTitle className="text-sm">Users</CardTitle><CardDescription className="text-xs">Seeded development accounts – never use these credentials in production.</CardDescription></CardHeader>
              <CardContent>
                <Table><TableHeader><TableRow><TableHead>User</TableHead><TableHead>Role</TableHead><TableHead>Status</TableHead><TableHead>Last login</TableHead></TableRow></TableHeader>
                  <TableBody>{users.data?.map((u) => (
                    <TableRow key={u.id}><TableCell className="text-xs">{u.full_name}<div className="text-muted-foreground">{u.email}</div></TableCell><TableCell className="text-xs capitalize">{u.role}</TableCell>
                      <TableCell><StatusBadge status={u.is_active ? "ok" : "neutral"} label={u.is_active ? "active" : "disabled"} /></TableCell><TableCell className="text-xs text-muted-foreground">{fmtRelative(u.last_login_at)}</TableCell></TableRow>
                  ))}</TableBody></Table>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </>
  );
}
