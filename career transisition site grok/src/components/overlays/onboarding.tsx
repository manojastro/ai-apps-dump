"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { TARGET_LOCATIONS, TARGET_ROLE_NAMES } from "@/lib/constants";
import { useCareerStore } from "@/store/career-store";

const STEPS = ["Baseline", "Target roles", "Salary", "Locations", "Capacity", "Workspace"] as const;

export function OnboardingGate() {
  const state = useCareerStore((s) => s.state);
  const recovery = useCareerStore((s) => s.recovery);
  const updateSettings = useCareerStore((s) => s.updateSettings);
  const setUi = useCareerStore((s) => s.setUi);
  const loadDemo = useCareerStore((s) => s.loadDemo);
  const [step, setStep] = useState(0);
  const [roles, setRoles] = useState<string[]>(state.settings.targetRoles.slice(0, 3));
  const [locations, setLocations] = useState<string[]>(state.settings.targetLocations);
  const [form, setForm] = useState({
    baselineCtc: String(state.settings.baselineCtc),
    targetMinCtc: String(state.settings.targetMinCtc),
    targetMaxCtc: String(state.settings.targetMaxCtc),
    stretchCtc: String(state.settings.stretchCtc),
    weeklyAvailableHours: String(state.settings.weeklyAvailableHours),
    weeklyLearningHoursTarget: String(state.settings.weeklyLearningHoursTarget),
    weeklyApplicationsTarget: String(state.settings.weeklyApplicationsTarget),
  });

  if (recovery || state.ui.onboardingComplete) return null;

  const toggle = (list: string[], value: string, set: (v: string[]) => void) => {
    set(list.includes(value) ? list.filter((x) => x !== value) : [...list, value]);
  };

  const finish = (mode: "clean" | "demo") => {
    updateSettings({
      baselineCtc: Number(form.baselineCtc),
      targetMinCtc: Number(form.targetMinCtc),
      targetMaxCtc: Number(form.targetMaxCtc),
      stretchCtc: Number(form.stretchCtc),
      targetRoles: roles,
      targetLocations: locations,
      weeklyAvailableHours: Number(form.weeklyAvailableHours),
      weeklyLearningHoursTarget: Number(form.weeklyLearningHoursTarget),
      weeklyApplicationsTarget: Number(form.weeklyApplicationsTarget),
    });
    if (mode === "demo") loadDemo();
    else setUi({ onboardingComplete: true, demoMode: false });
  };

  return (
    <div className="fixed inset-0 z-40 grid place-items-center bg-[#090d16]/92 p-4 backdrop-blur-sm">
      <div className="card w-full max-w-2xl p-7">
        <div className="mb-4 h-1 w-full overflow-hidden rounded-full bg-white/8">
          <div className="h-full bg-gradient-to-r from-emerald-400 to-cyan-400" style={{ width: `${((step + 1) / STEPS.length) * 100}%` }} />
        </div>
        <p className="text-[11px] font-medium tracking-[0.16em] text-cyan-300 uppercase">First run</p>
        <h2 className="mt-1 text-xl font-semibold tracking-tight">AI Career Transition — 2026</h2>
        <p className="mt-1 text-[13px] text-slate-400">
          Step {step + 1} of {STEPS.length}: {STEPS[step]}
        </p>
        <div className="mt-5 space-y-3">
          {step === 0 ? (
            <p className="text-[13px] text-slate-300">
              8.5 years in enterprise technology operations. Baseline compensation ₹11 LPA. The OS will treat operations
              experience as domain strength — and will not position you around service-desk chatbots.
            </p>
          ) : null}
          {step === 1 ? (
            <div className="flex flex-wrap gap-2">
              {TARGET_ROLE_NAMES.map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => toggle(roles, r, setRoles)}
                  className={`rounded-lg border px-2 py-1 text-[12px] ${roles.includes(r) ? "border-cyan-400/40 bg-cyan-400/10 text-cyan-100" : "border-white/10 text-slate-400"}`}
                >
                  {r}
                </button>
              ))}
            </div>
          ) : null}
          {step === 2 ? (
            <div className="grid grid-cols-2 gap-3">
              <Field label="Baseline LPA"><Input value={form.baselineCtc} onChange={(e) => setForm({ ...form, baselineCtc: e.target.value })} /></Field>
              <Field label="Target min LPA"><Input value={form.targetMinCtc} onChange={(e) => setForm({ ...form, targetMinCtc: e.target.value })} /></Field>
              <Field label="Target max LPA"><Input value={form.targetMaxCtc} onChange={(e) => setForm({ ...form, targetMaxCtc: e.target.value })} /></Field>
              <Field label="Stretch LPA"><Input value={form.stretchCtc} onChange={(e) => setForm({ ...form, stretchCtc: e.target.value })} /></Field>
            </div>
          ) : null}
          {step === 3 ? (
            <div className="flex flex-wrap gap-2">
              {TARGET_LOCATIONS.map((l) => (
                <button
                  key={l}
                  type="button"
                  onClick={() => toggle(locations, l, setLocations)}
                  className={`rounded-lg border px-2 py-1 text-[12px] ${locations.includes(l) ? "border-emerald-400/40 bg-emerald-400/10 text-emerald-100" : "border-white/10 text-slate-400"}`}
                >
                  {l}
                </button>
              ))}
            </div>
          ) : null}
          {step === 4 ? (
            <div className="grid grid-cols-3 gap-3">
              <Field label="Weekly hours"><Input value={form.weeklyAvailableHours} onChange={(e) => setForm({ ...form, weeklyAvailableHours: e.target.value })} /></Field>
              <Field label="Learning hours target"><Input value={form.weeklyLearningHoursTarget} onChange={(e) => setForm({ ...form, weeklyLearningHoursTarget: e.target.value })} /></Field>
              <Field label="Applications / week"><Input value={form.weeklyApplicationsTarget} onChange={(e) => setForm({ ...form, weeklyApplicationsTarget: e.target.value })} /></Field>
            </div>
          ) : null}
          {step === 5 ? (
            <div className="space-y-3 text-[13px] text-slate-300">
              <p>Demo data is optional and labeled. It is not inserted automatically.</p>
              <div className="flex flex-wrap gap-2">
                <Button onClick={() => finish("clean")}>Start Clean</Button>
                <Button variant="outline" onClick={() => finish("demo")}>
                  Load Demo Workspace
                </Button>
              </div>
            </div>
          ) : null}
        </div>
        {step < 5 ? (
          <div className="mt-6 flex justify-between">
            <Button variant="ghost" disabled={step === 0} onClick={() => setStep((s) => s - 1)}>
              Back
            </Button>
            <Button onClick={() => setStep((s) => s + 1)}>Continue</Button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
