"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { KEYS, readKey } from "@/lib/session";
import { pct } from "@/lib/format";
import { DISCLAIMER } from "@/lib/disclaimer";
import { Panel } from "@/components/Panel";

type Scenario = {
  name: string;
  label: string;
  equity_pct: number;
  fixed_income_pct: number;
  cash_pct: number;
  gold_pct: number;
  alternatives_pct: number;
  international_pct: number;
  estimated_volatility_class: string;
  liquidity: string;
  goal_fit: string;
  risk_flags: string[];
  source_coverage_pct: number;
  argument_for: string;
  argument_against: string;
};

export default function ComparePage() {
  const router = useRouter();
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [planId, setPlanId] = useState<string | null>(null);

  useEffect(() => {
    const id = readKey(KEYS.plan);
    setPlanId(id);
    if (!id) return;
    void api<{ data: { scenarios: Scenario[] } }>(`/api/v1/plans/${id}`).then((res) => {
      setScenarios(res.data.scenarios);
    });
  }, []);

  async function select(name: string) {
    if (!planId) return;
    await api(`/api/v1/plans/${planId}/select`, {
      method: "POST",
      body: JSON.stringify({ scenario: name }),
    });
    router.push(`/plan/${planId}`);
  }

  return (
    <div>
      <p className="mb-4 text-sm text-ink/75">{DISCLAIMER}</p>
      <div className="grid gap-4 md:grid-cols-3">
        {scenarios.map((s) => (
          <Panel key={s.name} title={s.label} kicker="Educational simulation">
            <dl className="space-y-2 text-sm">
              <Row k="Equity" v={pct(s.equity_pct)} />
              <Row k="Fixed income" v={pct(s.fixed_income_pct)} />
              <Row k="Cash" v={pct(s.cash_pct)} />
              <Row k="Gold" v={pct(s.gold_pct)} />
              <Row k="International" v={pct(s.international_pct)} />
              <Row k="Alternatives" v={pct(s.alternatives_pct)} />
              <Row k="Volatility" v={s.estimated_volatility_class} />
              <Row k="Liquidity" v={s.liquidity} />
              <Row k="Source coverage" v={pct(s.source_coverage_pct)} />
            </dl>
            <p className="mt-4 text-sm">{s.goal_fit}</p>
            <p className="mt-2 text-sm text-moss">For: {s.argument_for}</p>
            <p className="mt-2 text-sm text-seal">Against: {s.argument_against}</p>
            {s.risk_flags.length ? <p className="mt-2 text-xs text-brass">{s.risk_flags.join(", ")}</p> : null}
            <button className="mt-4 border border-navy px-3 py-2 text-sm" onClick={() => select(s.name)}>
              Select {s.label}
            </button>
          </Panel>
        ))}
      </div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between border-b border-rule py-1">
      <dt>{k}</dt>
      <dd>{v}</dd>
    </div>
  );
}
