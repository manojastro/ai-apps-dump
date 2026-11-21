import { useCallback, useEffect, useRef, useState } from 'react'
import { Activity, ArrowUpRight, BookOpen, Boxes, CheckCheck, ChevronRight, CircleHelp, FlaskConical, GitFork, LayoutList, LoaderCircle, Play, Plus, RefreshCw, Search, Settings2, ShieldCheck, X } from 'lucide-react'
import { api, streamEvents } from './api'
import { ApprovalPanel } from './components/ApprovalPanel'
import { Badge } from './components/Badge'
import { ArtifactPanel, AuditPanel, EvidencePanel, KnowledgePanel, VerifierPanel } from './components/InvestigationPanels'
import { LoopPanel } from './components/LoopPanel'
import { WorkflowGraph } from './components/WorkflowGraph'
import { scenarios } from './types'
import type { Incident, Scenario, Summary, WorkflowEvent, WorkflowState } from './types'

const seconds = (value?: number) => value == null ? '—' : `${value.toFixed(2)}s`
const tabs = ['Overview', 'Evidence', 'Attempts', 'Context', 'Artifact', 'Audit'] as const
type Tab = typeof tabs[number]

export default function App() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [summary, setSummary] = useState<Summary | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [incident, setIncident] = useState<Incident | null>(null)
  const [state, setState] = useState<WorkflowState | null>(null)
  const [events, setEvents] = useState<WorkflowEvent[]>([])
  const [tab, setTab] = useState<Tab>('Overview')
  const [view, setView] = useState<'incidents' | 'evaluation' | 'runbooks'>('incidents')
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [scenario, setScenario] = useState<Scenario>('schema_drift')
  const [forceFail, setForceFail] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [token, setToken] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [inspectedNode, setInspectedNode] = useState<string | null>(null)
  const refreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const latestSelected = useRef(selectedId)

  const refreshList = useCallback(async () => {
    const [rows, metrics] = await Promise.all([api<Incident[]>('/incidents', token), api<Summary>('/metrics/summary', token)])
    setIncidents(rows); setSummary(metrics)
    setSelectedId(current => current || rows[0]?.id || null)
  }, [token])
  const refreshIncident = useCallback(async (id: string) => {
    const [row, graph, audit] = await Promise.all([api<Incident>(`/incidents/${id}`, token), api<WorkflowState>(`/incidents/${id}/state`, token), api<(WorkflowEvent & { tool: string })[]>(`/incidents/${id}/audit`, token)])
    if (latestSelected.current !== id) return
    setIncident(row); setState(graph); setEvents(audit.map(event => ({ ...event, node: event.tool })))
    setIncidents(rows => rows.map(item => item.id === id ? row : item))
  }, [token])

  useEffect(() => {
    let active = true
    Promise.all([api<Incident[]>('/incidents', token), api<Summary>('/metrics/summary', token)]).then(([rows, metrics]) => {
      if (active) { setIncidents(rows); setSummary(metrics); setSelectedId(current => current || rows[0]?.id || null) }
    }).catch(e => { if (active) setError(String(e.message)) })
    return () => { active = false }
  }, [token])
  useEffect(() => {
    latestSelected.current = selectedId
    if (selectedId) {
      const id = selectedId
      Promise.all([api<Incident>(`/incidents/${id}`, token), api<WorkflowState>(`/incidents/${id}/state`, token), api<(WorkflowEvent & { tool: string })[]>(`/incidents/${id}/audit`, token)]).then(([row, graph, audit]) => {
        if (latestSelected.current === id) { setIncident(row); setState(graph); setEvents(audit.map(event => ({ ...event, node: event.tool }))); setInspectedNode(null) }
      }).catch(e => setError(String(e.message)))
    }
  }, [selectedId, token])
  useEffect(() => {
    if (!selectedId || incident?.status !== 'RUNNING') return
    const controller = new AbortController()
    const schedule = () => {
      if (refreshTimer.current) return
      refreshTimer.current = setTimeout(() => {
        refreshTimer.current = null
        void refreshIncident(selectedId).catch(e => setError(String(e.message)))
      }, 150)
    }
    void streamEvents(selectedId, token, 0, controller.signal, schedule).then(() => {
      if (!controller.signal.aborted) { schedule(); void refreshList().catch(e => setError(String(e.message))) }
    }).catch(e => { if (!controller.signal.aborted) setError(String(e.message)) })
    return () => { controller.abort(); if (refreshTimer.current) { clearTimeout(refreshTimer.current); refreshTimer.current = null } }
  }, [selectedId, incident?.status, token, refreshIncident, refreshList])

  const perform = async (action: () => Promise<void>) => { setBusy(true); setError(''); try { await action() } catch (e) { setError(e instanceof Error ? e.message : 'Request failed') } finally { setBusy(false) } }
  const inject = () => perform(async () => {
    const label = scenarios.find(s => s.value === scenario)!
    const row = await api<Incident>('/incidents', token, { method: 'POST', body: JSON.stringify({ scenario, title: `${label.label} in orders_daily`, demo_force_first_fix_fail: forceFail }) })
    setIncidents(rows => [row, ...rows]); setSelectedId(row.id); latestSelected.current = row.id
    setView('incidents'); setTab('Overview'); setShowCreate(false)
    await api(`/incidents/${row.id}/run`, token, { method: 'POST' })
    await refreshIncident(row.id)
  })
  const decide = (approved: boolean, actor: string, comment: string) => { void perform(async () => {
    if (!selectedId) return
    await api(`/incidents/${selectedId}/${approved ? 'approve' : 'reject'}`, token, { method: 'POST', body: JSON.stringify({ actor, comment }) })
    await refreshIncident(selectedId)
  }) }
  const visibleIncidents = incidents.filter(i => `${i.title} ${i.id} ${i.pipeline_id}`.toLowerCase().includes(search.toLowerCase()) && (filter === 'all' || i.status === filter))
  const timings = state?.values.latency_metrics || []
  const inspected = timings.filter(t => t.node === inspectedNode)
  const attempts = state?.values.attempt_history || []
  const selectedHypothesis = state?.values.selected_hypothesis

  return <div className="app-shell">
    <aside className="sidebar"><a className="brand" href="/" aria-label="RecoveryGraph home"><span className="brand-symbol"><GitFork size={22} /></span><span>RecoveryGraph<small>Pipeline recovery engineering</small></span></a>
      <div className="workspace-label"><span className="environment-dot" />Local workspace<Badge value="DEMO" /></div>
      <nav aria-label="Main navigation"><button className={view === 'incidents' ? 'nav-item active' : 'nav-item'} onClick={() => setView('incidents')}><LayoutList size={18} />Incidents<span>{summary?.total_incidents || 0}</span></button><button className={view === 'evaluation' ? 'nav-item active' : 'nav-item'} onClick={() => setView('evaluation')}><FlaskConical size={18} />Evaluation</button><button className={view === 'runbooks' ? 'nav-item active' : 'nav-item'} onClick={() => setView('runbooks')}><BookOpen size={18} />Retrieved runbooks</button></nav>
      <div className="sidebar-note"><ShieldCheck size={20} /><strong>Verified before release</strong><p>Propose. Test. Reject. Revise.<br />Every recovery leaves evidence.</p></div>
      <div className="sidebar-bottom"><button className="nav-item" onClick={() => setShowSettings(true)}><Settings2 size={17} />Connection settings</button><a className="nav-item" href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer"><CircleHelp size={17} />API reference<ArrowUpRight size={14} /></a><div className="build-label">RecoveryGraph v0.1.0</div></div>
    </aside>
    <div className="main-shell"><header className="topbar"><div className="breadcrumb">Workspace <ChevronRight size={14} /><strong>{view === 'incidents' ? 'Incidents' : view === 'evaluation' ? 'Evaluation' : 'Runbooks'}</strong></div><div className="topbar-state"><span className="environment-dot" />Sandbox only<span className="divider" />No production deployment</div></header>
      <main>
        <div className="page-heading"><div><h1>{view === 'incidents' ? 'Pipeline incidents' : view === 'evaluation' ? 'Golden evaluation' : 'Retrieved runbooks'}</h1><p>{view === 'incidents' ? 'Investigate the failure. Prove the recovery.' : view === 'evaluation' ? 'Measured outcomes from reproducible, labeled incidents.' : 'The supporting context used by the selected investigation.'}</p></div><button className="button primary" onClick={() => setShowCreate(true)}><Plus size={17} />Inject incident</button></div>
        {error && <div className="error-banner" role="alert"><span>{error}</span><button aria-label="Dismiss error" onClick={() => setError('')}><X size={16} /></button></div>}
        {view === 'evaluation' ? <section className="panel evaluation-panel"><h2>Deterministic safety evaluation</h2><p>Known failures, accepted recovery characteristics and deliberately incorrect candidates.</p>{summary?.evaluation ? <><p className="boundary-note">Last measured {new Date(summary.evaluation.created_at).toLocaleString()}</p><table><thead><tr><th>Metric</th><th>Measured value</th></tr></thead><tbody>{Object.entries(summary.evaluation.metrics).map(([key, value]) => <tr key={key}><td>{key.replaceAll('_', ' ')}</td><td className="mono">{Number.isInteger(value) ? value : value.toFixed(4)}</td></tr>)}</tbody></table></> : <div className="empty-inline"><p>No evaluation has been stored in this database yet.</p><code>uv run python -m evals.run --persist</code><p>The command runs the golden fixtures and publishes their measured results here.</p></div>}</section>
        : view === 'runbooks' ? <KnowledgePanel documents={state?.values.retrieved_context || []} /> : <>
          <div className="summary-strip"><span><Activity size={16} /><strong>{summary?.statuses.RUNNING || 0}</strong> investigating</span><span><ShieldCheck size={16} /><strong>{summary?.statuses.COMPLETED || 0}</strong> verified recoveries</span><span><CheckCheck size={16} /><strong>{summary?.attempts.REJECTED || 0}</strong> candidates rejected</span><span><strong>{summary?.statuses.WAITING_FOR_HUMAN || 0}</strong> awaiting approval</span></div>
          <section className="panel incident-register"><div className="register-tools"><div className="search-field"><Search size={16} /><input aria-label="Search incidents" placeholder="Search pipeline, incident or ID…" value={search} onChange={e => setSearch(e.target.value)} /></div><select aria-label="Filter incident status" value={filter} onChange={e => setFilter(e.target.value)}><option value="all">All statuses</option><option value="COMPLETED">Completed</option><option value="RUNNING">Running</option><option value="WAITING_FOR_HUMAN">Awaiting approval</option><option value="FAILED">Failed</option><option value="REJECTED">Rejected</option></select><button className="icon-button" aria-label="Refresh incidents" onClick={() => { void perform(async () => { await refreshList(); if (selectedId) await refreshIncident(selectedId) }) }}><RefreshCw size={16} /></button></div><div className="table-scroll incident-table-wrap"><table className="incident-table"><thead><tr><th>Incident</th><th>Pipeline</th><th>Status</th><th>Attempts</th><th>Created</th><th /></tr></thead><tbody>{visibleIncidents.map(row => <tr key={row.id} className={selectedId === row.id ? 'selected' : ''}><td><button className="incident-link" onClick={() => { setSelectedId(row.id); setTab('Overview') }}>{row.title}</button><span className="incident-id">{row.id.slice(0, 8)}</span></td><td><span className="pipeline-name"><Boxes size={14} />{row.pipeline_id}</span><small>{row.environment}</small></td><td><Badge value={row.status} /></td><td className="numeric">{row.attempt_count}</td><td className="time-cell">{new Date(row.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td><td><ChevronRight size={15} /></td></tr>)}</tbody></table></div>{!visibleIncidents.length && <div className="empty-state"><GitFork size={32} /><h2>{incidents.length ? 'No matching incidents' : 'Start with a broken pipeline'}</h2><p>{incidents.length ? 'Adjust the search or status filter.' : 'Inject a reproducible failure to watch the investigation graph and remediation loop.'}</p>{!incidents.length && <button className="button primary" onClick={() => setShowCreate(true)}><Play size={15} />Run a recovery demonstration</button>}</div>}</section>
          {incident && state && incident.id === selectedId && <section className="investigation"><div className="investigation-heading"><div><div className="investigation-caption">Selected investigation <span className="mono">{incident.id.slice(0, 8)}</span></div><h2>{incident.title}</h2></div><div className="button-row"><Badge value={incident.status} />{incident.status === 'CREATED' && <button className="button primary small" disabled={busy} onClick={() => { void perform(async () => { await api(`/incidents/${incident.id}/run`, token, { method: 'POST' }); await refreshIncident(incident.id) }) }}><Play size={14} />Investigate</button>}</div></div>
            <div className="tabs" role="tablist" aria-label="Investigation sections">{tabs.map(name => <button key={name} role="tab" aria-selected={tab === name} className={tab === name ? 'active' : ''} onClick={() => setTab(name)}>{name}{name === 'Evidence' && <span>{state.values.aggregated_evidence?.length || 0}</span>}{name === 'Attempts' && <span>{attempts.length}</span>}</button>)}</div>
            {incident.failure_reason && <div className="error-banner">{incident.failure_reason}</div>}
            <div className="investigation-content">
              <div className="primary-column">
                {tab === 'Overview' && <><section className="panel graph-panel"><div className="section-heading"><div className="icon-heading"><GitFork size={20} /><div><h2>Investigation graph</h2><p>Five branches. One evidence-backed diagnosis.</p></div></div><span className="live-label">{incident.status === 'RUNNING' ? <LoaderCircle className="spin" size={14} /> : <CheckCheck size={14} />}{timings.length} nodes executed</span></div><WorkflowGraph timings={timings} current={incident.current_stage} status={incident.status} onSelect={setInspectedNode} />{inspectedNode && <div className="node-inspector"><strong>{inspectedNode.replaceAll('_', ' ')}</strong><button aria-label="Close node details" onClick={() => setInspectedNode(null)}><X size={14} /></button><p>{inspected.length ? inspected.map(t => `${seconds(t.duration_seconds)} · ${new Date(t.started_at).toLocaleTimeString()}`).join(' / ') : 'This node has not completed yet.'}</p></div>}</section>{selectedHypothesis && <section className="diagnosis-panel"><div className="diagnosis-marker"><Search size={18} /></div><div><div className="diagnosis-title"><h3>Probable root cause</h3><span>{Math.round(selectedHypothesis.confidence * 100)}% confidence</span></div><p>{selectedHypothesis.summary}</p><div className="evidence-refs">{selectedHypothesis.evidence_ids.map(id => <button key={id} onClick={() => setTab('Evidence')}>{id}</button>)}</div>{selectedHypothesis.contradicting_evidence.length > 0 && <p>Contradicting evidence: {selectedHypothesis.contradicting_evidence.join(', ')}</p>}</div></section>}<LoopPanel attempts={attempts} /></>}
                {tab === 'Evidence' && <EvidencePanel evidence={state.values.aggregated_evidence || []} />}
                {tab === 'Attempts' && <LoopPanel attempts={attempts} />}
                {tab === 'Context' && <KnowledgePanel documents={state.values.retrieved_context || []} />}
                {tab === 'Artifact' && <ArtifactPanel artifact={incident.artifact} />}
                {tab === 'Audit' && <AuditPanel events={events} />}
              </div>
              <aside className="detail-column"><section className="panel outcome-panel"><h2>Recovery outcome</h2><div className="outcome-main"><span className={`outcome-symbol ${incident.status === 'COMPLETED' ? 'success' : ''}`}><ShieldCheck size={28} /></span><strong>{incident.status === 'COMPLETED' ? 'Verified artifact ready' : incident.status === 'WAITING_FOR_HUMAN' ? 'Awaiting human decision' : incident.status === 'RUNNING' ? 'Investigation in progress' : 'Recovery investigation'}</strong><p>{incident.artifact ? 'All mandatory checks passed. Fresh replay confirmed.' : 'Artifacts are withheld until all gates pass.'}</p></div><dl className="metrics-list"><div><dt>Time to diagnosis</dt><dd>{seconds(incident.metrics.time_to_diagnosis_seconds)}</dd></div><div><dt>Workflow duration</dt><dd>{seconds(incident.metrics.workflow_duration_seconds)}</dd></div><div><dt>Parallel investigation</dt><dd>{seconds(incident.metrics.parallel_branch_seconds)}</dd></div><div><dt>Validation results</dt><dd><span className="positive">{incident.metrics.validator_pass_count || 0} pass</span> / <span className="negative">{incident.metrics.validator_fail_count || 0} fail</span></dd></div><div><dt>Model calls</dt><dd>{incident.metrics.llm_calls || 0}</dd></div><div><dt>Input / output tokens</dt><dd>{incident.metrics.input_tokens || 0} / {incident.metrics.output_tokens || 0}</dd></div><div><dt>Estimated model cost</dt><dd>{incident.metrics.estimated_cost_usd == null ? 'Not priced' : `$${incident.metrics.estimated_cost_usd.toFixed(4)}`}</dd></div><div><dt>Risk classification</dt><dd>{state.values.risk_level ? <Badge value={state.values.risk_level} /> : 'Pending'}</dd></div></dl>{incident.artifact && <button className="button secondary full" onClick={() => setTab('Artifact')}>Inspect remediation artifact<ArrowUpRight size={15} /></button>}</section>
                <VerifierPanel verification={state.values.verification_result} />
                {incident.status === 'WAITING_FOR_HUMAN' && <ApprovalPanel state={state} busy={busy} onDecision={decide} />}
                {state.values.human_decision && <section className="panel"><h2>Human decision</h2><Badge value={state.values.human_decision.approved ? 'APPROVED' : 'REJECTED'} /><p>{state.values.human_decision.comment}</p><small>Reviewed by {state.values.human_decision.actor}</small></section>}
                <p className="sandbox-note"><ShieldCheck size={16} />Changes run in an isolated data copy. The final output is a reviewable proposal.</p>
              </aside>
            </div>
          </section>}
        </>}
        <footer className="page-footer"><span>Graph engineering + bounded remediation loops</span><span>Deterministic validation is the release gate</span></footer>
      </main>
    </div>
    {showCreate && <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="inject-title"><header><h2 id="inject-title">Inject a pipeline incident</h2><button className="icon-button" aria-label="Close dialog" onClick={() => setShowCreate(false)}><X size={18} /></button></header><p>Start a reproducible local recovery investigation.</p><label>Failure scenario<select value={scenario} onChange={e => setScenario(e.target.value as Scenario)}>{scenarios.map(s => <option value={s.value} key={s.value}>{s.label}</option>)}</select></label><p className="scenario-description">{scenarios.find(s => s.value === scenario)?.description}</p><label className="checkbox-label"><input type="checkbox" checked={forceFail} onChange={e => setForceFail(e.target.checked)} /><span>Demonstrate a rejected first fix<small>Attempt 1 uses incorrect currency units. Real validators must reject it.</small></span></label><div className="modal-actions"><button className="button secondary" onClick={() => setShowCreate(false)}>Cancel</button><button className="button primary" disabled={busy} onClick={() => void inject()}>{busy ? <LoaderCircle className="spin" size={16} /> : <Play size={16} />}Start investigation</button></div></section></div>}
    {showSettings && <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="settings-title"><header><h2 id="settings-title">Connection settings</h2><button className="icon-button" aria-label="Close settings" onClick={() => setShowSettings(false)}><X size={18} /></button></header><p>The console connects to the backend through the same-origin API proxy.</p><label>API bearer token<input type="password" autoComplete="off" value={token} onChange={e => setToken(e.target.value)} placeholder="Optional for the local demo" /></label><p className="boundary-note">Held in memory for this browser session. Configure API_TOKEN on the backend to require authentication.</p><button className="button primary" onClick={() => { setShowSettings(false); void refreshList().catch(e => setError(String(e.message))) }}>Connect</button></section></div>}
  </div>
}
