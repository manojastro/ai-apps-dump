"use client";
import { useState, FormEvent } from "react";
import {
  Activity,
  ArrowRight,
  Beaker,
  Bell,
  Bot,
  ChevronDown,
  ChevronRight,
  CircleDot,
  FlaskConical,
  GitCompareArrows,
  LayoutDashboard,
  LogOut,
  Menu,
  Radio,
  Settings2,
  ShieldCheck,
  Unplug,
  X,
  Play,
} from "lucide-react";
import { api, setCsrf } from "@/lib/productionlens/api";
import { Incident, Run, User } from "@/lib/productionlens/types";
import { Store, useLens } from "./components/store";
import { Badge, Modal, Status } from "./components/ui";
import { Dashboard, Incidents } from "./components/dashboard";
import { Investigation, ActionReview } from "./components/investigation";
import { Evaluations } from "./components/evaluations";
import { Admin, DemoLab, faults } from "./components/admin";
import "./productionlens.css";

const navigation = [
  { name: "Overview", icon: LayoutDashboard },
  { name: "Incidents", icon: Activity },
  { name: "Investigations", icon: Bot },
  { name: "Action review", icon: ShieldCheck },
  { name: "Demo lab", icon: FlaskConical },
  { name: "Evaluations", icon: Beaker },
  { name: "Version comparison", icon: GitCompareArrows },
  { name: "Integrations", icon: Unplug },
  { name: "Settings", icon: Settings2 },
];
export default function App() {
  return (
    <Store>
      <Shell />
    </Store>
  );
}
function Shell() {
  const s = useLens(),
    [mobile, setMobile] = useState(false);
  const pending = s.runs.filter((r) => r.status === "awaiting_review").length;
  if (!s.ready)
    return (
      <main className="pl">
        <div className="empty" style={{ paddingTop: "35vh" }}>
          Connecting to ProductionLens…
        </div>
      </main>
    );
  if (!s.user) return <Login />;
  const nav = (from: number, to: number) =>
    navigation.slice(from, to).map(({ name, icon: Icon }) => (
      <button
        key={name}
        className={`navbtn ${s.page === name ? "selected" : ""}`}
        onClick={() => {
          s.navigate(name);
          setMobile(false);
        }}
      >
        <Icon />
        {name}
        {name === "Incidents" && (
          <span className="navcount">{s.incidents.length}</span>
        )}
        {name === "Action review" && pending > 0 && (
          <span className="navcount">{pending}</span>
        )}
      </button>
    ));
  return (
    <main className="pl">
      <aside className={`sidebar ${mobile ? "open" : ""}`}>
        <div className="brand">
          <span className="brandmark">
            <CircleDot size={20} />
          </span>
          <div>
            <b>ProductionLens</b>
            <small>Investigate with evidence.</small>
          </div>
        </div>
        <div className="workspace-chip">
          <span className="square">PL</span>Local workspace
          <ChevronDown size={13} style={{ marginLeft: "auto" }} />
        </div>
        <div className="nav-label">Investigate</div>
        <nav>{nav(0, 5)}</nav>
        <div className="nav-label">Evaluate & release</div>
        <nav>{nav(5, 7)}</nav>
        <div className="nav-label">Workspace</div>
        <nav>{nav(7, 9)}</nav>
        <div className="sidebar-bottom">
          <div className="mode-card">
            <div className="row cyan" style={{ fontSize: 12 }}>
              <Radio size={14} />
              <b>Replay environment</b>
            </div>
            <p>Scripted behavior. No model usage or production connections.</p>
          </div>
          <a className="navbtn" href="/insight">
            <ArrowRight />
            Open InsightAI
          </a>
          <div className="user">
            <span className="avatar">
              {s.user.username.slice(0, 2).toUpperCase()}
            </span>
            <div>
              <h3 style={{ fontSize: 12 }}>{s.user.username}</h3>
              <small className="muted">{s.user.role}</small>
            </div>
            <button
              className="iconbtn"
              aria-label="Sign out"
              style={{ marginLeft: "auto" }}
              onClick={() =>
                s.act(async () => {
                  await api("/auth/logout", {});
                  s.setUser(null);
                })
              }
            >
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>
      <div className="shell">
        <header className="topbar">
          <div className="crumb">
            <button
              className="iconbtn mobile-menu"
              aria-label="Toggle navigation"
              onClick={() => setMobile(!mobile)}
            >
              <Menu size={19} />
            </button>
            <span className="hide-mobile">Workspace</span>
            <ChevronRight size={13} className="hide-mobile" />
            <span style={{ color: "#c9d5e5" }}>{s.page}</span>
          </div>
          <div className="row">
            <Badge tone="info">
              <i className="dot" />
              Replay — scripted behavior
            </Badge>
            <button
              className="iconbtn hide-mobile"
              aria-label="Open pending action reviews"
              onClick={() => s.navigate("Action review")}
            >
              <Bell size={17} />
            </button>
          </div>
        </header>
        <div className="content">
          {s.error && (
            <div className="error" role="alert">
              <span>{s.error}</span>
              <button
                className="iconbtn"
                aria-label="Dismiss error"
                onClick={() => s.setError("")}
              >
                <X size={16} />
              </button>
            </div>
          )}
          {s.notice && (
            <div
              className="callout info"
              role="status"
              style={{ marginBottom: 20 }}
            >
              {s.notice}
            </div>
          )}
          {s.page === "Overview" ? (
            <Dashboard />
          ) : s.page === "Incidents" ? (
            <Incidents />
          ) : s.page === "Investigations" ? (
            <Investigation />
          ) : s.page === "Action review" ? (
            <ActionReview />
          ) : s.page === "Demo lab" ? (
            <DemoLab />
          ) : ["Evaluations", "Version comparison"].includes(s.page) ? (
            <Evaluations />
          ) : (
            <Admin />
          )}
          <div className="footer-note">
            <ShieldCheck size={12} />
            <span>
              ProductionLens · Local workspace · Replay results are synthetic
              and reproducible.
            </span>
          </div>
        </div>
      </div>
      {s.creating && <CreateIncident />}
      {s.evidence && (
        <Modal
          title={`${s.evidence.source_type} evidence`}
          onClose={() => s.setEvidence(null)}
          wide
        >
          <div className="row">
            <Badge tone="info">{s.run?.mode || "replay"}</Badge>
            <Status
              value={
                s.evidence.stale
                  ? "stale"
                  : s.evidence.truncated
                    ? "truncated"
                    : "current"
              }
            />
          </div>
          <p>{s.evidence.summary}</p>
          <dl className="detail-list">
            <dt>Evidence ID</dt>
            <dd className="mono">{s.evidence.id}</dd>
            <dt>Source record</dt>
            <dd className="mono">{s.evidence.source_record_id}</dd>
            <dt>Observed</dt>
            <dd>{new Date(s.evidence.observed_at * 1000).toLocaleString()}</dd>
            <dt>Content hash</dt>
            <dd className="mono">{s.evidence.content_hash}</dd>
          </dl>
          <pre>{JSON.stringify(s.evidence.payload, null, 2)}</pre>
          <div className="callout info">
            Source content is untrusted data. A valid reference proves
            provenance, not that every claim citing it is supported.
          </div>
        </Modal>
      )}
    </main>
  );
}

