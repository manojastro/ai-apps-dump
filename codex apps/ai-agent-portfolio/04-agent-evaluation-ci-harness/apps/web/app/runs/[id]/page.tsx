import Link from 'next/link';
const api = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004';
async function getRun(id:string){const r=await fetch(`${api}/api/runs/${id}`,{cache:'no-store'}); return r.ok?r.json():null;}
const pct=(v:number)=>`${(v*100).toFixed(1)}%`;
export default async function RunDetail({params}:{params:{id:string}}){const run=await getRun(params.id); if(!run)return <section className="empty">Run not found.</section>;
 const failed=run.samples.filter((s:any)=>s.metrics.task_success<1||s.violations.length);
 return <><section className="runHead"><div><Link href="/">← Overview</Link><span>EXPERIMENT RUN</span><h1>{run.target}</h1><p>{run.id} · {new Date(run.created_at).toLocaleString()}</p></div><div className="badge">{failed.length?'REGRESSION':'PASS'}</div></section>
 <section className="metrics"><article><span>TASK SUCCESS</span><b>{pct(run.aggregate.task_success)}</b></article><article><span>GROUNDEDNESS</span><b>{pct(run.aggregate.groundedness)}</b></article><article><span>CITATIONS</span><b>{pct(run.aggregate.citation_correctness)}</b></article><article><span>P95 LATENCY</span><b>{run.aggregate.latency_p95_ms}ms</b></article></section>
 <section className="panel detail"><div className="panelTitle"><div><span>FAILURE EXPLORER</span><h2>{failed.length} changed or failed cases</h2></div><small>Judge: {run.judge_config.model}</small></div>
 {failed.length===0?<div className="empty">All {run.samples.length} samples passed. Run in bad mode to exercise the failure explorer.</div>:
 failed.slice(0,100).map((s:any)=><details key={s.case.id}><summary><code>{s.case.id}</code><b>{s.case.user_input}</b><span>{pct(s.metrics.task_success)}</span></summary><div className="caseGrid"><div><small>EXPECTED</small><p>{s.case.expected_answer||'Abstain safely'}</p><small>EXPECTED SOURCES</small><p>{s.case.expected_sources.join(', ')||'None'}</p></div><div><small>ACTUAL</small><p>{s.response.answer}</p><small>CITATIONS</small><p>{s.response.citations.join(', ')||'None'}</p></div><div><small>TOOL TRACE</small><pre>{JSON.stringify(s.response.tool_calls,null,2)}</pre><small>VIOLATIONS</small><p>{s.violations.join(', ')||'None'}</p></div></div></details>)}
 </section></>}
