"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FastForward, Hammer, ScanLine } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { SimBadge } from "@/components/badges";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useCan } from "@/hooks/use-me";
import { api } from "@/lib/api";
import type { FindingDetail, ServiceNowRecord } from "@/lib/types";

/**
 * Actions performed by the *simulated outside world*: a ServiceNow implementer moving the change,
 * and an engineer patching the host. They exist only in simulation mode and are labelled as such.
 */
export function SimulationConsole({ finding, records, targetVersion }: { finding: FindingDetail; records: ServiceNowRecord[]; targetVersion: string | null }) {
  const qc = useQueryClient();
  const canSim = useCan("simulation:control");
  const canVerify = useCan("verification:submit");
  const change = records.find((r) => r.table_name === "change_request" && r.mode === "mock" && r.sys_id);
  const device = finding.simulated_device;
  const sw = device?.software.find((s) => s.vendor === finding.finding.software_vendor && s.display_name === finding.finding.software);
  const [version, setVersion] = useState(targetVersion ?? "");

  const done = (title: string) => () => { toast.success(title); qc.invalidateQueries(); };
  const fail = (e: Error) => toast.error(e.message);
  const advance = useMutation({ mutationFn: () => api.post<{ from: string; to: string }>(`/simulation/servicenow/records/${change?.id}/advance`, {}),
    onSuccess: (r) => toast.success(`Change moved ${r.from} → ${r.to}`, { description: "Remediation status synchronised from ServiceNow." }), onError: fail, onSettled: () => qc.invalidateQueries() });
  const patch = useMutation({ mutationFn: () => api.post(`/simulation/devices/${device?.device_id}/patch`, { vendor: sw?.vendor, product: sw?.product, version }),
    onSuccess: done(`Simulated deployment of ${sw?.display_name} ${version}`), onError: fail });
  const rescan = useMutation({ mutationFn: () => api.post(`/findings/${finding.finding.id}/rescan`),
    onSuccess: done("Rescan collected; verification evaluated"), onError: fail });

  return (
    <Card id="simulation" className="border-dashed">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">Simulation console <SimBadge label="outside world" /></CardTitle>
        <CardDescription className="text-xs">These controls stand in for people and systems outside AegisRemediate. The platform itself never patches hosts.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2 text-sm">
          <div className="font-medium">1 · ServiceNow implementer</div>
          <p className="text-xs text-muted-foreground">{change ? `${change.number}: ${change.external_state_label ?? "New"}` : "No simulated change request yet (requires approval + sync)."}</p>
          <Button size="sm" variant="outline" disabled={!change || !canSim || advance.isPending || change.external_state === "3"} onClick={() => advance.mutate()}>
            <FastForward /> Advance change state
          </Button>
        </div>
        <div className="space-y-2 text-sm">
          <div className="font-medium">2 · Engineer deploys fix</div>
          <p className="text-xs text-muted-foreground">{sw ? `${device?.computer_dns_name}: ${sw.display_name} ${sw.version} installed` : "Asset not managed by the simulated Defender tenant."}</p>
          <div className="flex gap-2">
            <Input value={version} onChange={(e) => setVersion(e.target.value)} placeholder="Deployed version" className="h-7 text-xs" aria-label="Deployed version" />
            <Button size="sm" variant="outline" disabled={!sw || !version || !canSim || patch.isPending} onClick={() => patch.mutate()}><Hammer /> Deploy</Button>
          </div>
        </div>
        <div className="space-y-2 text-sm">
          <div className="font-medium">3 · Scanner rescan</div>
          <p className="text-xs text-muted-foreground">Collects fresh Defender evidence; only this can verify remediation.</p>
          <Button size="sm" disabled={!canVerify || rescan.isPending || finding.finding.scanner !== "mock_defender"} onClick={() => rescan.mutate()}><ScanLine /> Request rescan</Button>
        </div>
      </CardContent>
    </Card>
  );
}
