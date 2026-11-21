import type { IncidentStatus, Timing } from '../types'

const nodes = [
  { id: 'incident_intake', label: 'Incident intake', x: 226, y: 14 },
  { id: 'context_retrieval', label: 'Retrieve context', x: 430, y: 14 },
  { id: 'schema_investigator', label: 'Schema', x: 14, y: 104 },
  { id: 'quality_investigator', label: 'Quality', x: 176, y: 104 },
  { id: 'infrastructure_investigator', label: 'Infrastructure', x: 338, y: 104 },
  { id: 'dependency_investigator', label: 'Dependencies', x: 500, y: 104 },
  { id: 'change_investigator', label: 'Changes', x: 662, y: 104 },
  { id: 'evidence_aggregator', label: 'Combine evidence', x: 226, y: 208 },
  { id: 'root_cause_synthesis', label: 'Root cause', x: 430, y: 208 },
]
export function WorkflowGraph({ timings, current, status, onSelect }: { timings: Timing[]; current: string; status: IncidentStatus; onSelect: (node: string) => void }) {
  const completed = new Set(timings.map(t => t.node))
  return <div className="graph-wrap">
    <svg className="workflow-graph" viewBox="0 0 824 275" aria-label="Five concurrent investigation branches converge into evidence and root cause">
      <defs><marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="#9aaec2" /></marker></defs>
      <g className="graph-lines">
        <path d="M374 36H430" markerEnd="url(#arrow)" />
        <path d="M504 58V79H88M88 79H736" />
        {[88, 250, 412, 574, 736].map(x => <path key={x} d={`M${x} 79V104 M${x} 148V178`} markerEnd="url(#arrow)" />)}
        <path d="M88 178H736 M300 178V208" markerEnd="url(#arrow)" />
        <path d="M374 230H430" markerEnd="url(#arrow)" />
      </g>
      <text x="18" y="69" className="graph-label">Fan-out</text>
      <text x="18" y="199" className="graph-label">Fan-in</text>
      {nodes.map(node => {
        const mode = current === node.id && status === 'RUNNING' ? 'running' : completed.has(node.id) ? 'completed' : 'pending'
        return <g key={node.id} transform={`translate(${node.x},${node.y})`} role="button" tabIndex={0} className={`graph-node ${mode}`} aria-label={`${node.label}: ${mode}`} onClick={() => onSelect(node.id)} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(node.id) } }}>
          <rect width="148" height="44" rx="5" />
          <circle cx="14" cy="22" r="3.5" />
          <text x="26" y="27">{node.label}</text>
        </g>
      })}
    </svg>
    <div className="graph-legend"><span><i className="legend-dot pending" />Pending</span><span><i className="legend-dot running" />Running</span><span><i className="legend-dot completed" />Completed</span><span className="graph-help">Select a node to inspect its execution</span></div>
  </div>
}
