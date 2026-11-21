"use client";
import { useState } from "react";
import {
  Activity,
  ArrowRight,
  Beaker,
  Bot,
  ChevronRight,
  FlaskConical,
  GitBranch,
  Network,
  Play,
  Plus,
  Search,
  ShieldCheck,
  Terminal,
} from "lucide-react";
import { Incident } from "@/lib/productionlens/types";
import { useLens } from "./store";
import {
  Badge,
  Dependencies,
  Empty,
  Panel,
  Stat,
  Status,
  relative,
} from "./ui";

export function IncidentRows({ items }: { items: Incident[] }) {
  const s = useLens();
  return (
    <>
      {items.map((i) => (
        <button
          className="incident-row"
          key={i.id}
          onClick={() => {
            const existing = s.runs.find((r) => r.incident_id === i.id);
            if (existing) s.openRun(existing.id);
            else {
              s.setRun({
                id: "",
                incident_id: i.id,
                mode: i.mode,
                status: i.status,
                created_at: i.created_at,
                state: {},
                version: {},
                incident: i,
              });
              s.setPage("Investigations");
            }
          }}
        >
          <span className={`severity ${i.severity.toLowerCase()}`}>
            {i.severity}
          </span>
          <span className="body">
            <h3>{i.title}</h3>
            <span className="incident-meta">
              <span className="mono">INC-{i.id.slice(0, 6)}</span>
              <span>·</span>
              <span>{i.service}</span>
              <Badge>{i.mode}</Badge>
              <span>{relative(i.created_at)}</span>
            </span>
          </span>
          <ChevronRight size={15} className="muted" />
        </button>
      ))}
    </>
  );
}
export function Sources() {
  const s = useLens();
  return (
    <>
      {s.integrations?.sources.map((source, i) => (
        <div className="integration" key={source.name}>
          <span className="integration-icon">
            {i === 0 ? (
              <Activity size={16} />
            ) : i === 1 ? (
              <Network size={16} />
            ) : i === 2 ? (
              <Terminal size={16} />
            ) : (
              <GitBranch size={16} />
            )}
          </span>
          <div>
            <h3 style={{ fontSize: 12 }}>{source.name}</h3>
            <small className="muted">Fixture adapter v1</small>
          </div>
          <Badge tone="info">Replay</Badge>
        </div>
      ))}
    </>
  );
}
export function Dashboard() {
  const s = useLens(),
    pending = s.runs.filter((r) => r.status === "awaiting_review"),
    active = s.incidents.filter(
      (i) => !["resolved", "completed"].includes(i.status),
    ),
    latest = s.evaluations.find((e) => e.status === "completed");
  return (
    <>
      <div className="pagehead">
        <div>
          <h1>Production overview</h1>
          <p className="sub">
            From the first signal to a supported explanation.
          </p>
        </div>
        <div className="row">
          <button className="btn" onClick={() => s.navigate("Demo lab")}>
            <FlaskConical size={15} />
            Open demo lab
          </button>
          <button className="btn primary" onClick={() => s.setCreating(true)}>
            <Plus size={16} />
            New investigation
          </button>
        </div>
      </div>
      <div className="stats">
        <Stat
          label="Open incidents"
          value={String(active.length).padStart(2, "0")}
          foot={`${active.filter((i) => i.severity === "P1").length} critical in replay fixtures`}
          icon={<Activity size={15} />}
        />
        <Stat
          label="Investigations"
          value={String(s.runs.length).padStart(2, "0")}
          foot={`${s.runs.filter((r) => r.status === "completed").length} completed · ${s.runs.filter((r) => r.status === "inconclusive").length} inconclusive`}
          icon={<Bot size={15} />}
        />
        <Stat
          label="Awaiting review"
          value={
            <span className={pending.length ? "amber" : ""}>
              {String(pending.length).padStart(2, "0")}
            </span>
          }
          foot="Exact-action approval required"
          icon={<ShieldCheck size={15} />}
        />
        <Stat
          label="Evaluation runs"
          value={String(s.evaluations.length).padStart(2, "0")}
          foot={
            latest?.report?.release?.decision.replaceAll("_", " ") ||
            "Run a suite to assess a version"
          }
          icon={<Beaker size={15} />}
        />
      </div>
      <div className="columns">
        <div className="stack">
          <Panel
            title="Incident inbox"
            extra={
              <button
                className="btn ghost"
                onClick={() => s.navigate("Incidents")}
              >
                View all
                <ArrowRight size={14} />
              </button>
            }
            note="Seeded incidents and telemetry are explicitly synthetic replay fixtures."
          >
            {s.incidents.length ? (
              <IncidentRows items={s.incidents.slice(0, 4)} />
            ) : (
              <Empty
                title="No incidents yet"
                description="Create a replay incident or open the demo lab to choose a scenario."
              />
            )}
          </Panel>
          <Panel
            title="Investigation activity"
            extra={<Badge>{s.runs.length} runs</Badge>}
          >
            {s.runs.length ? (
              <div className="timeline">
                {s.runs.slice(0, 4).map((r) => (
                  <div className="timeline-item" key={r.id}>
                    <span className="timeline-marker">
                      <Bot size={12} />
                    </span>
                    <div>
                      <div className="row between">
                        <button
                          className="btn ghost"
                          style={{
                            padding: 0,
                            color: "#dce8f5",
                            whiteSpace: "normal",
                            textAlign: "left",
                          }}
                          onClick={() => s.openRun(r.id)}
                        >
                          {s.incidents.find((i) => i.id === r.incident_id)
                            ?.title || "Investigation"}
                        </button>
                        <small>{relative(r.created_at)}</small>
                      </div>
                      <p>
                        {r.state.diagnosis?.explanation ||
                          "The worker is collecting evidence for this incident."}
                      </p>
                      <div style={{ marginTop: 9 }}>
                        <Status value={r.status} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <Empty
                title="Follow the evidence, step by step"
                description="Start an investigation to watch the worker collect telemetry, record tool calls, and prepare findings for review."
              >
                <button
                  className="btn"
                  onClick={() => s.incidents[0] && s.start(s.incidents[0])}
                  disabled={s.busy || !s.incidents.length}
                >
                  <Play size={14} />
                  Investigate latest incident
                </button>
              </Empty>
            )}
          </Panel>
        </div>
        <div className="stack">
          <Panel
            title="Telemetry sources"
            extra={
              <span className="muted" style={{ fontSize: 11 }}>
                4 adapters
              </span>
            }
          >
            <Sources />
            <div className="panel-note">
              <div className="row between">
                <span>Investigation worker</span>
                <span
                  className={
                    s.integrations?.worker === "connected" ? "green" : "amber"
                  }
                >
                  {s.integrations?.worker || "Checking"}
                </span>
              </div>
            </div>
          </Panel>
          <Panel
            title="Demo service topology"
            extra={<Network size={15} className="muted" />}
          >
            <Dependencies />
            <div className="panel-note">
              Declared dependencies · isolated demo scope
            </div>
          </Panel>
          <div className="callout info">
            <div className="row" style={{ marginBottom: 7 }}>
              <ShieldCheck size={16} />
              <b>Evidence before action</b>
            </div>
            Every recovery proposal needs an explicit review. Scripted success
            cannot approve a live agent release.
          </div>
        </div>
      </div>
    </>
  );
}
export function Incidents() {
  const s = useLens(),
    [query, setQuery] = useState(""),
    [status, setStatus] = useState("all"),
    [service, setService] = useState("all");
  const rows = s.incidents.filter(
    (i) =>
      `${i.title} ${i.id} ${i.service}`
        .toLowerCase()
        .includes(query.toLowerCase()) &&
      (status === "all" || i.status === status) &&
      (service === "all" || i.service === service),
  );
  return (
    <>
      <div className="pagehead">
        <div>
          <h1>Incidents</h1>
          <p className="sub">
            Inspect the signal. Preserve the context. Start an investigation.
          </p>
        </div>
        <button className="btn primary" onClick={() => s.setCreating(true)}>
          <Plus size={16} />
          Create incident
        </button>
      </div>
      <div className="filters">
        <div className="search">
          <Search size={16} />
          <input
            aria-label="Search incidents"
            placeholder="Search incidents or services…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <select
          aria-label="Filter incident status"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="all">All statuses</option>
          {Array.from(new Set(s.incidents.map((i) => i.status))).map((v) => (
            <option key={v} value={v}>
              {v.replaceAll("_", " ")}
            </option>
          ))}
        </select>
        <select
          aria-label="Filter service"
          value={service}
          onChange={(e) => setService(e.target.value)}
        >
          <option value="all">All services</option>
          <option>checkout</option>
          <option>payment</option>
          <option>inventory</option>
        </select>
        <span className="muted">{rows.length} incidents</span>
      </div>
      <Panel title="Incident records" extra={<Badge>Persisted records</Badge>}>
        {rows.length ? (
          <IncidentRows items={rows} />
        ) : (
          <Empty
            title="No matching incidents"
            description="Try a different search or status filter."
          />
        )}
      </Panel>
    </>
  );
}
