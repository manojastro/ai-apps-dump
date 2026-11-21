export function Badge({ value }: { value: string }) {
  const tone = ['COMPLETED', 'PASSED', 'PASS', 'APPROVE', 'APPROVED', 'LOW'].includes(value) ? 'good'
    : ['FAILED', 'FAIL', 'REJECTED', 'REJECT', 'CRITICAL'].includes(value) ? 'bad'
    : ['WAITING_FOR_HUMAN', 'NEEDS_HUMAN', 'MEDIUM', 'HIGH'].includes(value) ? 'warn' : 'neutral'
  return <span className={`badge ${tone}`}><span className="badge-dot" />{value.replaceAll('_', ' ')}</span>
}
