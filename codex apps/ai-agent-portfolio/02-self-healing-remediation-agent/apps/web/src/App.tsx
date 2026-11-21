import {useEffect,useState} from 'react'

const API=import.meta.env.VITE_API_URL||'http://localhost:8002'
const headers={'Authorization':'Bearer demo-operator-token','Content-Type':'application/json','X-CSRF-Token':'demo-csrf-token'}
type Incident={id:string;title:string;scenario:string;status:string;risk_tier?:string;created_at:string;snapshot?:any}
type Dashboard={total_incidents:number;active_incidents:number;auto_resolution_rate:number;verified_recovery_rate:number;mttr_seconds:number;actions_blocked:number;rollback_rate:number;failed_recovery_rate:number;top_incident_types:[string,number][]}

async function call(path:string,options:RequestInit={}){const r=await fetch(`${API}${path}`,{...options,headers:{...headers,...(options.headers||{})}});if(!r.ok)throw new Error(`${r.status}: ${(await r.json()).detail||r.statusText}`);return r.json()}
const badge=(status:string)=>status.toLowerCase().replaceAll('_','-')

export default function App(){
 const [incidents,setIncidents]=useState<Incident[]>([]),[dashboard,setDashboard]=useState<Dashboard|null>(null),[selected,setSelected]=useState<any>(null)
 const [scenario,setScenario]=useState('crashloop'),[fail,setFail]=useState(false),[comment,setComment]=useState('Reviewed evidence and rollback plan.'),[busy,setBusy]=useState(false),[error,setError]=useState('')
 const refresh=async()=>{try{const [list,metrics]=await Promise.all([call('/api/incidents'),call('/api/dashboard')]);setIncidents(Array.isArray(list)?list.filter((item:any)=>item&&typeof item.id==='string'):[]);setDashboard(metrics);if(selected?.id){setSelected(await call(`/api/incidents/${selected.id}`))}}catch(e:any){setError(e.message)}}
 useEffect(()=>{refresh();const timer=setInterval(refresh,5000);return()=>clearInterval(timer)},[])
 const open=async(id:string)=>{setSelected(await call(`/api/incidents/${id}`));setError('')}
 const inject=async()=>{setBusy(true);try{const item=await call('/api/incidents',{method:'POST',body:JSON.stringify({scenario,force_verification_failure:fail})});setSelected(item);await refresh()}catch(e:any){setError(e.message)}finally{setBusy(false)}}
 const decide=async(decision:'APPROVED'|'REJECTED')=>{setBusy(true);try{setSelected(await call(`/api/incidents/${selected.id}/approval`,{method:'POST',body:JSON.stringify({decision,comment})}));await refresh()}catch(e:any){setError(e.message)}finally{setBusy(false)}}
 const cards=[['Detected',dashboard?.total_incidents??0],['Active',dashboard?.active_incidents??0],['Auto resolved',`${Math.round((dashboard?.auto_resolution_rate??0)*100)}%`],['Verified',`${Math.round((dashboard?.verified_recovery_rate??0)*100)}%`],['Rollbacks',`${Math.round((dashboard?.rollback_rate??0)*100)}%`],['Policy blocks',dashboard?.actions_blocked??0]]
 return <div className="shell">
  <header><div><span className="eyebrow">AIOPS / SANDBOX CONTROL</span><h1>Sentinel <i>Loop</i></h1></div><div className="cluster"><span className="pulse"/> selfheal-demo <small>memory sandbox</small></div></header>
  <main>
   <section className="hero"><div><p className="kicker">DETECT → DIAGNOSE → REMEDIATE</p><h2>Recovery with<br/><em>guardrails.</em></h2><p>Every action is evidence-linked, risk-tiered, policy checked, reversible, and confined to the demo namespace.</p></div>
    <div className="injector"><label>Inject a certified incident</label><select aria-label="Scenario" value={scenario} onChange={e=>setScenario(e.target.value)}><option value="crashloop">CrashLoopBackOff</option><option value="unhealthy_pod">Unhealthy pod</option><option value="excessive_latency">Excessive latency</option><option value="replica_shortage">Replica shortage</option><option value="bad_deployment">Bad deployment · approval</option><option value="failing_job">Failed scheduled job</option><option value="unsafe_no_remediation">Unsafe remediation · block</option></select><label className="check"><input type="checkbox" checked={fail} onChange={e=>setFail(e.target.checked)}/> Force health-check failure / rollback</label><button onClick={inject} disabled={busy}>Inject &amp; run workflow <span>↗</span></button></div>
   </section>
   {error&&<div className="error">{error}</div>}
   <section className="metrics">{cards.map(([label,value])=><article key={label}><span>{label}</span><strong>{value}</strong></article>)}</section>
   <section className="workbench">
    <div className="queue"><div className="section-title"><div><span>LIVE OPERATIONS</span><h3>Incident queue</h3></div><button className="ghost" onClick={refresh}>Refresh</button></div>
     <div className="table"><div className="tr head"><span>Incident</span><span>Risk</span><span>Status</span><span>Detected</span></div>{incidents.map(i=><button className={`tr ${selected?.id===i.id?'active':''}`} key={i.id} onClick={()=>open(i.id)}><span><b>{i.title}</b><small>{i.id.slice(0,12)}</small></span><span className={`risk ${i.risk_tier||'—'}`}>{i.risk_tier||'—'}</span><span className={`status ${badge(i.status)}`}>{i.status.replaceAll('_',' ')}</span><span>{new Date(i.created_at).toLocaleTimeString()}</span></button>)}</div>
    </div>
    <aside className="detail">{selected?<Detail incident={selected} comment={comment} setComment={setComment} decide={decide} busy={busy}/>:<div className="empty"><div>◎</div><h3>Select an incident</h3><p>Inspect its evidence-linked operational trace.</p></div>}</aside>
   </section>
  </main><footer><span>Sentinel Loop / POC 0.1</span><span>NO RAW SHELL · ALLOWLISTED TOOLS · FULL AUDIT</span></footer>
 </div>
}