function CreateIncident() {
  const s = useLens(),
    [title, setTitle] = useState(""),
    [fixture, setFixture] = useState("payment_delay"),
    [mode, setMode] = useState("replay"),
    [severity, setSeverity] = useState("P2"),
    [description, setDescription] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    await s.act(async () => {
      const i = await api<Incident>("/incidents", {
        title,
        description,
        fixture,
        mode,
        severity,
      });
      const r = await api<Run>("/investigations", { incident_id: i.id });
      s.setRun(await api<Run>(`/investigations/${r.id}`));
      s.setCreating(false);
      s.setPage("Investigations");
    });
  }
  return (
    <Modal title="New investigation" onClose={() => s.setCreating(false)}>
      <form className="stack" onSubmit={submit}>
        <p className="muted">
          Create an incident and queue evidence collection in the worker.
        </p>
        <label>
          Incident title
          <input
            autoFocus
            required
            minLength={3}
            maxLength={250}
            placeholder="Checkout latency exceeds the payment deadline"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </label>
        <div className="fields">
          <label>
            Operating mode
            <select value={mode} onChange={(e) => setMode(e.target.value)}>
              <option value="replay">Replay — scripted behavior</option>
              <option value="live">Live — requires a provider</option>
            </select>
          </label>
          <label>
            Severity
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
            >
              <option>P1</option>
              <option>P2</option>
              <option>P3</option>
            </select>
          </label>
        </div>
        {mode === "replay" ? (
          <label>
            Telemetry fixture
            <select
              value={fixture}
              onChange={(e) => setFixture(e.target.value)}
            >
              {faults.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name}
                </option>
              ))}
              <option value="healthy">Healthy baseline</option>
              <option value="missing_evidence">Incomplete evidence</option>
            </select>
          </label>
        ) : (
          <div className="callout warn">
            Live mode requires a server-configured model provider and telemetry
            sources. Missing configuration fails visibly.
          </div>
        )}
        <label>
          Incident context
          <textarea
            value={description}
            maxLength={4000}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Observed symptoms and the affected customer operation"
          />
        </label>
        <div className="modal-footer">
          <button
            type="button"
            className="btn"
            onClick={() => s.setCreating(false)}
          >
            Cancel
          </button>
          <button className="btn primary" disabled={s.busy}>
            <Play size={15} />
            {s.busy ? "Creating…" : "Create & investigate"}
          </button>
        </div>
        {s.error && (
          <div className="callout warn" role="alert">
            {s.error}
          </div>
        )}
      </form>
    </Modal>
  );
}

