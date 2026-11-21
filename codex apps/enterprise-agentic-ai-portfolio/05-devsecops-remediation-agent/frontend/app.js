const byId = (id) => document.getElementById(id);
let currentIncident = null;

function esc(value) {
  return String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
}
async function api(path, options={}) {
  const response = await fetch(path, {headers:{'Content-Type':'application/json',...(options.headers||{})}, ...options});
  if (!response.ok) { const body=await response.json().catch(()=>({detail:response.statusText})); throw new Error(body.detail || response.statusText); }
  return response.json();
}
function banner(title, copy, state='') {
  const node=byId('banner'); node.className=`banner ${state}`; node.querySelector('strong').textContent=title; node.querySelector('p').textContent=copy; node.querySelector('.banner-mark').textContent=state==='alert'?'!':'✓';
}
function pct(value){return `${Math.round((value||0)*100)}%`;}
function step(id, complete){byId(id).classList.toggle('complete',complete);}

async function loadSummary(){
  const summary=await api('/api/v1/evaluations/summary');
  byId('investigations').textContent=summary.investigations; byId('validity').textContent=pct(summary.finding_validity); byId('accuracy').textContent=pct(summary.exploitability_accuracy); byId('success').textContent=pct(summary.remediation_success_rate); byId('regressions').textContent=summary.security_regressions+summary.test_regressions;
}
async function loadScenarios(){
  const scenarios=await api('/api/v1/scenarios');
  byId('scenarios').innerHTML=scenarios.map(s=>`<button class="scenario" data-scenario="${esc(s.name)}"><strong>${esc(s.title)}</strong><span>${esc(s.cwe)} · ${esc(s.description)}</span></button>`).join('');
  document.querySelectorAll('[data-scenario]').forEach(button=>button.addEventListener('click',()=>scan(button.dataset.scenario)));
}
async function loadActivity(){
  const rows=await api('/api/v1/activity?limit=12');
  byId('activity-body').innerHTML=rows.length?rows.map(row=>`<tr><td>${esc(new Date(row.timestamp).toLocaleTimeString())}</td><td>${esc(row.actor)}</td><td>${esc(row.action)}</td><td><span class="badge neutral">${esc(row.decision)}</span></td></tr>`).join(''):'<tr><td colspan="4" class="muted">No activity yet.</td></tr>';
}
function render(incident){
  currentIncident=incident; const inv=incident.investigation; const finding=inv.finding; const exploit=inv.exploitability; const proposal=inv.remediation; const risk=inv.release_risk_before;
  byId('risk-score').textContent=risk.score; byId('risk-ring').style.background=`conic-gradient(var(--red) ${risk.score*3.6}deg,#e4e1d9 0)`; byId('release-decision').textContent=risk.decision; byId('release-decision').className='decision danger'; byId('risk-copy').textContent=risk.reasons.join(' · ');
  byId('finding-title').textContent=finding.title; byId('severity').textContent=finding.severity; byId('severity').className='badge danger'; byId('cwe').textContent=finding.cwe; byId('rule').textContent=finding.rule_id; byId('location').textContent=`${finding.file}:${finding.line}`;
  const ev=finding.evidence[0]; byId('evidence').textContent=`${ev.claim}. Source SHA-256: ${ev.value.source_sha256.slice(0,16)}…`;
  byId('exploit-score').textContent=pct(exploit.score); byId('classification').textContent=exploit.classification.replaceAll('_',' '); byId('rationale').textContent=exploit.rationale; byId('preconditions').innerHTML=exploit.preconditions.map(item=>`<span>${esc(item)}</span>`).join('');
  byId('patch-title').textContent=proposal.summary; byId('patch').textContent=proposal.patch_preview; byId('patch-risk').textContent=`${proposal.risk} · APPROVAL REQUIRED`; byId('rollback').textContent=`Blast radius: ${proposal.blast_radius}. Rollback: ${proposal.rollback_plan}.`;
  const reviewable=['AWAITING_APPROVAL','REAPPROVAL_REQUIRED'].includes(incident.status);
  byId('incident-status').textContent=incident.status; byId('approve').disabled=!reviewable; byId('approve').textContent=incident.status==='REAPPROVAL_REQUIRED'?'Reapprove exact bound patch':'Approve with demo reviewer'; byId('remediate').disabled=incident.status!=='APPROVED';
  step('step-assess',true); step('step-approve',['APPROVED','FIXED','VALIDATED'].includes(incident.status)); step('step-patch',['FIXED','VALIDATED'].includes(incident.status)); step('step-validate',incident.status==='VALIDATED');
  if(incident.validation){
    const v=incident.validation.result; const verified=v.passed===true; byId('risk-score').textContent=v.release_risk_after.score; byId('risk-ring').style.background=`conic-gradient(var(--${verified?'lime':'red'}) ${v.release_risk_after.score*3.6}deg,#e4e1d9 0)`; byId('release-decision').textContent=v.release_risk_after.decision; byId('release-decision').className=`decision ${verified?'safe':'danger'}`; byId('risk-copy').textContent=v.release_risk_after.reasons.join(' · ');
    byId('validation').innerHTML=`<strong>${esc(v.summary)}</strong><ul>${Object.entries(v.checks).map(([name,pass])=>`<li class="${pass?'pass':''}">${pass?'✓':'×'} ${esc(name.replaceAll('_',' '))}</li>`).join('')}</ul><small>${v.findings_before} finding → ${v.findings_after} findings</small>`;
  } else { byId('validation').innerHTML='<p class="muted">Awaiting an approved remediation.</p>'; }
}
async function scan(scenario){
  document.querySelectorAll('[data-scenario]').forEach(b=>b.disabled=true); banner('Investigation running',`Scanning the inert ${scenario.replaceAll('_',' ')} fixture…`);
  try{const incident=await api(`/api/v1/scenarios/${scenario}/scan`,{method:'POST'});render(incident);banner('Release blocked',`A ${incident.investigation.finding.severity} finding is awaiting human approval.`,'alert');await Promise.all([loadSummary(),loadActivity()]);}
  catch(error){banner('Investigation failed',error.message,'alert');}
  finally{document.querySelectorAll('[data-scenario]').forEach(b=>b.disabled=false);}
}
byId('approve').addEventListener('click',async()=>{if(!currentIncident)return;try{const incident=await api(`/api/v1/incidents/${currentIncident.incident_id}/approval`,{method:'POST',headers:{'X-API-Key':'forgeguard-local-demo-approver'},body:JSON.stringify({approved:true,reason:'Reviewed exact patch hashes, bounded blast radius, and rollback plan'})});render(incident);banner('Remediation approved','A separately authenticated demo executor can now apply the bound artifact.');await loadActivity();}catch(error){banner('Approval failed',error.message,'alert');}});
byId('remediate').addEventListener('click',async()=>{if(!currentIncident)return;try{const incident=await api(`/api/v1/incidents/${currentIncident.incident_id}/remediate`,{method:'POST',headers:{'X-API-Key':'forgeguard-local-demo-executor'}});render(incident);banner(incident.status==='VALIDATED'?'Fix verified':'Validation failed',incident.validation.result.summary,incident.status==='VALIDATED'?'success':'alert');await Promise.all([loadSummary(),loadActivity()]);}catch(error){banner('Remediation blocked',error.message,'alert');}});
Promise.all([loadScenarios(),loadSummary(),loadActivity()]).catch(error=>banner('API unavailable',error.message,'alert'));
