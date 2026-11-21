const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));

async function api(path, options = {}) {
  const response = await fetch(path, {headers: {"Content-Type": "application/json"}, ...options});
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body;
}

function toast(message, error = false) {
  const node = $("#toast"); node.textContent = message; node.className = error ? "show error" : "show";
  setTimeout(() => node.className = "", 2600);
}

function percent(value) { return `${Math.round((value || 0) * 100)}%`; }

async function refresh() {
  const data = await api("/api/v1/dashboard");
  $("#mode").textContent = data.mode.toUpperCase();
  $("#success-rate").textContent = percent(data.fleet.success_rate);
  $("#success-bar").style.width = percent(data.fleet.success_rate);
  $("#cost-task").textContent = `$${Number(data.fleet.cost_per_task).toFixed(4)}`;
  $("#p95").textContent = `${Number(data.fleet.p95_latency_ms).toLocaleString()} ms`;
  $("#tool-accuracy").textContent = percent(data.fleet.tool_accuracy);
  $("#failed").textContent = data.fleet.failed_trajectories;
  $("#loop-rate").textContent = `LOOP RATE ${percent(data.fleet.loop_rate)}`;
  renderIncidents(data.incidents); renderActions(data.actions);
}

function renderIncidents(items) {
  $("#incident-rows").innerHTML = items.length ? items.map((i) => `<tr><td><span class="severity ${escapeHtml(i.severity)}">${escapeHtml(i.severity)}</span></td><td class="mono">${escapeHtml(i.incident_id)}</td><td>${escapeHtml(i.root_cause)}</td><td>${Math.round(i.confidence * 100)}%</td><td>${escapeHtml(i.status)}</td></tr>`).join("") : '<tr><td colspan="5" class="empty">No incidents. Run a fault scenario.</td></tr>';
}

function renderActions(items) {
  $("#action-list").innerHTML = items.length ? items.map((a) => `<div class="action"><h3>${escapeHtml(a.action_type.replaceAll("_", " "))}</h3><div class="action-meta"><span>${escapeHtml(a.risk)}</span><span>•</span><span>${escapeHtml(a.status)}</span><span>•</span><span>${a.required_approval ? "APPROVAL REQUIRED" : "AUTO-ELIGIBLE"}</span></div>${a.status === "PROPOSED" ? `<button data-approve="${escapeHtml(a.action_id)}">Approve</button>` : ""}${a.status === "APPROVED" || (!a.required_approval && a.status === "PROPOSED") ? `<button data-execute="${escapeHtml(a.action_id)}">Execute safe simulation</button>` : ""}</div>`).join("") : '<p class="empty">No remediation actions proposed.</p>';
  document.querySelectorAll("[data-approve]").forEach((button) => button.addEventListener("click", () => approve(button.dataset.approve)));
  document.querySelectorAll("[data-execute]").forEach((button) => button.addEventListener("click", () => execute(button.dataset.execute)));
}

async function runScenario() {
  const button = $("#run-scenario"); button.disabled = true;
  try {
    const result = await api("/api/v1/demo/run", {method: "POST", body: JSON.stringify({scenario: $("#scenario").value, agent_version: "1.0.0"})});
    renderWorkflow(result); await refresh(); toast(`Investigation ${result.incident_id || "passed without incident"}`);
  } catch (error) { toast(error.message, true); } finally { button.disabled = false; }
}

function renderWorkflow(result) {
  $("#run-id").textContent = result.run_id;
  $("#claimed").textContent = result.trace.claimed_outcome.success ? "SUCCESS" : "NOT COMPLETE";
  $("#expected").textContent = "EXISTS · COMPLETE · VERIFIED";
  $("#verified").textContent = result.verified_outcome.success ? "CONFIRMED" : "MISMATCH";
  $("#outcome-badge").textContent = result.verified_outcome.success ? "VERIFIED" : "FAILED";
  $("#outcome-badge").className = `badge ${result.verified_outcome.success ? "pass" : "fail"}`;
  $("#verification-checks").innerHTML = Object.entries(result.verified_outcome.checks).map(([name, pass]) => `<li><span>${escapeHtml(name.replaceAll("_", " "))}</span><b class="${pass ? "yes" : "no"}">${pass ? "PASS" : "FAIL"}</b></li>`).join("");
  $("#rca-confidence").textContent = result.rca ? `${Math.round(result.rca.confidence * 100)}% CONFIDENCE` : "NO INCIDENT";
  $("#rca-summary").textContent = result.rca?.summary || "All acceptance criteria were independently verified.";
  $("#evidence-list").innerHTML = result.rca ? result.rca.evidence.slice(0,4).map((e) => `<div class="evidence"><b>${escapeHtml(e.fact)}</b><span>${escapeHtml(e.source)} · ${escapeHtml(e.evidence_id)}</span></div>`).join("") : "";
  $("#trajectory").innerHTML = result.trace.steps.map((step) => `<div class="step ${step.success ? "" : "failed"}"><small>${String(step.sequence).padStart(2,"0")} / ${escapeHtml(step.kind)}</small><b>${escapeHtml(step.name)}</b><span>${step.latency_ms.toLocaleString()} ms · ${(step.prompt_tokens + step.completion_tokens).toLocaleString()} tok</span></div>`).join("");
}

async function approve(actionId) {
  try { await api(`/api/v1/actions/${actionId}/approval`, {method:"POST", body:JSON.stringify({approver:"local-reviewer", decision:"APPROVED", reason:"Evidence reviewed in local demo"})}); await refresh(); toast("Action approved; execution remains a separate step."); } catch (error) { toast(error.message, true); }
}
async function execute(actionId) {
  try { await api(`/api/v1/actions/${actionId}/execute`, {method:"POST"}); await refresh(); toast("Synthetic policy updated and shadow-validated."); } catch (error) { toast(error.message, true); }
}
async function evaluate() {
  try { const result = await api("/api/v1/evaluations/run", {method:"POST"}); toast(`Evaluator benchmark ${result.passed ? "passed" : "failed"}: recall ${percent(result.metrics.detection_recall)}`); await refresh(); } catch (error) { toast(error.message, true); }
}
async function compare() {
  try {
    const result = await api("/api/v1/regression/compare", {method:"POST", body:JSON.stringify({current_version:"1.0.0", candidate_version:$("#candidate").value})});
    $("#gate-decision").textContent = result.decision; $("#gate-decision").className = `badge ${result.passed ? "pass" : "fail"}`;
    $("#gate-checks").innerHTML = Object.entries(result.checks).map(([name, pass]) => `<div><span>${escapeHtml(name.replaceAll("_", " "))}</span><b class="${pass ? "yes" : "no"}">${pass ? "PASS" : "BLOCK"}</b></div>`).join("");
    toast(`Release gate: ${result.decision}`); await refresh();
  } catch (error) { toast(error.message, true); }
}

$("#run-scenario").addEventListener("click", runScenario);
$("#run-evaluation").addEventListener("click", evaluate);
$("#compare").addEventListener("click", compare);
$("#refresh").addEventListener("click", () => refresh().catch((e) => toast(e.message, true)));
refresh().catch((error) => toast(error.message, true));