function Detail({incident,comment,setComment,decide,busy}:any){const s=incident.snapshot||{};const timeline=incident.audit_events||[];return <div>
 <div className="detail-head"><span className={`status ${badge(incident.status)}`}>{incident.status.replaceAll('_',' ')}</span><h3>{incident.title}</h3><p>{incident.id}</p></div>
 <div className="fact-grid"><div><span>RISK TIER</span><b className={`risk ${incident.risk_tier}`}>{incident.risk_tier||'PENDING'}</b></div><div><span>RUNBOOK</span><b>{incident.runbook?.id||'—'}</b></div><div><span>ACTION</span><b>{s.plan?.action?.replaceAll('_',' ')||'—'}</b></div><div><span>OUTCOME</span><b>{s.outcome?.replaceAll('_',' ')||'—'}</b></div></div>
 {incident.status==='PENDING_APPROVAL'&&<div className="approval"><span>OPERATOR CHECKPOINT</span><h4>Medium-risk change needs approval</h4><p>{s.plan?.rollback?.strategy}. Review evidence and leave an audit comment.</p><textarea aria-label="Approval comment" value={comment} onChange={e=>setComment(e.target.value)}/><div><button disabled={busy} className="reject" onClick={()=>decide('REJECTED')}>Reject</button><button disabled={busy} onClick={()=>decide('APPROVED')}>Approve change</button></div></div>}
 <div className="evidence"><h4>Evidence &amp; decision</h4>{(incident.evidence||[]).map((e:any)=><div key={e.id}><span>{e.kind}</span><p>{e.summary}</p><code>{e.source_ref}</code></div>)}</div>
 <div className="timeline"><h4>Audit timeline</h4>{timeline.map((e:any)=><div key={e.id}><span className="dot"/><div><b>{e.event_type.replaceAll('.',' / ')}</b><small>{e.actor} · {new Date(e.created_at).toLocaleTimeString()}</small></div></div>)}</div>
 </div>}
