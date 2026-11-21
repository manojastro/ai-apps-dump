import { useState } from 'react'
import { LockKeyhole } from 'lucide-react'
import type { WorkflowState } from '../types'

export function ApprovalPanel({ state, busy, onDecision }: { state: WorkflowState; busy: boolean; onDecision: (approved: boolean, actor: string, comment: string) => void }) {
  const [actor, setActor] = useState('')
  const [comment, setComment] = useState('')
  const evidenceOnly = state.interrupts[0]?.kind === 'insufficient_evidence'
  return <section className="panel approval-panel"><div className="icon-heading"><LockKeyhole size={20} /><h2>{evidenceOnly ? 'Manual investigation required' : 'Human approval required'}</h2></div><p>{evidenceOnly ? state.interrupts[0].reason : 'This proposal changes pipeline configuration. Review the candidate and checks before releasing the artifact.'}</p><p className="boundary-note">{state.interrupts[0]?.scope}</p><form onSubmit={e => { e.preventDefault(); onDecision(true, actor, comment) }}><label>Reviewer<input value={actor} onChange={e => setActor(e.target.value)} maxLength={80} required placeholder="Your name" /></label><label>Decision note<textarea value={comment} onChange={e => setComment(e.target.value)} maxLength={2000} required placeholder="Why is this proposal approved or rejected?" rows={3} /></label><div className="button-row"><button type="submit" className="button primary" disabled={busy || !actor.trim() || !comment.trim()}>{evidenceOnly ? 'Acknowledge escalation' : 'Approve artifact'}</button>{!evidenceOnly && <button type="button" className="button danger" disabled={busy || !actor.trim() || !comment.trim()} onClick={() => onDecision(false, actor, comment)}>Reject</button>}</div></form></section>
}