function Login() {
  const s = useLens(),
    [username, setUsername] = useState("admin"),
    [password, setPassword] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const u = await api<User>("/auth/login", { username, password });
      setCsrf(u.csrf);
      s.setUser(u);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign in failed");
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="pl">
      <div className="login">
        <section className="login-story">
          <div className="brand" style={{ padding: 0 }}>
            <span className="brandmark">
              <CircleDot size={21} />
            </span>
            <b>ProductionLens</b>
          </div>
          <h1>Every diagnosis starts with the evidence.</h1>
          <p>
            Investigate production signals, review recovery actions, and
            evaluate the agent you rely on.
          </p>
          <div className="timeline" style={{ marginTop: 40, maxWidth: 430 }}>
            {[
              "Collect the signal",
              "Connect the evidence",
              "Review the next action",
            ].map((text, i) => (
              <div className="timeline-item" key={text}>
                <span className="timeline-marker">{i + 1}</span>
                <div>
                  <h3>{text}</h3>
                  <p>
                    {
                      [
                        "Metrics, traces, logs and deployment history.",
                        "A supported explanation with clear uncertainty.",
                        "Explicit approval. Verified recovery.",
                      ][i]
                    }
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>
        <section className="login-form">
          <form onSubmit={submit}>
            <ShieldCheck
              size={27}
              className="cyan"
              style={{ marginBottom: 25 }}
            />
            <h2>Welcome to your workspace</h2>
            <p className="muted">Sign in to investigate and evaluate.</p>
            {error && (
              <div className="error mt" role="alert">
                {error}
              </div>
            )}
            <label>
              Username
              <input
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>
            <button className="btn primary" disabled={busy}>
              {busy ? "Signing in…" : "Sign in to workspace"}
              <ArrowRight size={16} />
            </button>
            <div className="login-note">
              Local setup generates a unique administrator password:
              <code>.productionlens/admin-password.txt</code>
              <p style={{ marginTop: 15 }}>
                First run:{" "}
                <code style={{ display: "inline" }}>npm run bootstrap</code>
              </p>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}
