"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { api } from "@/lib/api";
import { DISCLAIMER } from "@/lib/disclaimer";
import { KEYS, writeKey } from "@/lib/session";
import { Panel } from "@/components/Panel";

const STEPS = ["Disclaimer", "Household", "Cash-flow", "Goals & risk", "Constraints"];

function OnboardingForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [step, setStep] = useState(0);
  const [accepted, setAccepted] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    first_name: "",
    age: 33,
    city: "",
    state: "",
    marital_status: "married",
    dependents: 0,
    earners: 1,
    monthly_take_home_inr: 0,
    essential_expenses_monthly_inr: 0,
    discretionary_expenses_monthly_inr: 0,
    insurance_premiums_monthly_inr: 0,
    rent_monthly_inr: 0,
    tax_regime: "unknown",
    emotional_tolerance: 3,
    financial_capacity: 3,
    income_stability: 3,
    investment_experience: 2,
    liquidity_need: 3,
    goal_horizon_years: 10,
    goal_name: "emergency reserve",
    goal_amount: 300000,
    goal_year: 2028,
    international_opt_in: false,
    direct_equity_opt_in: false,
    vda_opt_in: false,
    constraints: [] as string[],
  });

  useEffect(() => {
    if (params.get("demo") === "2") {
      void loadDemo();
    }
  }, [params]);

  async function loadDemo() {
    setError("");
    try {
      const res = await api<{ data: { household_id: string; plan_id: string } }>("/api/v1/demo/seed/2", {
        method: "POST",
      });
      writeKey(KEYS.disclaimer, "1");
      writeKey(KEYS.household, res.data.household_id);
      writeKey(KEYS.plan, res.data.plan_id);
      router.push("/war-room");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo seed failed");
    }
  }

  const payload = useMemo(
    () => ({
      first_name: form.first_name,
      age: Number(form.age),
      city: form.city,
      state: form.state,
      marital_status: form.marital_status,
      dependents: Number(form.dependents),
      earners: Number(form.earners),
      monthly_take_home_inr: Number(form.monthly_take_home_inr),
      essential_expenses_monthly_inr: Number(form.essential_expenses_monthly_inr),
      discretionary_expenses_monthly_inr: Number(form.discretionary_expenses_monthly_inr),
      insurance_premiums_monthly_inr: Number(form.insurance_premiums_monthly_inr),
      rent_monthly_inr: Number(form.rent_monthly_inr),
      tax_regime: form.tax_regime,
      international_opt_in: form.international_opt_in,
      direct_equity_opt_in: form.direct_equity_opt_in,
      vda_opt_in: form.vda_opt_in,
      constraints: form.constraints,
      goals: [
        {
          name: form.goal_name,
          target_amount_inr: Number(form.goal_amount),
          target_year: Number(form.goal_year),
          priority: "must_have",
        },
      ],
      risk: {
        emotional_tolerance: Number(form.emotional_tolerance),
        financial_capacity: Number(form.financial_capacity),
        income_stability: Number(form.income_stability),
        investment_experience: Number(form.investment_experience),
        liquidity_need: Number(form.liquidity_need),
        goal_horizon_years: Number(form.goal_horizon_years),
      },
      existing_holdings: [],
    }),
    [form],
  );

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (!accepted) {
      setError("Accept the educational disclaimer to continue.");
      return;
    }
    try {
      const res = await api<{ data: { household_id: string } }>("/api/v1/ips", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      writeKey(KEYS.disclaimer, "1");
      writeKey(KEYS.household, res.data.household_id);
      router.push("/holdings");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save profile");
    }
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[220px_1fr]">
      <ol className="space-y-2 text-sm">
        {STEPS.map((label, i) => (
          <li key={label} className={i === step ? "text-navy" : "text-ink/50"}>
            {i + 1}. {label}
          </li>
        ))}
      </ol>
      <Panel title="Household mandate" kicker="Onboarding">
        <p className="mb-6 text-sm leading-6 text-ink/80">{DISCLAIMER}</p>
        <form onSubmit={onSubmit} className="grid gap-4">
          {step === 0 && (
            <label className="flex items-start gap-3 text-sm">
              <input type="checkbox" checked={accepted} onChange={(e) => setAccepted(e.target.checked)} />
              I understand this is an educational simulation and not SEBI-regulated advice.
            </label>
          )}
          {step === 1 && (
            <div className="grid gap-3 md:grid-cols-2">
              <Field label="First name" value={form.first_name} onChange={(v) => set("first_name", v)} />
              <Field label="Age" type="number" value={String(form.age)} onChange={(v) => set("age", Number(v))} />
              <Field label="City" value={form.city} onChange={(v) => set("city", v)} />
              <Field label="State" value={form.state} onChange={(v) => set("state", v)} />
            </div>
          )}
          {step === 2 && (
            <div className="grid gap-3 md:grid-cols-2">
              <Field label="Monthly take-home (₹)" type="number" value={String(form.monthly_take_home_inr)} onChange={(v) => set("monthly_take_home_inr", Number(v))} />
              <Field label="Essential expenses (₹)" type="number" value={String(form.essential_expenses_monthly_inr)} onChange={(v) => set("essential_expenses_monthly_inr", Number(v))} />
              <Field label="Discretionary (₹)" type="number" value={String(form.discretionary_expenses_monthly_inr)} onChange={(v) => set("discretionary_expenses_monthly_inr", Number(v))} />
              <Field label="Rent (₹)" type="number" value={String(form.rent_monthly_inr)} onChange={(v) => set("rent_monthly_inr", Number(v))} />
            </div>
          )}
          {step === 3 && (
            <div className="grid gap-3 md:grid-cols-2">
              <Field label="Goal name" value={form.goal_name} onChange={(v) => set("goal_name", v)} />
              <Field label="Goal amount (₹)" type="number" value={String(form.goal_amount)} onChange={(v) => set("goal_amount", Number(v))} />
              <Field label="Emotional tolerance (1-5)" type="number" value={String(form.emotional_tolerance)} onChange={(v) => set("emotional_tolerance", Number(v))} />
              <Field label="Financial capacity (1-5)" type="number" value={String(form.financial_capacity)} onChange={(v) => set("financial_capacity", Number(v))} />
            </div>
          )}
          {step === 4 && (
            <div className="grid gap-3">
              <label className="text-sm">
                Tax regime
                <select
                  className="mt-1 w-full p-2"
                  value={form.tax_regime}
                  onChange={(e) => set("tax_regime", e.target.value)}
                >
                  <option value="unknown">unknown</option>
                  <option value="new">new</option>
                  <option value="old">old</option>
                </select>
              </label>
              <label className="text-sm">
                <input
                  type="checkbox"
                  className="mr-2"
                  checked={form.constraints.includes("no_crypto")}
                  onChange={(e) =>
                    set(
                      "constraints",
                      e.target.checked
                        ? [...form.constraints, "no_crypto"]
                        : form.constraints.filter((c) => c !== "no_crypto"),
                    )
                  }
                />
                No crypto / VDA
              </label>
              <label className="text-sm">
                <input
                  type="checkbox"
                  className="mr-2"
                  checked={form.constraints.includes("no_international")}
                  onChange={(e) =>
                    set(
                      "constraints",
                      e.target.checked
                        ? [...form.constraints, "no_international"]
                        : form.constraints.filter((c) => c !== "no_international"),
                    )
                  }
                />
                No international assets
              </label>
            </div>
          )}
          {error ? <p className="text-sm text-seal">{error}</p> : null}
          <div className="flex flex-wrap gap-3">
            {step > 0 ? (
              <button type="button" className="border border-navy px-4 py-2 text-sm" onClick={() => setStep(step - 1)}>
                Back
              </button>
            ) : null}
            {step < STEPS.length - 1 ? (
              <button type="button" className="bg-navy px-4 py-2 text-sm text-paper" onClick={() => setStep(step + 1)}>
                Continue
              </button>
            ) : (
              <button type="submit" className="bg-navy px-4 py-2 text-sm text-paper">
                Save IPS
              </button>
            )}
            <button type="button" className="border border-brass px-4 py-2 text-sm text-navy" onClick={loadDemo}>
              Load demo household #2
            </button>
          </div>
        </form>
      </Panel>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
}) {
  return (
    <label className="text-sm">
      {label}
      <input className="mt-1 w-full p-2" type={type} value={value} onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}

export default function OnboardingPage() {
  return (
    <Suspense fallback={<p>Loading onboarding…</p>}>
      <OnboardingForm />
    </Suspense>
  );
}
