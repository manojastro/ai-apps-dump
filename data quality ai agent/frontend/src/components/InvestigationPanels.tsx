import { Download, FileCheck2, ShieldCheck } from 'lucide-react'
import type { Artifact, Evidence, Knowledge, Verification, WorkflowEvent } from '../types'
import { Badge } from './Badge'

export function EvidencePanel({ evidence }: { evidence: Evidence[] }) {
  return <section className="panel"><div className="section-heading"><div><h2>Investigation evidence</h2><p>Observations from five independent, read-only branches.</p></div><span className="count-label">{evidence.length} sources</span></div>
    {!evidence.length && <p className="empty-inline">Run an investigation to gather evidence.</p>}
    <div className="evidence-list">{evidence.map(item => <article className="evidence-item" key={item.id}><div className="evidence-heading"><code>{item.id}</code><span>{item.branch}</span></div><h3>{item.summary}</h3><dl>{Object.entries(item.facts).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</dd></div>)}</dl><p className="source-path">{item.source}</p></article>)}</div>
  </section>
}

export function VerifierPanel({ verification }: { verification?: Verification }) {
  return <section className="panel verifier-panel"><div className="section-heading"><div className="icon-heading"><ShieldCheck size={20} /><h2>Independent verifier</h2></div>{verification && <Badge value={verification.decision} />}</div>
    {!verification ? <p className="empty-inline">Runs only after all ten deterministic validators pass.</p> : <><p>{verification.reason_summary}</p><dl className="verifier-facts"><div><dt>Review confidence</dt><dd>{Math.round(verification.confidence * 100)}%</dd></div><div><dt>Unsupported claims</dt><dd>{verification.unsupported_claims.length}</dd></div><div><dt>Missing checks</dt><dd>{verification.missing_checks.length}</dd></div></dl>{[...verification.unsupported_claims, ...verification.missing_checks, ...verification.risk_findings].map(finding => <p className="finding" key={finding}>{finding}</p>)}</>}
    <p className="boundary-note">Isolated evidence package. No worker conversation or scratchpad.</p>
  </section>
}

export function ArtifactPanel({ artifact }: { artifact: Artifact | null }) {
  const download = () => {
    if (!artifact) return
    const url = URL.createObjectURL(new Blob([artifact.diff], { type: 'text/x-diff' }))
    const link = document.createElement('a'); link.href = url; link.download = artifact.filename; link.click()
    URL.revokeObjectURL(url)
  }
  return <section className="panel"><div className="section-heading"><div className="icon-heading"><FileCheck2 size={20} /><h2>Remediation artifact</h2></div>{artifact && <button className="button secondary small" onClick={download}><Download size={14} />Download diff</button>}</div>
    {!artifact ? <p className="empty-inline">A reviewable artifact is released after validation, verification and any required approval.</p> : <><p>{artifact.title}</p><pre className="diff-view">{artifact.diff}</pre><div className="artifact-meta"><Badge value={artifact.post_validation} /><span>Fresh replay post-validation</span></div><p className="boundary-note">{artifact.instructions}</p><p className="hash">SHA-256 {artifact.sha256}</p><p className="boundary-note">Rollback: {artifact.rollback}</p></>}
  </section>
}

export function KnowledgePanel({ documents }: { documents: Knowledge[] }) {
  return <section className="panel"><div className="section-heading"><div><h2>Retrieved context</h2><p>Filtered by pipeline and environment. Local retrieval uses a deterministic lexical vector baseline.</p></div></div>
    {!documents.length && <p className="empty-inline">Select an investigated incident to view its retrieved runbooks.</p>}
    {documents.map(doc => <article className="knowledge-item" key={doc.id}><code>{doc.id}</code><h3>{doc.title}</h3><p>{doc.content}</p><small>{doc.source_type} · {doc.environment} · version {doc.version} · relevance {doc.score.toFixed(3)}</small></article>)}
  </section>
}

export function AuditPanel({ events }: { events: WorkflowEvent[] }) {
  return <section className="panel"><div className="section-heading"><div><h2>Execution audit</h2><p>Persisted node events, tool calls and human decisions.</p></div><span className="count-label">{events.length} events</span></div><div className="table-scroll"><table><thead><tr><th>Time</th><th>Event</th><th>Node / tool</th></tr></thead><tbody>{events.map(event => <tr key={event.id}><td className="mono">{new Date(event.timestamp).toLocaleTimeString()}</td><td>{event.kind.replaceAll('_', ' ')}</td><td className="mono">{event.node}</td></tr>)}</tbody></table></div></section>
}
