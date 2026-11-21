"use client";
import { useEffect, useState } from "react";
import {
  Bot,
  Clock3,
  Database,
  GitBranch,
  Play,
  Plus,
  RotateCcw,
  Zap,
} from "lucide-react";
import { api } from "@/lib/productionlens/api";
import { Incident } from "@/lib/productionlens/types";
import { useLens } from "./store";
import { Badge, Panel, Status } from "./ui";
export const faults = [
  {
    id: "payment_delay",
    name: "Payment dependency delay",
    icon: Clock3,
    description:
      "Replay checkout timeouts caused by upstream payment latency exceeding its deadline.",
  },
  {
    id: "config_regression",
    name: "Configuration regression",
    icon: GitBranch,
    description:
      "Replay application errors following an incompatible request validation change.",
  },
  {
    id: "pool_exhaustion",
    name: "Connection pool exhaustion",
    icon: Database,
    description:
      "Replay acquisition timeouts and saturated database connections under traffic.",
  },
  {
    id: "cpu_saturation",
    name: "CPU saturation",
    icon: Zap,
    description:
      "Replay elevated CPU utilization, compute latency, and slow checkout responses.",
  },
];
export function DemoLab() {
  const s = useLens();
  return (
    <>
      <div className="pagehead">
        <div>
          <h1>Demo lab</h1>
          <p className="sub">
            Reproduce a signal in an isolated, controlled environment.
          </p>
        </div>
        <button
          className="btn"
          disabled={s.busy || s.user?.role !== "administrator"}
          onClick={() =>
            s.act(async () => {
              s.setDemo(await api("/demo", { operation: "reset" }));
              s.setNotice(
                "Replay lab reset. Existing incident snapshots remain reproducible.",
              );
            })
          }
        >
          <RotateCcw size={14} />
          Reset lab
        </button>
      </div>
      <div className="callout info" style={{ marginBottom: 22 }}>
        <b>Replay controls — synthetic telemetry</b>
        <p>
          These controls load deterministic samples; they do not generate real
          requests or consume CPU. Fault controls are unavailable to the
          investigation agent.
        </p>
      </div>
      <Panel
        title="Replay traffic"
        extra={<Status value={s.demo?.traffic ? "completed" : "idle"} />}
      >
        <div className="panel-body row between" style={{ flexWrap: "wrap" }}>
          <div>
            <h3>{s.demo?.samples || 0} requests in the loaded sample</h3>
            <p className="sub">
              A fixed 240-request snapshot for repeatable local investigation.
            </p>
          </div>
          <button
            className="btn primary"
            disabled={s.busy || s.user?.role !== "administrator"}
            onClick={() =>
              s.act(async () => {
                s.setDemo(await api("/demo", { operation: "traffic" }));
              })
            }
          >
            <Play size={14} />
            Load traffic sample
          </button>
        </div>
      </Panel>
      <div className="fault-grid mt">
        {faults.map((f) => (
          <section className="fault-card" key={f.id}>
            <div className="row between">
              <f.icon size={22} className="cyan" />
              {s.demo?.fault === f.id ? (
                <Badge tone="warn">Active · auto reset 120s</Badge>
              ) : (
                <Badge>Bounded scenario</Badge>
              )}
            </div>
            <h2>{f.name}</h2>
            <p>{f.description}</p>
            <button
              className="btn"
              disabled={s.busy}
              onClick={() =>
                s.act(async () => {
                  if (s.user?.role === "administrator")
                    s.setDemo(
                      await api("/demo", { operation: "fault", fault: f.id }),
                    );
                  const i = await api<Incident>("/incidents", {
                    title: f.name + " in checkout",
                    fixture: f.id,
                    description: "Created by the replay demo controller.",
                  });
                  s.setNotice(
                    `Replay incident created: ${i.title}. Open Incidents to start its investigation.`,
                  );
                })
              }
            >
              <Plus size={14} />
              Create scenario incident
            </button>
          </section>
        ))}
      </div>
    </>
  );
}
export function Admin() {
  const s = useLens(),
    [policy, setPolicy] = useState<Record<string, unknown> | null>(null);
  const { page, setError } = s;
  useEffect(() => {
    if (page === "Settings")
      api<Record<string, unknown>>("/policy")
        .then(setPolicy)
        .catch((e) => setError(e.message));
  }, [page, setError]);
  return s.page === "Integrations" ? (
    <>
      <div className="pagehead">
        <div>
          <h1>Integrations</h1>
          <p className="sub">
            Know where your evidence comes from and what has been verified.
          </p>
        </div>
        <button
          className="btn"
          disabled={s.busy}
          onClick={() =>
            s.act(async () => {
              await s.refresh();
              s.setNotice(
                "Adapter configuration and worker heartbeat refreshed. Live connectivity is not inferred from replay health.",
              );
            })
          }
        >
          <RotateCcw size={14} />
          Refresh health
        </button>
      </div>
      <div className="columns">
        <div className="stack">
          {s.integrations?.sources.map((source) => (
            <Panel
              key={source.name}
              title={source.name}
              extra={<Badge tone="info">Replay adapter</Badge>}
            >
              <div className="panel-body">
                <dl className="detail-list">
                  <dt>Authentication</dt>
                  <dd>{source.authentication}</dd>
                  <dt>Freshness</dt>
                  <dd>{source.freshness}</dd>
                  <dt>Request bounds</dt>
                  <dd>
                    {source.timeout_seconds}s timeout · {source.retries} retries
                    · {source.max_bytes.toLocaleString()} bytes
                  </dd>
                  <dt>Live verification</dt>
                  <dd className="amber">Not verified in this environment</dd>
                </dl>
              </div>
            </Panel>
          ))}
        </div>
        <div className="stack">
          <Panel
            title="Model provider"
            extra={<Bot size={16} className="cyan" />}
          >
            <div className="panel-body">
              <Status
                value={
                  s.integrations?.provider_configured
                    ? "configured"
                    : "not_configured"
                }
              />
              <h3 style={{ marginTop: 15 }}>{s.integrations?.model}</h3>
              <p className="sub">
                Credentials are configured on the server and never returned to
                this browser.
              </p>
              <button
                className="btn mt"
                disabled={s.busy || s.user?.role !== "administrator"}
                onClick={() =>
                  s.act(async () => {
                    const result = await api<{ status: string }>(
                      "/integrations/provider/test",
                      {},
                    );
                    s.setNotice(`Provider test: ${result.status}`);
                  })
                }
              >
                <Zap size={14} />
                Test connection
              </button>
            </div>
          </Panel>
          <Panel title="Worker">
            <div className="panel-body">
              <Status value={s.integrations?.worker || "disconnected"} />
              <p className="sub">
                Persisted jobs are reclaimed after lease expiry. Long
                investigations run outside HTTP handlers.
              </p>
            </div>
          </Panel>
        </div>
      </div>
    </>
  ) : (
    <>
      <div className="pagehead">
        <div>
          <h1>Workspace settings</h1>
          <p className="sub">
            Operating boundaries, release policy, and local configuration.
          </p>
        </div>
        <Badge>{s.user?.role}</Badge>
      </div>
      <div className="columns">
        <div className="stack">
          <Panel title="Release policy v1">
            <div className="panel-body">
              <p className="sub">
                Project thresholds are stored in
                packages/evaluation/policy.json. Maintainers edit this versioned
                file; the evaluation agent cannot change it.
              </p>
              <pre>{JSON.stringify(policy, null, 2)}</pre>
            </div>
          </Panel>
          <Panel title="Provider configuration">
            <div className="panel-body">
              <p className="sub">
                Set backend environment variables before starting the API and
                worker. Do not put provider secrets in browser code.
              </p>
              <pre>
                {
                  "MODEL_API_KEY=<server-only secret>\nMODEL_ID=<configured model>\nMODEL_BASE_URL=https://api.openai.com/v1\nMODEL_ALLOWED_HOSTS=api.openai.com"
                }
              </pre>
              <button
                className="btn mt"
                onClick={() => s.navigate("Integrations")}
              >
                View connection status
              </button>
            </div>
          </Panel>
        </div>
        <div className="stack">
          <div className="callout info">
            <h3>Single organization</h3>
            <p>
              Viewer, investigator, reviewer and administrator permissions apply
              to this workspace. Full multi-tenant isolation is outside this
              release.
            </p>
          </div>
          <div className="callout warn">
            <h3>Audit records</h3>
            <p>
              Ordinary database audit records support inspection. They are not
              tamper-proof storage.
            </p>
          </div>
          <Panel title="Default investigation limits">
            <div className="panel-body">
              <dl className="detail-list">
                <dt>Tools</dt>
                <dd>12 calls</dd>
                <dt>Model</dt>
                <dd>8 calls</dd>
                <dt>Tokens</dt>
                <dd>24,000</dd>
                <dt>Runtime</dt>
                <dd>120 seconds</dd>
                <dt>Approval</dt>
                <dd>15 minutes</dd>
              </dl>
            </div>
          </Panel>
        </div>
      </div>
    </>
  );
}
