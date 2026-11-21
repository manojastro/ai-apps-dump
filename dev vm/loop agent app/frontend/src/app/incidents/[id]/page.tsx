"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Badge from "@/components/ui/Badge";
import IncidentGraph from "@/components/graph/IncidentGraph";
import {
  approve,
  getEvidence,
  getHypotheses,
  getIncident,
  getIncidentGraph,
  getReport,
  getTimeline,
  investigate,
} from "@/lib/api";
import { fmtTime } from "@/lib/utils";

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const [inc, setInc] = useState<any>(null);
  const [graph, setGraph] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [evidence, setEvidence] = useState<any[]>([]);
  const [hyps, setHyps] = useState<any[]>([]);
  const [report, setReport] = useState<any>(null);
  const [selected, setSelected] = useState<any>(null);
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    const [i, g, t, e, h, r] = await Promise.all([
      getIncident(id),
      getIncidentGraph(id),
      getTimeline(id),
      getEvidence(id),
      getHypotheses(id),
      getReport(id),
    ]);
    setInc(i);
    setGraph(g);
    setEvents(t.events || []);
    setEvidence(e);
    setHyps(h);
    setReport(r);
  };

  useEffect(() => {
    refresh().catch(() => {});
    const es = new EventSource(`/api/incidents/${id}/events`);
    es.onmessage = () => refresh().catch(() => {});
    es.addEventListener("graph.node.started", () => refresh().catch(() => {}));
    es.addEventListener("graph.node.completed", () => refresh().catch(() => {}));
    es.addEventListener("approval.required", () => refresh().catch(() => {}));
    es.addEventListener("incident.resolved", () => refresh().catch(() => {}));
    es.addEventListener("hypothesis.generated", () => refresh().catch(() => {}));
    es.addEventListener("hypothesis.rejected", () => refresh().catch(() => {}));
    es.addEventListener("root_cause.confirmed", () => refresh().catch(() => {}));
    const iv = setInterval(() => refresh().catch(() => {}), 1500);
    return () => {
      es.close();
      clearInterval(iv);
    };
  }, [id]);

  if (!inc) return <div className="text-zinc-500">Loading incident…</div>;

  const waiting = inc.status === "WAITING_APPROVAL" || inc.human_approval_required;
  const loop = graph?.loop || {};
  const interrupt = graph?.interrupt || inc.state?.interrupt_payload;

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="font-mono text-teal-300 text-sm">{inc.id}</div>
          <h1 className="text-2xl font-semibold mt-1">{inc.title}</h1>
          <div className="mt-2 flex flex-wrap gap-2 text-[12px] text-zinc-400">
            <span>
              Severity <Badge status={inc.severity}>{inc.severity}</Badge>
            </span>
            <span>Pipeline {inc.pipeline_id}</span>
            <span>Started {fmtTime(inc.detected_at)}</span>
            <span>
              Status <Badge status={inc.status}>{inc.status}</Badge>
            </span>
          </div>
          {inc.error_message ? (
            <pre className="mt-3 text-[12px] text-rose-200 bg-rose-400/5 border border-rose-400/20 rounded p-3 whitespace-pre-wrap">
              {inc.error_message}
            </pre>
          ) : null}
        </div>
        <button
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            await investigate(id);
            setBusy(false);
          }}
          className="px-4 py-2 rounded-md bg-teal-400 text-ink-950 text-sm font-semibold hover:bg-teal-300 disabled:opacity-50"
        >
          Investigate incident
        </button>
      </div>

      {waiting && interrupt ? (
        <div className="rounded-lg border border-amber-400/40 bg-amber-400/10 p-4 space-y-3">
          <div className="text-[11px] uppercase tracking-[0.16em] text-amber-200">Human approval required</div>
          <div className="text-sm">
            <div className="font-medium">Root cause</div>
            <div className="text-zinc-300">{interrupt.root_cause?.statement || inc.root_cause?.statement}</div>
            <div className="mt-2 font-medium">Proposed fix</div>
            <div className="text-zinc-300">{interrupt.remediation?.title || inc.selected_remediation?.title}</div>
            <div className="mt-2 text-[12px] text-zinc-400">
              Risk {interrupt.risk || inc.risk_level} · Sandbox {String(interrupt.sandbox?.passed)} · Policy{" "}
              {interrupt.policy_action}
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => approve(id, "approve").then(refresh)}
              className="px-3 py-1.5 rounded bg-emerald-400 text-ink-950 text-sm font-semibold"
            >
              Approve
            </button>
            <button
              onClick={() => approve(id, "reject").then(refresh)}
              className="px-3 py-1.5 rounded border border-line text-sm"
            >
              Reject
            </button>
          </div>
        </div>
      ) : null}

      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-8 space-y-3">
          <IncidentGraph graph={graph} onSelect={setSelected} />
          {selected ? (
            <div className="rounded-lg border border-line p-4 text-[12px]">
              <div className="uppercase tracking-[0.16em] text-zinc-500">{selected.id}</div>
              <div className="mt-1">{selected.label} · {selected.status} · {selected.duration_ms}ms</div>
              <pre className="mt-2 text-[11px] text-zinc-400 overflow-auto max-h-40">
                {JSON.stringify(selected.output || {}, null, 2)}
              </pre>
            </div>
          ) : null}
        </div>
        <div className="col-span-4 space-y-4">
          <Panel title="RCA loop">
            <div className="grid grid-cols-2 gap-2 text-[12px]">
              <div>Iteration {loop.iterations || inc.state?.loop_iterations || 0} / 8</div>
              <div>Hypotheses {hyps.length}</div>
              <div>Rejected {hyps.filter((h) => h.status === "REJECTED").length}</div>
              <div>Confirmed {hyps.filter((h) => h.status === "CONFIRMED").length}</div>
            </div>
            <div className="mt-3 space-y-2">
              {hyps.map((h) => (
                <div key={h.id} className="border border-line rounded p-2">
                  <div className="flex justify-between">
                    <span className="font-mono text-[11px]">{h.id}</span>
                    <Badge status={h.status}>{h.status}</Badge>
                  </div>
                  <div className="text-[12px] mt-1 text-zinc-300">{h.statement}</div>
                  <div className="text-[11px] text-zinc-500 mt-1">{Math.round((h.confidence || 0) * 100)}%</div>
                </div>
              ))}
            </div>
          </Panel>
          <Panel title="Live activity">
            <div className="space-y-2 max-h-72 overflow-auto">
              {events.slice(-30).reverse().map((e, i) => (
                <div key={i} className="text-[11px] border-l-2 border-teal-400/40 pl-2">
                  <span className="text-zinc-500">{fmtTime(e.ts)}</span> {e.message}
                </div>
              ))}
            </div>
          </Panel>
          <Panel title="Evidence">
            <div className="space-y-2 max-h-56 overflow-auto">
              {evidence.map((e) => (
                <div key={e.evidence_id} className="text-[12px]">
                  <span className="font-mono text-teal-300">{e.evidence_id}</span>{" "}
                  <span className="text-zinc-500">{e.type}</span>
                  <div className="text-zinc-300">{e.description}</div>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>

      {report?.markdown ? (
        <section className="rounded-lg border border-line p-4">
          <div className="text-[11px] uppercase tracking-[0.16em] text-zinc-500 mb-2">Incident report</div>
          <pre className="text-[12px] whitespace-pre-wrap text-zinc-300">{report.markdown}</pre>
        </section>
      ) : null}

      <div className="grid grid-cols-4 gap-3 text-[12px] text-zinc-400">
        <Meta label="Tokens" value={inc.tokens_used} />
        <Meta label="Cost" value={`$${(inc.estimated_cost || 0).toFixed(4)}`} />
        <Meta label="Class" value={inc.failure_class || "—"} />
        <Meta label="Risk" value={inc.risk_level || "—"} />
      </div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-line bg-ink-800/60 p-3">
      <div className="text-[11px] uppercase tracking-[0.16em] text-zinc-500 mb-2">{title}</div>
      {children}
    </div>
  );
}

function Meta({ label, value }: { label: string; value: any }) {
  return (
    <div className="rounded border border-line p-3">
      <div className="text-[11px] uppercase tracking-[0.16em] text-zinc-500">{label}</div>
      <div className="mt-1 font-mono">{value}</div>
    </div>
  );
}
