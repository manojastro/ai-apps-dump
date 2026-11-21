const state = { selected: null, keys: {viewer: '', approver: '', executor: ''} };
const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value).replace(/[&<>'"]/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));

async function api(path, options = {}) {
  const {role = 'viewer', ...requestOptions} = options;
  const headers = {'Content-Type': 'application/json', ...(requestOptions.headers || {})};
  if (state.keys[role]) headers['X-API-Key'] = state.keys[role];
  const response = await fetch(path, {...requestOptions, headers});
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

function toast(message) {
  const node = $('#toast'); node.textContent = message; node.classList.add('show');
  setTimeout(() => node.classList.remove('show'), 2800);
}

async function loadScenarios() {
  const scenarios = await api('/api/v1/scenarios');
  $('#scenario-list').innerHTML = scenarios.map(item => `
    <button class="scenario" data-scenario="${esc(item.name)}">
      <strong>${esc(item.name.replaceAll('_', ' '))}</strong><span>${esc(item.description)}</span>
    </button>`).join('');
  document.querySelectorAll('.scenario').forEach(button => button.addEventListener('click', () => inject(button.dataset.scenario)));
}

async function inject(scenario) {
  try {
    toast(`Injecting ${scenario.replaceAll('_', ' ')}…`);
    state.selected = await api(`/api/v1/scenarios/${encodeURIComponent(scenario)}/inject`, {method: 'POST'});
    renderDetail(); await refresh(); toast('Investigation completed; approval is required.');
  } catch (error) { toast(error.message); }
}

async function refresh() {
  const [evaluation, incidents] = await Promise.all([api('/api/v1/evaluations/summary'), api('/api/v1/incidents')]);
  $('#accuracy').textContent = `${(evaluation.rca_accuracy * 100).toFixed(0)}%`;
  $('#total').textContent = evaluation.total;
  $('#confidence').textContent = `${(evaluation.mean_confidence * 100).toFixed(0)}%`;
  $('#duration').textContent = `${evaluation.mean_diagnosis_ms.toFixed(2)} ms`;
  $('#mttd').textContent = `${(evaluation.mean_mttd_ms / 1000).toFixed(1)} s`;
  $('#mttr').textContent = evaluation.mean_mttr_ms ? `${(evaluation.mean_mttr_ms / 1000).toFixed(1)} s` : '—';
  $('#updated').textContent = `Updated ${new Date().toLocaleTimeString()}`;
  $('#incident-rows').innerHTML = incidents.length ? incidents.map(item => `
    <tr data-id="${esc(item.incident_id)}"><td>${esc(item.incident_id)}</td><td>${esc(item.scenario.replaceAll('_',' '))}</td>
    <td>${esc(item.root_cause)}</td><td>${(item.confidence * 100).toFixed(0)}%</td><td><span class="badge ${item.status === 'VALIDATED' ? 'ok' : 'warn'}">${esc(item.status)}</span></td></tr>`).join('')
    : '<tr><td colspan="5">No incidents yet. Inject a scenario to begin.</td></tr>';
  document.querySelectorAll('tr[data-id]').forEach(row => row.addEventListener('click', () => selectIncident(row.dataset.id)));
}

async function selectIncident(id) {
  try { state.selected = await api(`/api/v1/incidents/${encodeURIComponent(id)}`); renderDetail(); }
  catch (error) { toast(error.message); }
}

function renderDetail() {
  const item = state.selected; if (!item) return;
  const rca = item.rca; const action = rca.recommended_actions[0];
  $('#empty-detail').hidden = true; $('#incident-detail').hidden = false;
  $('#incident-heading').textContent = item.incident_id;
  $('#incident-status').textContent = item.status; $('#incident-status').className = `badge ${item.status === 'VALIDATED' ? 'ok' : 'warn'}`;
  $('#root-cause').textContent = rca.probable_root_cause.replaceAll('_', ' ');
  $('#root-confidence').textContent = `${(rca.confidence * 100).toFixed(0)}% confidence · ${rca.reasoning_mode}`;
  $('#evidence').innerHTML = rca.evidence.map(e => `<div class="evidence-item"><span>${esc(e.source)}</span><strong>${esc(e.claim)}</strong><code title="${esc(JSON.stringify(e.value))}">${esc(JSON.stringify(e.value))}</code></div>`).join('');
  $('#action').innerHTML = `<strong>${esc(action.summary)}</strong><div class="action-meta"><span>Risk: ${esc(action.risk)}</span><span>Blast radius: ${esc(action.blast_radius)}</span><span>Rollback: ${esc(action.rollback_plan)}</span></div>`;
  renderControls(item);
  const validation = item.validation?.result;
  $('#validation').hidden = !validation;
  if (validation) $('#validation').innerHTML = `<strong>${validation.passed ? '✓ Outcome independently verified' : 'Validation failed'}</strong><div>${esc(validation.summary)}</div><div class="checks">${Object.entries(validation.checks).map(([key, ok]) => `<span>${ok ? '✓' : '×'} ${esc(key.replaceAll('_',' '))}</span>`).join('')}</div>`;
}

function renderControls(item) {
  const controls = $('#controls');
  if (item.status === 'AWAITING_APPROVAL') {
    controls.innerHTML = '<button class="primary" id="approve">Approve bounded action</button><button class="danger" id="reject">Reject</button>';
    $('#approve').onclick = () => decide(true); $('#reject').onclick = () => decide(false);
  } else if (['APPROVED', 'EXECUTION_FAILED', 'VALIDATION_FAILED'].includes(item.status)) {
    const retry = item.status !== 'APPROVED' ? 'Retry exact action & validation' : 'Execute in simulator & validate';
    controls.innerHTML = `<button class="execute" id="execute">${retry}</button>`;
    $('#execute').onclick = execute;
  } else controls.innerHTML = '';
}

async function decide(approved) {
  try {
    state.selected = await api(`/api/v1/incidents/${encodeURIComponent(state.selected.incident_id)}/approval`, {method:'POST', role:'approver', body: JSON.stringify({approved, approved_by:'demo-operator', reason: approved ? 'Evidence and rollback plan reviewed' : 'Operator rejected the proposed change'})});
    renderDetail(); await refresh(); toast(approved ? 'Action approved. Execution remains a separate step.' : 'Action rejected.');
  } catch (error) { toast(error.message); }
}

async function execute() {
  try {
    state.selected = await api(`/api/v1/incidents/${encodeURIComponent(state.selected.incident_id)}/execute`, {method:'POST', role:'executor'});
    renderDetail(); await refresh(); toast('Synthetic action executed and outcome verified.');
  } catch (error) { toast(error.message); }
}

$('#refresh').addEventListener('click', refresh);
$('#apply-keys').addEventListener('click', () => {
  state.keys.viewer = $('#viewer-key').value;
  state.keys.approver = $('#approver-key').value;
  state.keys.executor = $('#executor-key').value;
  Promise.all([loadScenarios(), refresh()]).then(() => toast('Session keys applied in memory.')).catch(error => toast(error.message));
});
Promise.all([loadScenarios(), refresh()]).catch(error => toast(error.message));
