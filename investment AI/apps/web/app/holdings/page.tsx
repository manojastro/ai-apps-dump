"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { KEYS, readKey, writeKey } from "@/lib/session";
import { Panel } from "@/components/Panel";
import { inr } from "@/lib/format";

export default function HoldingsPage() {
  const router = useRouter();
  const [text, setText] = useState("EPF 850000\nNifty 50 index SIP 420000\nFlexi-cap SIP 180000\nLiquid fund 120000");
  const [rows, setRows] = useState<Array<{ name: string; current_value_inr: number; category: string }>>([]);
  const [meta, setMeta] = useState("");
  const [error, setError] = useState("");

  async function parse() {
    setError("");
    const household = readKey(KEYS.household);
    if (!household) {
      setError("Create a household profile first.");
      return;
    }
    try {
      const res = await api<{
        data: { holdings: Array<{ name: string; current_value_inr: number; category: string }>; meta: { redacted: boolean; kinds: string[] } };
      }>("/api/v1/holdings/parse", {
        method: "POST",
        body: JSON.stringify({ household_id: household, text }),
      });
      setRows(res.data.holdings);
      setMeta(
        res.data.meta.redacted
          ? `PII redacted (${res.data.meta.kinds.join(", ")}) before any model call.`
          : "No PII patterns detected.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Parse failed");
    }
  }

  async function generate() {
    const household = readKey(KEYS.household);
    if (!household) return;
    const res = await api<{ data: { plan_id: string } }>("/api/v1/plans", {
      method: "POST",
      body: JSON.stringify({ household_id: household, holdings: rows }),
    });
    writeKey(KEYS.plan, res.data.plan_id);
    router.push("/war-room");
  }

  return (
    <Panel title="Holdings" kicker="Paste statements after PII redaction">
      <p className="mb-4 text-sm text-ink/75">
        Do not paste Aadhaar or PAN. If they appear, they are redacted in Python before any LLM sees the text.
      </p>
      <textarea className="min-h-40 w-full p-3 font-mono text-sm" value={text} onChange={(e) => setText(e.target.value)} />
      <div className="mt-4 flex gap-3">
        <button className="bg-navy px-4 py-2 text-sm text-paper" onClick={parse}>
          Parse holdings
        </button>
        <button className="border border-navy px-4 py-2 text-sm" onClick={generate} disabled={!rows.length}>
          Generate plan
        </button>
      </div>
      {meta ? <p className="mt-3 text-sm text-moss">{meta}</p> : null}
      {error ? <p className="mt-3 text-sm text-seal">{error}</p> : null}
      {rows.length ? (
        <table className="mt-6 w-full text-left text-sm">
          <thead>
            <tr className="border-b border-rule">
              <th className="py-2">Name</th>
              <th>Category</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.name} className="border-b border-rule/70">
                <td className="py-2">{row.name}</td>
                <td>{row.category}</td>
                <td>{inr(row.current_value_inr)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </Panel>
  );
}
