import { ArrowDown, Check, RotateCcw, X } from 'lucide-react'
import type { Attempt } from '../types'
import { Badge } from './Badge'

const show = (value: unknown) => typeof value === 'string' ? value : JSON.stringify(value)

export function LoopPanel({ attempts }: { attempts: Attempt[] }) {
  return <section className="panel loop-panel">
    <div className="section-heading"><div><h2>Remediation loop</h2><p>Each candidate must pass every mandatory check.</p></div><RotateCcw size={18} /></div>
    {!attempts.length && <p className="empty-inline">Candidates and deterministic results appear here after investigation.</p>}
    {attempts.map((attempt, index) => <div key={attempt.number}>
      {index > 0 && <div className="feedback-connector"><ArrowDown size={14} /> Validation feedback returned to planner</div>}
      <article className={`attempt ${attempt.status.toLowerCase()}`}>
        <header><div className="attempt-title"><span className="attempt-icon">{attempt.status === 'PASSED' ? <Check size={16} /> : <X size={16} />}</span><h3>Attempt {attempt.number}</h3></div><Badge value={attempt.status} /></header>
        <p className="candidate-summary">{attempt.candidate.summary}</p>
        <div className="operation-list">{attempt.candidate.operations.map(op => <code key={op}>{op}</code>)}</div>
        {attempt.feedback.length > 0 && <p className="failure-reason">{attempt.feedback[0]}</p>}
        <details><summary>View checks <span>{attempt.validations.filter(v => v.status === 'PASS').length}/{attempt.validations.length} passed</span></summary>
          <div className="table-scroll"><table className="validation-table"><thead><tr><th>Validator</th><th>Result</th><th>Evidence</th></tr></thead><tbody>{attempt.validations.map(check => <tr key={check.validator}><td>{check.validator}</td><td><Badge value={check.status} /></td><td>{check.evidence}<details className="actual-values"><summary>Expected / actual</summary><pre>Expected: {show(check.expected)}{'\n'}Actual: {show(check.actual)}</pre></details></td></tr>)}</tbody></table></div>
        </details>
      </article>
    </div>)}
  </section>
}
