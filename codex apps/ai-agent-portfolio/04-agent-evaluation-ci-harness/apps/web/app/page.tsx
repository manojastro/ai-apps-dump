import Link from 'next/link';
import { RunButton } from './actions';

const api = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004';
async function getDashboard() {
  try { const response = await fetch(`${api}/api/dashboard`, {cache:'no-store'}); return response.ok ? response.json() : null; }
  catch { return null; }
}
const pct = (value: number | undefined) => `${((value || 0) * 100).toFixed(1)}%`;

export default async function Home() {
  const data = await getDashboard();
  const latest = data?.latest_runs?.[0]?.aggregate || {};
  return <>
    <section className="hero"><div><div className="eyebrow">QUALITY CONTROL FOR AI SYSTEMS</div>
      <h1>Ship agents with<br/><em>measurable confidence.</em></h1>
      <p>Evaluate retrieval, answers, tools, latency, and cost against versioned golden datasets. Stop regressions at the pull request.</p>
      <div className="heroActions"><RunButton/><a className="secondary" href="http://localhost:8004/docs">Explore API</a></div>
    </div><div className="scorecard"><div className="scoreTop"><span>LATEST QUALITY SCORE</span><b>GOOD</b></div>
      <strong>{pct(latest.task_success)}</strong><div className="bar"><i style={{width:pct(latest.task_success)}}/></div>
      <dl><div><dt>Groundedness</dt><dd>{pct(latest.groundedness)}</dd></div><div><dt>Citations</dt><dd>{pct(latest.citation_correctness)}</dd></div><div><dt>p95 latency</dt><dd>{latest.latency_p95_ms || '—'} ms</dd></div></dl>
    </div></section>
    <section className="metrics"><article><span>PROJECTS</span><b>{data?.counts?.projects ?? '—'}</b><small>Active workspaces</small></article>
      <article><span>GOLDEN CASES</span><b>{data?.counts?.test_cases ?? '—'}</b><small>60 / 25 / 15 split</small></article>
      <article><span>EXPERIMENT RUNS</span><b>{data?.counts?.runs ?? '—'}</b><small>Fully reproducible</small></article>
      <article><span>AVG COST</span><b>${(latest.cost_per_request_usd || 0).toFixed(4)}</b><small>Per request</small></article></section>
    <section className="grid" id="runs"><article className="panel wide"><div className="panelTitle"><div><span>EXPERIMENTS</span><h2>Recent runs</h2></div><RunButton/></div>
      <table><thead><tr><th>Target</th><th>Task success</th><th>Grounded</th><th>p95</th><th>Cost</th><th></th></tr></thead><tbody>
      {(data?.latest_runs || []).map((run:any)=><tr key={run.id}><td><b>{run.target}</b><small>{run.id.slice(0,8)}</small></td><td className={run.aggregate.task_success > .89?'good':'bad'}>{pct(run.aggregate.task_success)}</td><td>{pct(run.aggregate.groundedness)}</td><td>{run.aggregate.latency_p95_ms} ms</td><td>${run.aggregate.cost_per_request_usd.toFixed(4)}</td><td><Link href={`/runs/${run.id}`}>Inspect →</Link></td></tr>)}
      {!data?.latest_runs?.length && <tr><td colSpan={6}>No runs yet. Start the deterministic evaluation.</td></tr>}</tbody></table>
    </article><article className="panel" id="datasets"><span>GOLDEN DATASET</span><h2>Coverage mix</h2><div className="donut"><b>200</b><small>CASES</small></div><ul className="legend"><li><i className="c1"/>Common <b>120</b></li><li><i className="c2"/>Edge <b>50</b></li><li><i className="c3"/>Unanswerable <b>30</b></li></ul></article></section>
    <section className="ci" id="ci"><div><span>CI QUALITY GATE</span><h2>Regressions do not merge.</h2><p>Absolute thresholds, relative baseline checks, forbidden tool detection, p95 latency, and cost limits produce a machine-readable decision and non-zero failure code.</p></div><pre><code>$ evalharness gate --candidate run.json{`\n`}✓ task_success ≥ 0.90{`\n`}✓ groundedness ≥ 0.85{`\n`}✓ unsafe_tool_calls = 0{`\n`}{`\n`}QUALITY GATE PASSED</code></pre></section>
  </>;
}
