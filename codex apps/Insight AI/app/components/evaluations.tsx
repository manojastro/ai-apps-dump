"use client";
import { useState } from "react";
import { ArrowDownToLine, Beaker, ChevronRight, Play } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/productionlens/api";
import { CaseResult, Evaluation } from "@/lib/productionlens/types";
import { useLens } from "./store";
import {
  Badge,
  CheckRow,
  Empty,
  Modal,
  Panel,
  Stat,
  Status,
  relative,
} from "./ui";

export function Evaluations() {
  const s = useLens(),
    [candidate, setCandidate] = useState("script-regression"),
    [trials, setTrials] = useState(1),
    [result, setResult] = useState<CaseResult | null>(null);
  const evaluation = s.evaluation,
    selected =
      evaluation || s.evaluations.find((e) => e.status === "completed"),
    metrics = selected?.report?.metrics;
  async function runSuite(caseId?: string) {
    await s.act(async () => {
      const e = await api<Evaluation>("/evaluations", {
        candidate: caseId && selected ? selected.config.candidate : candidate,
        trials: caseId ? 1 : trials,
        case_id: caseId,
      });
      s.setEvaluation({ ...e, results: [] });
      s.setPage("Evaluations");
      setResult(null);
    });
  }
  return (
    <>
      <div className="pagehead">
        <div>
          <h1>
            {s.page === "Evaluations"
              ? "Agent evaluations"
              : "Version comparison"}
          </h1>
          <p className="sub">
            Reproducible cases. Independent assertions. Explicit release policy.
          </p>
        </div>
        <div className="row">
          {selected && (
            <a
              className="btn"
              href={`/api/evaluations/${selected.id}/export`}
              download
            >
              <ArrowDownToLine size={14} />
              Export results
            </a>
          )}
          <button
            className="btn primary"
            disabled={s.busy}
            onClick={() => runSuite()}
          >
            <Play size={14} />
            Run benchmark
          </button>
        </div>
      </div>
      <div className="filters">
        <label className="row">
          Suite
          <select aria-label="Evaluation suite">
            <option>Core benchmark v1 · 48 cases</option>
          </select>
        </label>
        <label className="row">
          Candidate
          <select
            aria-label="Candidate version"
            value={candidate}
            onChange={(e) => setCandidate(e.target.value)}
          >
            <option value="script-regression">
              script-regression · known defect
            </option>
            <option value="script-v1">script-v1 · fixed script</option>
          </select>
        </label>
        <label className="row">
          Trials
          <select
            aria-label="Repeated trials"
            value={trials}
            onChange={(e) => setTrials(Number(e.target.value))}
          >
            <option value={1}>1 trial</option>
            <option value={2}>2 trials</option>
            <option value={3}>3 trials</option>
          </select>
        </label>
      </div>
      <div className="callout info" style={{ marginBottom: 22 }}>
        Deterministic plumbing evaluation. Synthetic scenarios are unreviewed.
        The single-call LLM and iterative live-agent comparisons are not yet
        available in this runner.
      </div>
      {selected && (
        <>
          <div className="stats">
            <Stat
              label="Diagnosis accuracy"
              value={metrics ? `${(metrics.accuracy * 100).toFixed(0)}%` : "—"}
              foot={
                metrics
                  ? `${metrics.correct} / ${metrics.diagnosis_count} diagnosis cases`
                  : "Calculated when the run completes"
              }
            />
            <Stat
              label="Cases executed"
              value={
                metrics
                  ? `${metrics.executed} / ${metrics.total}`
                  : String(evaluation?.results?.length || 0)
              }
              foot="Unexecuted cases never count as passes"
            />
            <Stat
              label="Regressions"
              value={
                <span className="amber">{metrics?.regressions ?? "—"}</span>
              }
              foot="Paired with the fixed-script baseline"
            />
            <Stat
              label="Release decision"
              value={
                <span style={{ fontSize: 18, letterSpacing: 0 }}>
                  {selected.report?.release?.decision.replaceAll("_", " ") ||
                    selected.status}
                </span>
              }
              foot="Versioned project policy v1"
            />
          </div>
          {selected.report?.release && (
            <div
              className={`callout ${selected.report.release.decision === "fail" ? "warn" : "info"}`}
              style={{ marginBottom: 22 }}
            >
              <b>
                {selected.report.release.decision === "fail"
                  ? "Candidate does not meet release policy"
                  : "More evidence is required before release"}
              </b>
              {[
                ...selected.report.release.failures,
                ...selected.report.release.missing,
              ].map((m) => (
                <p key={m}>{m}</p>
              ))}
            </div>
          )}
          {selected.status === "failed" && (
            <div className="callout warn" role="alert">
              <b>Benchmark failed</b>
              <p>
                {selected.report?.error ||
                  "The worker could not complete this benchmark. Inspect the persisted results and run it again."}
              </p>
            </div>
          )}
          {evaluation &&
            !["completed", "cancelled", "failed"].includes(
              evaluation.status,
            ) && (
              <Panel
                title="Benchmark in progress"
                extra={
                  <button
                    className="btn"
                    onClick={() =>
                      s.act(async () => {
                        await api(`/evaluations/${evaluation.id}/cancel`, {});
                        s.setEvaluation(
                          await api(`/evaluations/${evaluation.id}`),
                        );
                      })
                    }
                  >
                    Cancel evaluation
                  </button>
                }
              >
                <div className="panel-body">
                  <div className="row between">
                    <span>
                      Baseline and candidate run in separate agent processes
                    </span>
                    <span>
                      {evaluation.results?.length || 0} /{" "}
                      {(evaluation.config.case_id ? 1 : 48) *
                        evaluation.config.trials}
                    </span>
                  </div>
                  <div className="progress">
                    <span
                      style={{
                        width: `${((evaluation.results?.length || 0) / ((evaluation.config.case_id ? 1 : 48) * evaluation.config.trials)) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              </Panel>
            )}
          {s.page === "Version comparison" && metrics && (
            <Panel
              title="Paired diagnosis quality"
              extra={<Badge>Same incident snapshots</Badge>}
            >
              <div className="panel-body">
                <div className="chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      layout="vertical"
                      data={[
                        {
                          name: "Fixed script v1",
                          accuracy: Math.round(metrics.baseline_accuracy * 100),
                        },
                        {
                          name: selected.config.candidate,
                          accuracy: Math.round(metrics.accuracy * 100),
                        },
                      ]}
                      margin={{ left: 20, right: 25 }}
                    >
                      <CartesianGrid stroke="#27364a" horizontal={false} />
                      <XAxis
                        type="number"
                        domain={[0, 100]}
                        tick={{ fontSize: 11 }}
                        unit="%"
                      />
                      <YAxis
                        type="category"
                        dataKey="name"
                        width={140}
                        tick={{ fontSize: 12 }}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "#152231",
                          border: "1px solid #34465b",
                          borderRadius: 6,
                        }}
                      />
                      <Bar
                        dataKey="accuracy"
                        fill="#63cce1"
                        barSize={24}
                        radius={[0, 4, 4, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </Panel>
          )}
        </>
      )}
      <div className="mt">
        <Panel
          title={evaluation ? "Case results" : "Evaluation history"}
          extra={
            <Badge>
              {evaluation
                ? `${evaluation.results?.length || 0} results`
                : `${s.evaluations.length} runs`}
            </Badge>
          }
        >
          {evaluation?.results?.length ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Case</th>
                    <th>Scenario</th>
                    <th>Baseline</th>
                    <th>Candidate</th>
                    <th>Change</th>
                    <th>Latency</th>
                  </tr>
                </thead>
                <tbody>
                  {evaluation.results.map((r) => (
                    <tr
                      key={r.key}
                      className="clickable"
                      onClick={() => setResult(r)}
                    >
                      <td>
                        <button
                          className="btn ghost"
                          style={{ padding: 0 }}
                          onClick={() => setResult(r)}
                        >
                          {r.case_id}
                        </button>
                      </td>
                      <td>{r.name}</td>
                      <td>
                        <Status
                          value={
                            r.baseline.status !== "completed"
                              ? r.baseline.status
                              : r.baseline.passed
                                ? "pass"
                                : "fail"
                          }
                        />
                      </td>
                      <td>
                        <Status
                          value={
                            r.candidate.status !== "completed"
                              ? r.candidate.status
                              : r.candidate.passed
                                ? "pass"
                                : "fail"
                          }
                        />
                      </td>
                      <td>
                        {r.regression ? (
                          <Badge tone="bad">Regression</Badge>
                        ) : (
                          <span className="muted">—</span>
                        )}
                      </td>
                      <td className="mono">
                        {Math.round(r.candidate.latency_ms)}ms
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : s.evaluations.length ? (
            s.evaluations.map((e) => (
              <button
                className="incident-row"
                key={e.id}
                onClick={() =>
                  s.act(async () => {
                    s.setEvaluation(await api(`/evaluations/${e.id}`));
                    s.setPage("Version comparison");
                  })
                }
              >
                <Beaker size={18} className="cyan" />
                <span className="body">
                  <h3>Core benchmark · {e.config.candidate}</h3>
                  <span className="incident-meta">
                    {relative(e.created_at)} · {e.config.trials} trial(s) ·
                    replay
                  </span>
                </span>
                <Status value={e.status} />
                <ChevronRight size={14} />
              </button>
            ))
          ) : (
            <Empty
              title="Put the agent to the test"
              description="Compare the baseline with a deliberately regressed candidate to see failure inspection and the release policy at work."
            />
          )}
        </Panel>
      </div>
      {result && (
        <Modal
          title={`Failure replay · ${result.case_id}`}
          onClose={() => setResult(null)}
          wide
        >
          <h2>{result.name}</h2>
          <div className="row">
            <Badge>{result.category}</Badge>
            <Badge tone="warn">{result.review_status}</Badge>
            {result.regression && (
              <Badge tone="bad">Candidate regression</Badge>
            )}
          </div>
          <div className="fields">
            <div>
              <h3>Expected by controller</h3>
              <p className="sub">{result.expected.replaceAll("_", " ")}</p>
            </div>
            <div>
              <h3>Candidate diagnosis</h3>
              <p className="sub">
                {result.candidate.output?.diagnosis.category.replaceAll(
                  "_",
                  " ",
                ) || "Not executed"}
              </p>
            </div>
          </div>
          <div>
            {result.candidate.assertions.map((a) => (
              <CheckRow key={a.name} pass={a.passed}>
                {a.name}
              </CheckRow>
            ))}
          </div>
          {result.candidate.note && (
            <div className="callout warn">{result.candidate.note}</div>
          )}
          <details>
            <summary>Intermediate tool calls and outputs</summary>
            <pre>
              {JSON.stringify(result.candidate.output?.tools || [], null, 2)}
            </pre>
          </details>
          <div className="callout info">
            Expected labels are held by the evaluation controller and are not
            passed to the agent.
          </div>
          <button
            className="btn"
            disabled={s.busy}
            onClick={() => runSuite(result.case_id)}
          >
            <Play size={14} />
            Rerun this case
          </button>
        </Modal>
      )}
    </>
  );
}
