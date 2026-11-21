import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import { useAuth } from "../auth";
import { Badge, Button, Card, ErrorBox, Loading, PageHeader, Select } from "../ui";

export default function Admin() {
  const { has } = useAuth();
  const qc = useQueryClient();
  const suppliers = useQuery({ queryKey: ["suppliers"], queryFn: () => api("/api/suppliers") });
  const policies = useQuery({ queryKey: ["policies"], queryFn: () => api("/api/policies") });
  const fixtures = useQuery({ queryKey: ["fixtures"], queryFn: () => api("/api/admin/fixtures/scenarios"), enabled: has("admin"), retry: false });
  const active = policies.data?.policies.find((p: any) => p.active);
  const [scenario, setScenario] = useState("happy_path");

  const patch = useMutation({ mutationFn: ({ id, body }: { id: string; body: any }) => api(`/api/suppliers/${id}`, { method: "PATCH", json: body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["suppliers"] }) });
  const reset = useMutation({ mutationFn: () => api("/api/admin/fixtures/reset", { method: "POST", json: { scenario } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["fixtures"] }) });
  const priceRise = useMutation({ mutationFn: () => api("/api/admin/fixtures/mutate", { method: "POST",
    json: { supplier: "beta", products: { "B-77821": { unit_price: "48900.00" } } } }) });

  if (!has("admin")) return <p className="text-sm text-muted">Administrator role required.</p>;
  return (
    <div className="space-y-5">
      <PageHeader title="Suppliers, policy and fixtures" subtitle="Administrative settings. Policy is data enforced by code, never model instructions." />
      <Card title="Suppliers">
        {suppliers.isLoading ? <Loading /> : (
          <div className="overflow-x-auto"><table className="w-full text-sm">
            <thead className="text-left text-xs text-muted"><tr><th className="py-2 pr-3">Supplier</th><th className="pr-3">Allowed origins</th>
              <th className="pr-3">Adapter</th><th className="pr-3">Eligibility</th><th className="pr-3">Enabled</th><th>Contract</th></tr></thead>
            <tbody>{suppliers.data?.suppliers.map((s: any) => (
              <tr key={s.id} className="border-t border-line">
                <td className="py-2 pr-3 font-medium">{s.name} {s.synthetic && <Badge kind="warn">synthetic</Badge>}</td>
                <td className="pr-3 font-mono text-xs">{s.allowed_origins.join(", ")}</td>
                <td className="pr-3 text-xs">{s.adapter}</td>
                <td className="pr-3"><Select aria-label={`${s.name} eligibility`} value={s.eligibility_status} className="w-36"
                  onChange={(e) => patch.mutate({ id: s.id, body: { eligibility_status: e.target.value } })}>
                  <option value="approved">approved</option><option value="suspended">suspended</option></Select></td>
                <td className="pr-3"><input type="checkbox" aria-label={`${s.name} enabled`} checked={s.enabled}
                  onChange={(e) => patch.mutate({ id: s.id, body: { enabled: e.target.checked } })} /></td>
                <td className="text-xs text-muted">conditional submit: {String(s.conditional_submit_supported)}; status API: {String(s.status_api_supported)}</td>
              </tr>))}</tbody></table></div>
        )}
        <ErrorBox error={patch.error} />
        <p className="mt-2 text-xs text-muted">Credentials are referenced by ID and resolved from the secret store at run time; they are never shown here or sent to a model.</p>
      </Card>
      {active && <PolicyEditor key={active.id} version={active.version} rules={active.rules} />}
      <Card title="Fixture scenarios (operator only, outside the agent's environment)">
        {fixtures.error ? <ErrorBox error={fixtures.error} /> : fixtures.isLoading ? <Loading /> : (
          <div className="space-y-3">
            <p className="text-sm">Active scenario: <Badge kind="info">{fixtures.data.state.scenario}</Badge></p>
            <div className="flex flex-wrap gap-2">
              <Select aria-label="Scenario" value={scenario} onChange={(e) => setScenario(e.target.value)} className="w-72">
                {Object.entries(fixtures.data.scenarios).map(([k, v]: any) => <option key={k} value={k} title={v.description}>{k}</option>)}
              </Select>
              <Button variant="danger" onClick={() => { if (confirm(`Reset synthetic supplier data to "${scenario}"? Mock orders and carts are deleted.`)) reset.mutate(); }}>Reset suppliers</Button>
              <Button variant="secondary" onClick={() => priceRise.mutate()}>Demo: raise Beta price to ₹48,900</Button>
            </div>
            <p className="text-xs text-muted">{fixtures.data.scenarios[scenario]?.description}</p>
            <ErrorBox error={reset.error ?? priceRise.error} />
          </div>
        )}
      </Card>
    </div>
  );
}

function PolicyEditor({ version, rules }: { version: number; rules: unknown }) {
  const qc = useQueryClient();
  const [draft, setDraft] = useState(() => JSON.stringify(rules, null, 2));
  const save = useMutation({ mutationFn: () => api("/api/policies", { method: "POST", json: { rules: JSON.parse(draft) } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["policies"] }) });
  return (
    <Card title={`Purchasing policy (active version ${version})`}
      actions={<Button onClick={() => save.mutate()} disabled={save.isPending}>Save as new version</Button>}>
      <label htmlFor="policy" className="sr-only">Policy JSON</label>
      <textarea id="policy" className="h-80 w-full rounded-md border border-line p-3 font-mono text-xs" value={draft} onChange={(e) => setDraft(e.target.value)} />
      <ErrorBox error={save.error} />
      <p className="mt-2 text-xs text-muted">Saving creates a new immutable version; runs keep the version they started with and approvals bind to it.</p>
    </Card>
  );
}
