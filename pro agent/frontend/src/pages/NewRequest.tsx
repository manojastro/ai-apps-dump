import { useMemo, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { useAuth } from "../auth";
import { Button, Card, ErrorBox, Field, Input, PageHeader, Select, SyntheticBanner } from "../ui";

function plusDays(n: number) {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

export default function NewRequest() {
  const nav = useNavigate();
  const { has } = useAuth();
  const products = useQuery({ queryKey: ["products"], queryFn: () => api("/api/catalog/products") });
  const suppliers = useQuery({ queryKey: ["suppliers"], queryFn: () => api("/api/suppliers") });
  const policies = useQuery({ queryKey: ["policies"], queryFn: () => api("/api/policies") });
  const destinations = useMemo(() => Object.entries(policies.data?.policies.find((p: any) => p.active)?.rules.destinations ?? {}),
    [policies.data]);
  const [form, setForm] = useState({
    title: "Ten business laptops for the Bengaluru team", canonical_product_id: "NW-PRO14-16-512", min_ram_gb: 16,
    min_ssd_gb: 512, quantity: 10, currency: "INR", budget_total: "500000.00", address_ref: "ADDR-BLR-01",
    delivery_deadline: plusDays(7),
  });
  const [chosen, setChosen] = useState<string[]>([]);
  const [plant, setPlant] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const set = (k: string, v: string | number) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const req = await api("/api/requests", { method: "POST", idempotent: true, json: { ...form, allowed_suppliers: chosen } });
      const run = await api(`/api/requests/${req.id}/runs`, {
        method: "POST", idempotent: true,
        json: plant && has("admin") ? { fixture_options: { planted_bad_recommendation: "A-NW14-8-512" } } : {},
      });
      nav(`/runs/${run.id}`);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-5">
      <PageHeader title="New purchase request" subtitle="The agent gathers offers through the supplier portals; nothing is bought without an approver." />
      <SyntheticBanner />
      <form onSubmit={submit} className="space-y-5">
        <Card title="What to buy">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2"><Field id="title" label="Title">
              <Input id="title" value={form.title} onChange={(e) => set("title", e.target.value)} required minLength={3} /></Field></div>
            <Field id="product" label="Canonical product">
              <Select id="product" value={form.canonical_product_id} onChange={(e) => set("canonical_product_id", e.target.value)}>
                {products.data?.products.map((p: any) => <option key={p.id} value={p.id}>{p.family} · {p.ram_gb}GB / {p.ssd_gb}GB ({p.id})</option>)}
              </Select></Field>
            <Field id="qty" label="Quantity (individual laptops)">
              <Input id="qty" type="number" min={1} max={1000} value={form.quantity} onChange={(e) => set("quantity", Number(e.target.value))} required /></Field>
            <Field id="ram" label="Minimum RAM (GB)">
              <Input id="ram" type="number" min={1} value={form.min_ram_gb} onChange={(e) => set("min_ram_gb", Number(e.target.value))} required /></Field>
            <Field id="ssd" label="Minimum SSD (GB)">
              <Input id="ssd" type="number" min={1} value={form.min_ssd_gb} onChange={(e) => set("min_ssd_gb", Number(e.target.value))} required /></Field>
          </div>
        </Card>
        <Card title="Constraints">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field id="budget" label="Budget incl. tax and shipping (INR)">
              <Input id="budget" inputMode="decimal" pattern="^\d+(\.\d{1,2})?$" value={form.budget_total} onChange={(e) => set("budget_total", e.target.value)} required /></Field>
            <Field id="deadline" label="Deliver by">
              <Input id="deadline" type="date" min={plusDays(1)} value={form.delivery_deadline} onChange={(e) => set("delivery_deadline", e.target.value)} required /></Field>
            <Field id="dest" label="Destination" hint="Addresses are referenced by code; full addresses never enter prompts or logs.">
              <Select id="dest" value={form.address_ref} onChange={(e) => set("address_ref", e.target.value)}>
                {destinations.map(([ref, label]) => <option key={ref} value={ref}>{String(label)} ({ref})</option>)}
              </Select></Field>
            <fieldset className="space-y-1">
              <legend className="text-sm font-medium">Allowed suppliers</legend>
              <p className="text-xs text-muted">None selected means all enabled suppliers.</p>
              {suppliers.data?.suppliers.map((s: any) => (
                <label key={s.key} className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={chosen.includes(s.key)} disabled={!s.enabled}
                    onChange={(e) => setChosen((c) => e.target.checked ? [...c, s.key] : c.filter((x) => x !== s.key))} />
                  {s.name} {s.synthetic && <span className="text-xs text-muted">(synthetic)</span>}
                </label>
              ))}
            </fieldset>
          </div>
        </Card>
        {has("admin") && (
          <Card title="Demonstration options (administrator)">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={plant} onChange={(e) => setPlant(e.target.checked)} />
              Plant a bad recommendation (cheaper 8 GB laptop) so the verifier rejection is visible
            </label>
          </Card>
        )}
        <ErrorBox error={error} />
        <Button type="submit" disabled={busy}>{busy ? "Starting…" : "Create request and start run"}</Button>
      </form>
    </div>
  );
}
