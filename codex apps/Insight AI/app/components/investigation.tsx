"use client";
import { useState } from "react";
import {
  ArrowDownToLine,
  Bot,
  Check,
  ChevronRight,
  Database,
  FileText,
  Play,
  Radio,
  ShieldCheck,
  Terminal,
  X,
} from "lucide-react";
import { api } from "@/lib/productionlens/api";
import { Run } from "@/lib/productionlens/types";
import { useLens } from "./store";
import {
  Badge,
  Dependencies,
  Empty,
  Panel,
  Status,
  relative,
  time,
} from "./ui";

export function Investigation() {
  const s = useLens(),
    run = s.run,
    [tab, setTab] = useState("Timeline");
  return (
    <>
      <div className="pagehead">
        <div>
          <div className="row" style={{ marginBottom: 9 }}>
            <button
              className="iconbtn"
              aria-label="All investigations"
              onClick={() => s.setRun(null)}
            >
              <Bot size={18} />
            </button>
            <span className="mono muted">
              {run
                ? `INC-${run.incident_id.slice(0, 6)}`
                : "Evidence workspace"}
            </span>
            {run && <Status value={run.status} />}
          </div>
          <h1>{run?.incident?.title || "Investigations"}</h1>
          <p className="sub">
            {run
              ? `${run.mode === "replay" ? "Replay — scripted behavior" : "Live agent"} · ${run.incident?.service || "checkout"} · Saved investigation state`
              : "Inspect tool activity, hypotheses, and source evidence."}
          </p>
        </div>
        <div className="row">
          {run?.id && (
            <>
              <a
                className="btn"
                href={`/api/investigations/${run.id}/export`}
                download
              >
                <ArrowDownToLine size={15} />
                Export report
              </a>
              {![
                "completed",
                "failed",
                "inconclusive",
                "cancelled",
                "budget_exceeded",
                "awaiting_review",
              ].includes(run.status) && (
                <button
                  className="btn"
                  disabled={s.busy}
                  onClick={() =>
                    s.act(async () => {
                      await api(`/investigations/${run.id}/cancel`, {});
                      s.setRun(await api(`/investigations/${run.id}`));
                    })
                  }
                >
                  Cancel run
                </button>
              )}
            </>
          )}
          {run?.incident && !run.id && (
            <button
              className="btn primary"
              disabled={s.busy}
              onClick={() => s.start(run.incident!)}
            >
              <Play size={15} />
              Start investigation
            </button>
          )}
        </div>
      </div>
      {!run ? (
        <Panel title="All investigations">
          {s.runs.length ? (
            s.runs.map((r) => (
              <button
                className="incident-row"
                key={r.id}
                onClick={() => s.openRun(r.id)}
              >
                <Bot size={18} className="cyan" />
                <span className="body">
                  <h3>
                    {s.incidents.find((i) => i.id === r.incident_id)?.title ||
                      r.id}
                  </h3>
                  <span className="incident-meta">
                    {relative(r.created_at)}
                    <Badge>{r.mode}</Badge>
                  </span>
                </span>
                <Status value={r.status} />
              </button>
            ))
          ) : (
            <Empty
              title="No investigations yet"
              description="Start with an existing incident or create a new one."
            >
              <button
                className="btn primary"
                onClick={() => s.setCreating(true)}
              >
                New investigation
              </button>
            </Empty>
          )}
        </Panel>
      ) : !run.id ? (
        <div className="columns">
          <Panel title="Incident context">
            <div className="panel-body">
              <p>{run.incident?.description}</p>
              <div className="callout info mt">
                Start this investigation to collect metrics, traces, logs and
                deployment history. No diagnosis has been generated.
              </div>
            </div>
          </Panel>
          <Panel title="Service dependencies">
            <Dependencies />
          </Panel>
        </div>
      ) : (
        <>
          <div className="tabs">
            {["Timeline", "Evidence", "Hypotheses", "Tool activity"].map(
              (t) => (
                <button
                  key={t}
                  className={`tab ${tab === t ? "active" : ""}`}
                  onClick={() => setTab(t)}
                >
                  {t}
                  {t === "Evidence" && ` (${run.evidence?.length || 0})`}
                </button>
              ),
            )}
          </div>
          <div className="columns">
            <div className="stack">
              {run.state.error && (
                <div className="callout warn">{run.state.error}</div>
              )}
              {tab === "Timeline" && (
                <>
                  <Panel
                    title="Investigation timeline"
                    extra={
                      <Badge tone="info">
                        <Radio size={11} />
                        Persisted events
                      </Badge>
                    }
                  >
                    <div className="timeline">
                      {run.events?.map((e) => (
                        <div className="timeline-item" key={e.id}>
                          <span className="timeline-marker">
                            {e.kind === "tool" ? (
                              <Terminal size={11} />
                            ) : (
                              <Check size={11} />
                            )}
                          </span>
                          <div>
                            <div className="row between">
                              <h3>{e.kind.replaceAll("_", " ")}</h3>
                              <small>{time(e.created_at)}</small>
                            </div>
                            <p>{e.message}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Panel>
                  {run.state.diagnosis && (
                    <Panel
                      title="Most supported explanation"
                      extra={<Status value={run.state.diagnosis.confidence} />}
                    >
                      <div className="panel-body">
                        <p>{run.state.diagnosis.explanation}</p>
                        <p className="sub">
                          Inference based on the referenced observations. Model
                          agreement is not independent evidence.
                        </p>
                        <div className="row mt" style={{ flexWrap: "wrap" }}>
                          {run.state.diagnosis.evidence_ids.map((id) => (
                            <button
                              className="btn"
                              key={id}
                              onClick={() =>
                                s.setEvidence(
                                  run.evidence?.find((e) => e.id === id) ||
                                    null,
                                )
                              }
                            >
                              <FileText size={13} />
                              {
                                run.evidence?.find((e) => e.id === id)
                                  ?.source_type
                              }{" "}
                              · {id.slice(0, 6)}
                            </button>
                          ))}
                        </div>
                      </div>
                    </Panel>
                  )}
                </>
              )}
              {tab === "Evidence" && (
                <div className="evidence-grid">
                  {run.evidence?.map((e) => (
                    <button
                      className="evidence-card"
                      key={e.id}
                      onClick={() => s.setEvidence(e)}
                    >
                      <div className="row between">
                        <span className="row cyan">
                          <Database size={15} />
                          {e.source_type}
                        </span>
                        <Badge tone={e.stale || e.truncated ? "warn" : "good"}>
                          {e.stale
                            ? "Stale"
                            : e.truncated
                              ? "Truncated"
                              : "Current snapshot"}
                        </Badge>
                      </div>
                      <p style={{ fontSize: 12 }}>{e.summary}</p>
                      <span className="mono muted">
                        {e.id.slice(0, 8)} · {time(e.observed_at)}
                      </span>
                    </button>
                  ))}
                </div>
              )}
              {tab === "Hypotheses" && (
                <Panel title="Hypotheses and uncertainty">
                  {run.state.diagnosis ? (
                    <div className="panel-body">
                      <Status value={run.state.diagnosis.confidence} />
                      <h2 style={{ margin: "15px 0 8px" }}>
                        {run.state.diagnosis.category.replaceAll("_", " ")}
                      </h2>
                      <p className="sub">{run.state.diagnosis.explanation}</p>
                      <div className="eyeline" />
                      <h3>Alternative explanations</h3>
                      {run.state.diagnosis.alternatives.map((a) => (
                        <p className="sub" key={a}>
                          {a}
                        </p>
                      ))}
                      <div className="eyeline" />
                      <h3>Missing information</h3>
                      {run.state.diagnosis.missing.length ? (
                        run.state.diagnosis.missing.map((m) => (
                          <p className="sub" key={m}>
                            {m}
                          </p>
                        ))
                      ) : (
                        <p className="sub">
                          No missing fields identified by the scripted rules.
                          Replay support does not establish a real incident
                          cause.
                        </p>
                      )}
                    </div>
                  ) : (
                    <Empty
                      title="Collecting evidence"
                      description="Hypotheses will appear when the worker has observations to assess."
                    />
                  )}
                </Panel>
              )}
              {tab === "Tool activity" && (
                <Panel title="Tool execution history">
                  <div className="panel-body">
                    {run.state.tools?.map((t, i) => (
                      <details
                        key={`${t.tool}-${i}`}
                        style={{
                          padding: "12px 0",
                          borderBottom: "1px solid #253043",
                        }}
                      >
                        <summary style={{ cursor: "pointer" }}>
                          <span className="mono">{t.tool}</span>{" "}
                          <span className="muted">
                            {t.duration_ms} ms · {t.status}
                          </span>
                        </summary>
                        <pre>
                          {JSON.stringify(
                            { inputs: t.inputs, output: t.output },
                            null,
                            2,
                          )}
                        </pre>
                      </details>
                    ))}
                  </div>
                </Panel>
              )}
            </div>
            <div className="stack">
              {run.action && (
                <Panel
                  title="Recovery proposal"
                  extra={<ShieldCheck size={16} className="amber" />}
                >
                  <div className="panel-body">
                    <Status value={run.action.status} />
                    <h3 style={{ marginTop: 15 }}>Reset isolated replay lab</h3>
                    <p className="sub">{run.action.proposal.expected_effect}</p>
                    <button
                      className="btn primary mt"
                      onClick={() => s.setPage("Action review")}
                    >
                      <ShieldCheck size={14} />
                      Review exact action
                    </button>
                  </div>
                </Panel>
              )}
              <Panel title="Run budget">
                <div className="panel-body">
                  <div className="row between">
                    <span className="muted">Tool calls</span>
                    <span>
                      {run.state.budget?.tool_calls || 0} /{" "}
                      {run.state.budget?.tool_limit ?? 12}
                    </span>
                  </div>
                  <div className="progress">
                    <span
                      style={{
                        width: `${Math.min(100, ((run.state.budget?.tool_calls || 0) / (run.state.budget?.tool_limit || 12)) * 100)}%`,
                      }}
                    />
                  </div>
                  <div className="row between">
                    <span className="muted">Model calls</span>
                    <span>{run.state.budget?.model_calls || 0}</span>
                  </div>
                  <div className="row between mt">
                    <span className="muted">Cost</span>
                    <span className="muted">Unknown / not billed</span>
                  </div>
                </div>
              </Panel>
              <Panel title="Affected dependencies">
                <Dependencies />
              </Panel>
            </div>
          </div>
        </>
      )}
    </>
  );
}

export function ActionReview() {
  const s = useLens(),
    run = s.run,
    pending = s.runs.filter((r) => r.status === "awaiting_review"),
    action = run?.action;
  const allowed = s.user && ["administrator", "reviewer"].includes(s.user.role);
  return (
    <>
      <div className="pagehead">
        <div>
          <h1>Action review</h1>
          <p className="sub">
            Authorize an exact operation, then verify its observed effect.
          </p>
        </div>
        <Badge tone="warn">
          <ShieldCheck size={13} />
          {pending.length} awaiting review
        </Badge>
      </div>
      {action && run ? (
        <div className="columns">
          <Panel
            title="Exact recovery action"
            extra={<Status value={action.status} />}
          >
            <div className="panel-body">
              <dl className="detail-list">
                <dt>Operation</dt>
                <dd className="mono">{action.proposal.operation}</dd>
                <dt>Target</dt>
                <dd>{action.proposal.target}</dd>
                <dt>Parameters</dt>
                <dd className="mono">
                  {JSON.stringify(action.proposal.parameters)}
                </dd>
                <dt>Expected effect</dt>
                <dd>{action.proposal.expected_effect}</dd>
                <dt>Risk</dt>
                <dd>{action.proposal.risk}</dd>
                <dt>Preconditions</dt>
                <dd>
                  {action.proposal.preconditions.map((p) => (
                    <p key={p}>{p}</p>
                  ))}
                </dd>
                <dt>Reset procedure</dt>
                <dd>{action.proposal.rollback}</dd>
                <dt>Expiry</dt>
                <dd>{new Date(action.expires_at * 1000).toLocaleString()}</dd>
                <dt>Action hash</dt>
                <dd className="mono">{action.digest}</dd>
              </dl>
              <div className="eyeline" />
              <h3>Supporting evidence</h3>
              <div className="row mt" style={{ flexWrap: "wrap" }}>
                {action.proposal.evidence_ids.map((id) => (
                  <button
                    className="btn"
                    key={id}
                    onClick={() =>
                      s.setEvidence(
                        run.evidence?.find((e) => e.id === id) || null,
                      )
                    }
                  >
                    <FileText size={13} />
                    {id.slice(0, 8)}
                  </button>
                ))}
              </div>
              {action.status === "pending" && (
                <div className="row mt">
                  <button
                    className="btn primary"
                    disabled={s.busy || !allowed}
                    onClick={() =>
                      s.act(async () => {
                        await api(`/actions/${action.id}/approve`, {
                          action_hash: action.digest,
                        });
                        s.setRun(await api(`/investigations/${run.id}`));
                      })
                    }
                  >
                    <Check size={15} />
                    Approve exact action
                  </button>
                  <button
                    className="btn danger"
                    disabled={s.busy || !allowed}
                    onClick={() =>
                      s.act(async () => {
                        await api(`/actions/${action.id}/reject`, {
                          action_hash: action.digest,
                        });
                        s.setRun(await api(`/investigations/${run.id}`));
                      })
                    }
                  >
                    <X size={15} />
                    Reject action
                  </button>
                </div>
              )}
              {action.result.error && (
                <div className="callout warn mt">{action.result.error}</div>
              )}
              {run.state.recovery && (
                <div className="callout info mt">
                  <b>
                    {run.state.recovery.verified
                      ? "Replay recovery verified"
                      : "Recovery not verified"}
                  </b>
                  <p>{run.state.recovery.measurement}</p>
                  <p>
                    {run.state.recovery.after.samples} requests · error rate{" "}
                    {(run.state.recovery.before.error_rate * 100).toFixed(1)}% →{" "}
                    {(run.state.recovery.after.error_rate * 100).toFixed(1)}% ·
                    p95 {run.state.recovery.before.p95_ms}ms →{" "}
                    {run.state.recovery.after.p95_ms}ms
                  </p>
                </div>
              )}
            </div>
          </Panel>
          <div className="stack">
            <div className="callout info">
              <ShieldCheck size={22} style={{ marginBottom: 10 }} />
              <p>
                Approval is bound to this hash and these parameters. The
                executor checks the demo revision and expiry again before
                changing state.
              </p>
            </div>
            <button className="btn" onClick={() => s.setPage("Investigations")}>
              Back to investigation
            </button>
          </div>
        </div>
      ) : (
        <Panel title="Review queue">
          {pending.length ? (
            pending.map((r) => (
              <button
                className="incident-row"
                key={r.id}
                onClick={() =>
                  s.act(async () => {
                    s.setRun(await api<Run>(`/investigations/${r.id}`));
                  })
                }
              >
                <ShieldCheck size={18} className="amber" />
                <span className="body">
                  <h3>
                    {s.incidents.find((i) => i.id === r.incident_id)?.title}
                  </h3>
                  <p className="sub">Proposed reset · replay lab only</p>
                </span>
                <ChevronRight size={16} />
              </button>
            ))
          ) : (
            <Empty
              title="No actions awaiting review"
              description="Supported replay investigations can propose a recovery action. No operation runs without a review."
            />
          )}
        </Panel>
      )}
    </>
  );
}
