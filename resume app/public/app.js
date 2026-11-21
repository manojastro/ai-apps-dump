// ================= helpers =================
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s = "") => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtNum = (n) => Number(n).toLocaleString("en-IN");
const store = {
  get(k) { try { return localStorage.getItem(k) || ""; } catch { return ""; } },
  set(k, v) { try { v ? localStorage.setItem(k, v) : localStorage.removeItem(k); } catch {} },
};
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.remove("show"), 2600);
}
// The chosen provider (and model, for OpenAI-compatible providers) travel with every AI request
const currentProvider = () => store.get("cf_provider") || config.defaultProvider || "anthropic";
const authHeaders = () => {
  const h = { "x-provider": currentProvider() };
  if (store.get("cf_key")) h["x-api-key"] = store.get("cf_key");
  if (currentProvider() === "openai" && store.get("cf_model")) h["x-model"] = store.get("cf_model");
  return h;
};

let config = { serverKeys: {} };
let jobs = null;

// ================= navigation =================
function showTab(name) {
  $$(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${name}`));
  $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  history.replaceState(null, "", `#${name}`);
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (name === "trends") renderCharts();
}
document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-tab]");
  if (el) { e.preventDefault(); showTab(el.dataset.tab); }
});

// ================= settings / API key =================
function refreshKeyDot() {
  const on = Boolean(store.get("cf_key")) || Boolean(config.serverKeys?.[currentProvider()]);
  $("#keyDot").classList.toggle("on", on);
  $("#openSettings").title = on ? "AI mode active" : "Demo mode — add an API key";
}
// Update the Settings form for the selected provider
function syncProviderFields() {
  const p = $("#provider").value;
  const openai = p === "openai";
  $("#modelRow").classList.toggle("hidden", !openai);
  $("#apiKey").placeholder = openai ? "sk-apx..." : "sk-ant-...";
  $("#modelName").placeholder = config.models?.openai || "deepseek-v4-flash";
  $("#providerNote").textContent = openai
    ? `Requests go to ${config.openaiHost || "api.apinex.bond"}, a third-party service, including any resume details you enter. Leave Model empty to use ${config.models?.openai || "deepseek-v4-flash"}.`
    : `Uses ${config.models?.anthropic || "Claude"} through Anthropic's API.`;
  const shared = config.serverKeys?.[p];
  $("#serverKeyNote").textContent = shared
    ? `This app has a shared key for this provider, so AI mode works without one, up to ${config.limits?.resumePerHour ?? 5} resumes and ${config.limits?.chatPerHour ?? 30} chat messages per hour. Add your own key for no limits.`
    : config.requireUserKey ? "This app needs your own API key for AI features." : "";
}
$("#provider").onchange = syncProviderFields;
// An APInex key (sk-apx...) means the OpenAI-compatible provider; pick it automatically
$("#apiKey").addEventListener("input", (e) => {
  if (e.target.value.trim().startsWith("sk-apx") && $("#provider").value !== "openai") { $("#provider").value = "openai"; syncProviderFields(); }
  if (e.target.value.trim().startsWith("sk-ant") && $("#provider").value !== "anthropic") { $("#provider").value = "anthropic"; syncProviderFields(); }
});
$("#openSettings").onclick = () => {
  $("#provider").value = currentProvider();
  $("#apiKey").value = store.get("cf_key");
  $("#modelName").value = store.get("cf_model");
  syncProviderFields();
  $("#settings").showModal();
};
$("#saveKey").onclick = () => {
  store.set("cf_provider", $("#provider").value);
  store.set("cf_key", $("#apiKey").value.trim());
  store.set("cf_model", $("#modelName").value.trim());
  refreshKeyDot();
  toast("AI settings saved in this browser");
};
$("#clearKey").onclick = () => { store.set("cf_key", ""); refreshKeyDot(); toast("API key removed"); };

// ================= animated counters =================
function countUp(el, target, { decimals = 0, prefix = "", suffix = "" } = {}) {
  const start = performance.now(), dur = 1200;
  const tick = (now) => {
    const p = Math.min(1, (now - start) / dur), v = target * (1 - Math.pow(1 - p, 3));
    el.textContent = prefix + (decimals ? v.toFixed(decimals) : fmtNum(Math.round(v))) + suffix;
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}
function statCards(container, items) {
  container.innerHTML = items.map((s, i) => `<div class="stat"><div class="num" id="${container.id}-${i}">0</div><div class="lbl">${s.label}</div></div>`).join("");
  items.forEach((s, i) => countUp($(`#${container.id}-${i}`), s.value, s));
}

// ================= JOB TRENDS =================
async function loadJobs() {
  jobs = await fetch("/api/jobs").then((r) => r.json());
  const s = jobs.summary;
  const stats = [
    { label: "Job openings tracked", value: s.totalOpenings, suffix: "+" },
    { label: "Avg. salary (LPA)", value: s.avgSalaryLPA, decimals: 1, prefix: "₹" },
    { label: "Cities covered", value: s.citiesTracked },
    { label: "Domains analysed", value: jobs.domains.length },
    { label: "Remote share", value: s.remoteShare, suffix: "%" },
  ];
  statCards($("#homeStats"), stats);
  statCards($("#kpis"), stats);
  $("#asOf").textContent = jobs.meta.asOf;
  $("#dataNote").textContent = `Fastest growing: ${s.fastestGrowing}. ${jobs.meta.note}`;
  renderList("trendingJobs");
  renderDomains();
  renderCityTable();
}

const LIST_RENDER = {
  trendingJobs: (j) => ({ t: j.role, s: `${fmtNum(j.openings)} openings · ~₹${j.avgSalaryLPA} LPA`, v: `+${j.growth}%`, pct: j.growth / 55 }),
  highPaying: (j) => ({ t: j.role, s: `Salary range`, v: `₹${j.minLPA}–${j.maxLPA} L`, pct: j.maxLPA / 95 }),
  easyEntry: (j) => ({ t: j.role, s: `~${j.learnMonths} months to job-ready · ${fmtNum(j.openings)} openings`, v: `₹${j.fresherLPA} L`, pct: 1 - j.learnMonths / 6 }),
  freshers: (j) => ({ t: j.role, s: `${fmtNum(j.openings)} openings`, v: `₹${j.avgLPA} L`, pct: j.openings / 60000 }),
  experienced: (j) => ({ t: j.role, s: `${fmtNum(j.openings)} openings`, v: `₹${j.avgLPA} L`, pct: j.avgLPA / 55 }),
};
function renderList(key) {
  $$("#listTabs .chip").forEach((c) => c.classList.toggle("active", c.dataset.list === key));
  $("#listBody").innerHTML = jobs[key].map((j, i) => {
    const r = LIST_RENDER[key](j);
    return `<div class="rank" style="animation-delay:${i * 40}ms"><div class="n">${i + 1}</div>
      <div class="r-main"><b>${esc(r.t)}</b><small>${esc(r.s)}</small><div class="bar"><i style="width:${Math.max(8, Math.min(100, r.pct * 100))}%"></i></div></div>
      <div class="val">${esc(r.v)}</div></div>`;
  }).join("");
}
$("#listTabs").onclick = (e) => { const c = e.target.closest(".chip"); if (c) renderList(c.dataset.list); };

function renderDomains() {
  const q = $("#domainSearch").value.toLowerCase();
  const key = $("#domainSort").value;
  const list = jobs.domains
    .filter((d) => !q || d.name.toLowerCase().includes(q) || d.skills.join(" ").toLowerCase().includes(q) || d.roles.join(" ").toLowerCase().includes(q))
    .sort((a, b) => (key === "difficulty" ? a[key] - b[key] : b[key] - a[key]));
  $("#domainGrid").innerHTML = list.map((d) => `
    <article class="card domain">
      <h4>${esc(d.name)} <span class="growth">+${d.growth}%</span></h4>
      <small>${d.roles.map(esc).join(" · ")}</small>
      <div class="meta">
        <div><b>${fmtNum(d.openings)}</b><small>openings</small></div>
        <div><b>₹${d.fresherLPA}L</b><small>fresher</small></div>
        <div><b>₹${d.experiencedLPA}L</b><small>experienced</small></div>
      </div>
      <div class="skill-tags">${d.skills.map((s) => `<span>${esc(s)}</span>`).join("")}</div>
      <div class="diff"><span>Difficulty <span class="pips">${"●".repeat(d.difficulty)}${"○".repeat(5 - d.difficulty)}</span></span>
      <button class="ask-btn" data-ask="Give me a 6-month roadmap to get a job in ${esc(d.name)}">Get a roadmap ›</button></div>
    </article>`).join("") || `<p class="muted">No domains match “${esc(q)}”.</p>`;
}
$("#domainSearch").oninput = renderDomains;
$("#domainSort").onchange = renderDomains;
$("#domainGrid").onclick = (e) => {
  const b = e.target.closest("[data-ask]");
  if (b) { showTab("chat"); sendChat(b.dataset.ask); }
};

function renderCityTable() {
  const rows = [...jobs.cities].sort((a, b) => b.openings - a.openings);
  $("#cityTable").innerHTML = `<thead><tr><th>#</th><th>City</th><th>Openings</th><th>Avg salary</th><th>Growth</th><th>Top domains</th></tr></thead><tbody>${
    rows.map((c, i) => `<tr><td>${i + 1}</td><td><b>${esc(c.name)}</b></td><td>${fmtNum(c.openings)}</td><td>₹${c.avgSalaryLPA} LPA</td><td class="pos">+${c.growth}%</td><td>${c.topDomains.map(esc).join(", ")}</td></tr>`).join("")
  }</tbody>`;
}

let chartsDone = false;
function renderCharts() {
  if (chartsDone || !jobs || !window.Chart) return;
  chartsDone = true;
  const css = getComputedStyle(document.documentElement);
  const v = (n) => css.getPropertyValue(n).trim();
  const ROYAL = v("--royal"), GOLD = v("--gold-deco"), MUTED = v("--muted"), HAIR = v("--hair");
  Chart.defaults.color = MUTED;
  Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
  Chart.defaults.font.size = 11;
  Chart.defaults.borderColor = HAIR;
  const base = (horizontal) => ({
    indexAxis: horizontal ? "y" : "x", responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { backgroundColor: ROYAL, titleColor: v("--bg"), bodyColor: v("--bg"), padding: 10, cornerRadius: 10, displayColors: false } },
    scales: {
      x: { grid: { display: horizontal, drawTicks: false }, border: { display: false }, ticks: { padding: 6 } },
      y: { grid: { display: !horizontal, drawTicks: false }, border: { display: false }, ticks: { padding: 6 } },
    },
    animation: { duration: 1200, easing: "easeOutQuart" },
  });
  // highlight the leader in gold, the rest in royal navy
  const mk = (id, labels, data, horizontal, fmt) => {
    const el = $(id); el.parentElement.style.height = "360px";
    const opts = base(horizontal);
    opts.plugins.tooltip.callbacks = { label: (c) => fmt(c.raw) };
    const colors = data.map((_, i) => (i === 0 ? GOLD : ROYAL));
    new Chart(el.getContext("2d"), { type: "bar", data: { labels, datasets: [{ data, backgroundColor: colors, borderRadius: 6, maxBarThickness: horizontal ? 14 : 22 }] }, options: opts });
  };
  const cities = [...jobs.cities].sort((a, b) => b.openings - a.openings);
  mk("#cityChart", cities.map((c) => c.name), cities.map((c) => c.openings), false, (x) => `${fmtNum(x)} openings`);
  const top = [...jobs.domains].sort((a, b) => b.openings - a.openings).slice(0, 10);
  mk("#domainChart", top.map((d) => d.name), top.map((d) => d.openings), true, (x) => `${fmtNum(x)} openings`);
  const pay = [...jobs.domains].sort((a, b) => b.avgSalaryLPA - a.avgSalaryLPA).slice(0, 10);
  mk("#payChart", pay.map((d) => d.name), pay.map((d) => d.avgSalaryLPA), true, (x) => `₹${x} LPA average`);
  const gr = [...jobs.domains].sort((a, b) => b.growth - a.growth).slice(0, 10);
  mk("#growthChart", gr.map((d) => d.name), gr.map((d) => d.growth), false, (x) => `+${x}% year over year`);
}

// ================= RESUME BUILDER =================
let mode = "skills";
let currentResume = null;
$$(".seg-btn").forEach((b) => (b.onclick = () => {
  mode = b.dataset.mode;
  $$(".seg-btn").forEach((x) => x.classList.toggle("active", x === b));
  $$(".mode-upload").forEach((x) => x.classList.toggle("hidden", mode !== "upload"));
  $$(".mode-skills").forEach((x) => x.classList.toggle("hidden", mode !== "skills"));
}));

// Quick-add skill chips: click to append to the skills box, click again to remove
const QUICK_SKILLS = ["Python", "SQL", "Excel", "Power BI", "Java", "JavaScript", "React", "Node.js", "AWS", "Machine Learning", "Data Analysis", "Communication", "Teamwork", "Problem Solving"];
const skillsBox = $("#skillsText");
const skillPresent = (s) => new RegExp(`(^|[^\\w])${s.replace(/[.+]/g, "\\$&")}([^\\w]|$)`, "i").test(skillsBox.value);
function renderSkillChips() {
  $("#skillChips").innerHTML = QUICK_SKILLS.map((s) => `<button type="button" class="skill-chip ${skillPresent(s) ? "added" : ""}" data-skill="${esc(s)}">${skillPresent(s) ? "✓ " : "+ "}${esc(s)}</button>`).join("");
}
$("#skillChips").onclick = (e) => {
  const b = e.target.closest("[data-skill]");
  if (!b) return;
  const s = b.dataset.skill;
  if (skillPresent(s)) {
    skillsBox.value = skillsBox.value
      .split(",").map((x) => x.trim()).filter((x) => x.toLowerCase() !== s.toLowerCase()).join(", ");
  } else {
    const v = skillsBox.value.trim();
    skillsBox.value = v ? `${v.replace(/[,\s]+$/, "")}, ${s}` : s;
  }
  renderSkillChips();
  skillsBox.focus();
};
skillsBox.addEventListener("input", renderSkillChips);
renderSkillChips();

const drop = $("#drop"), fileInput = $("#fileInput");
fileInput.onchange = () => ($("#fileName").textContent = fileInput.files[0] ? `✓ ${fileInput.files[0].name}` : "");
["dragover", "dragenter"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, () => drop.classList.remove("over")));
drop.addEventListener("drop", (e) => {
  e.preventDefault();
  if (e.dataTransfer.files[0]) { fileInput.files = e.dataTransfer.files; fileInput.onchange(); }
});

$("#resumeForm").onsubmit = async (e) => {
  e.preventDefault();
  const form = e.target, msg = $("#formMsg"), btn = $("#genBtn");
  const fd = new FormData(form);
  if (mode === "upload") {
    if (!fileInput.files[0]) { msg.className = "form-msg err"; msg.textContent = "Please choose a resume file to upload."; return; }
  } else {
    fd.delete("resume");
    if (!fd.get("skills").trim()) { msg.className = "form-msg err"; msg.textContent = "Please enter at least a few skills."; return; }
  }
  btn.disabled = true; btn.classList.add("loading");
  msg.className = "form-msg"; msg.textContent = "Crafting your ATS-optimised resume…";
  try {
    const res = await fetch("/api/resume", { method: "POST", body: fd, headers: authHeaders() });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Generation failed");
    currentResume = data.resume;
    saveResume();
    renderResume(currentResume);
    msg.className = "form-msg ok";
    msg.textContent = data.demo ? "Demo resume generated. Add an API key in Settings for full AI rewriting." : "Done! Click any text on the resume to edit it.";
    if (innerWidth < 960) $("#resumePaper").scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    msg.className = "form-msg err"; msg.textContent = err.message;
  } finally {
    btn.disabled = false; btn.classList.remove("loading");
  }
};

// ---- templates ----
const { TEMPLATES, TPL_BASE_CSS, SAMPLE_RESUME } = window.ResumeTemplates;
let templateId = TEMPLATES[store.get("cf_tpl")] ? store.get("cf_tpl") : "classic";
const templateCss = (id) => TPL_BASE_CSS + TEMPLATES[id].css;
const THUMBS = {
  classic: `<i class="t-n"></i><i class="w7"></i><i class="rule"></i><i class="t-h"></i><i class="w9"></i><i class="w8"></i><i class="t-h"></i><i class="w9"></i><i class="w7"></i>`,
  elegant: `<i class="t-n"></i><i class="w7"></i><i class="rule"></i><i class="w9"></i><i class="t-h"></i><i class="w9"></i><i class="w8"></i><i class="t-h"></i><i class="w7"></i>`,
  modern: `<i class="t-n"></i><i class="w7"></i><i class="t-h"></i><i class="w9"></i><i class="w8"></i><i class="t-h"></i><i class="w9"></i><i class="w7"></i>`,
  minimal: `<i class="t-n"></i><i class="w7"></i><i class="rule"></i><i class="t-h"></i><i class="rule"></i><i class="w9"></i><i class="w8"></i><i class="t-h"></i><i class="rule"></i><i class="w9"></i>`,
};
function renderPicker() {
  $("#tplPicker").innerHTML = Object.entries(TEMPLATES).map(([id, t]) => `
    <button type="button" class="tpl-opt ${id === templateId ? "active" : ""}" data-tpl="${id}" role="radio" aria-checked="${id === templateId}" title="${esc(t.desc)}">
      <div class="thumb ${id === "elegant" ? "center" : ""} ${id === "modern" ? "band" : ""}" style="--sw:${t.swatch}">${THUMBS[id]}</div>${esc(t.name)}
    </button>`).join("");
  $("#tplDesc").textContent = TEMPLATES[templateId].desc;
}
$("#tplPicker").onclick = (e) => {
  const b = e.target.closest("[data-tpl]");
  if (!b) return;
  templateId = b.dataset.tpl;
  store.set("cf_tpl", templateId);
  renderPicker();
  renderResume(currentResume || SAMPLE_RESUME, !currentResume);
};
renderPicker();

// ---- saving the resume & on-page edits ----
// The generated resume (including any edits) is kept in this browser so a refresh or a
// template switch never loses work.
function saveResume() {
  if (currentResume) store.set("cf_resume", JSON.stringify(currentResume));
}
function loadSavedResume() {
  try { return JSON.parse(store.get("cf_resume") || "null"); } catch { return null; }
}
// Write `value` into obj at a dotted path like "experience.0.bullets.2"
function setPath(obj, path, value) {
  const keys = path.split(".");
  let o = obj;
  keys.slice(0, -1).forEach((k, i) => {
    if (o[k] == null) o[k] = /^\d+$/.test(keys[i + 1]) ? [] : {};
    o = o[k];
  });
  o[keys[keys.length - 1]] = value;
}
let saveTimer;
$("#resumePaper").addEventListener("input", (e) => {
  const el = e.target.closest("[data-path]");
  if (!el || !currentResume) return; // edits to the sample are not kept
  // textContent, not innerText: innerText applies CSS like text-transform: uppercase
  const text = el.textContent.replace(/\s+/g, " ").trim();
  setPath(currentResume, el.dataset.path, el.dataset.list ? text.split(",").map((s) => s.trim()).filter(Boolean) : text);
  clearTimeout(saveTimer);
  saveTimer = setTimeout(saveResume, 400);
});
// Enter would insert line breaks/divs inside a field; treat it as "done editing" instead
$("#resumePaper").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && e.target.closest("[data-path]")) { e.preventDefault(); e.target.blur(); }
});
// Paste as plain text so formatting from other apps doesn't leak in
$("#resumePaper").addEventListener("paste", (e) => {
  if (!e.target.closest("[data-path]")) return;
  e.preventDefault();
  document.execCommand("insertText", false, (e.clipboardData || window.clipboardData).getData("text/plain"));
});

currentResume = loadSavedResume();
setTimeout(() => (currentResume ? renderResume(currentResume) : renderResume(SAMPLE_RESUME, true)));

function renderResume(r, isSample = false) {
  const paper = $("#resumePaper");
  $("#tplStyle").textContent = templateCss(templateId);
  paper.className = `paper tpl tpl-${templateId}`;
  paper.innerHTML = (isSample ? `<span class="sample-badge">Sample</span>` : "") + TEMPLATES[templateId].render(r);
  if (isSample) paper.querySelectorAll("[contenteditable]").forEach((el) => el.removeAttribute("contenteditable"));
  ["#pdfBtn", "#docBtn", "#copyBtn"].forEach((id) => ($(id).disabled = isSample));

  // ATS score + tips
  const ats = r.ats || {};
  const score = Math.max(0, Math.min(100, Number(ats.score) || 0));
  $("#atsScore").textContent = score || "--";
  const ring = $("#ringFg");
  ring.style.stroke = score >= 80 ? "var(--gold-deco)" : score >= 60 ? "var(--warn)" : "var(--err)";
  requestAnimationFrame(() => ring.setAttribute("stroke-dasharray", `${score},100`));
  const kw = (arr, cls) => (arr || []).filter(Boolean).map((k) => `<span class="kw ${cls}">${esc(k)}</span>`).join("");
  const tips = $("#tipsBox");
  tips.classList.remove("hidden");
  tips.innerHTML = `
    ${ats.tips?.length ? `<h4>Suggestions</h4><ul>${ats.tips.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>` : ""}
    ${ats.matchedKeywords?.length ? `<h4>Keywords matched</h4>${kw(ats.matchedKeywords, "ok")}` : ""}
    ${ats.missingKeywords?.length ? `<h4 style="margin-top:16px">Consider adding</h4>${kw(ats.missingKeywords, "miss")}` : ""}`;
}

const fileBase = () => ((currentResume?.name || "resume").replace(/[^\w]+/g, "_") + "_ATS_Resume");
$("#pdfBtn").onclick = () => {
  const old = document.title;
  document.title = fileBase();
  window.print();
  document.title = old;
};
$("#docBtn").onclick = () => {
  const body = $("#resumePaper").innerHTML.replace(/ contenteditable="true" spellcheck="false"/g, "");
  // Word ignores flex/grid, so keep dates inline with a gap and stack section labels
  const wordFix = `.tpl .t-row span{display:inline}.tpl .t-date{margin-left:14pt}.tpl .t-sec{display:block!important}
    .tpl .t-grid{display:block}.tpl .t-grid li{display:list-item}.tpl .t-contact div{display:inline-block;margin-right:18pt}`;
  const html = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word"><head><meta charset="utf-8"><style>${templateCss(templateId)}${wordFix}</style></head><body><div class="tpl tpl-${templateId}">${body}</div></body></html>`;
  const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(new Blob(["﻿", html], { type: "application/msword" })), download: `${fileBase()}.doc` });
  a.click();
  URL.revokeObjectURL(a.href);
};
$("#copyBtn").onclick = async () => {
  try { await navigator.clipboard.writeText($("#resumePaper").innerText); toast("Resume text copied"); }
  catch { toast("Copy failed — select the text manually"); }
};

// ================= CHATBOT =================
const chatHistory = [];
const WELCOME = "Hello, I'm **CareerPilot**.\n\nAsk me about trending roles, salaries, which domain suits a fresher, demand by city, or a learning roadmap. You can start with one of the suggestions below.";

function md(text) {
  // tiny, safe markdown renderer (escape first, then format)
  const lines = esc(text).split("\n");
  let out = "", list = null, table = [];
  const inline = (s) => s.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/(^|[^*])\*(?!\s)(.+?)\*/g, "$1<i>$2</i>").replace(/_\((.+?)\)_/g, "<i>($1)</i>").replace(/`(.+?)`/g, "<code>$1</code>");
  const flushList = () => { if (list) { out += `</${list}>`; list = null; } };
  const flushTable = () => {
    if (!table.length) return;
    const rows = table.filter((r) => !/^\|?\s*:?-{2,}/.test(r)).map((r) => r.replace(/^\||\|$/g, "").split("|").map((c) => inline(c.trim())));
    out += `<table><thead><tr>${rows[0].map((c) => `<th>${c}</th>`).join("")}</tr></thead><tbody>${rows.slice(1).map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
    table = [];
  };
  for (const raw of lines) {
    const l = raw.trim();
    if (l.startsWith("|")) { flushList(); table.push(l); continue; }
    flushTable();
    let m;
    if ((m = l.match(/^[-*•]\s+(.*)/))) { if (list !== "ul") { flushList(); out += "<ul>"; list = "ul"; } out += `<li>${inline(m[1])}</li>`; }
    else if ((m = l.match(/^\d+[.)]\s+(.*)/))) { if (list !== "ol") { flushList(); out += "<ol>"; list = "ol"; } out += `<li>${inline(m[1])}</li>`; }
    else if ((m = l.match(/^#{1,4}\s+(.*)/))) { flushList(); out += `<p><b>${inline(m[1])}</b></p>`; }
    else if (!l) flushList();
    else { flushList(); out += `<p>${inline(l)}</p>`; }
  }
  flushList(); flushTable();
  return out;
}
function addMsg(role, text) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.innerHTML = role === "user" ? esc(text) : md(text);
  $("#chatBody").appendChild(div);
  $("#chatBody").scrollTop = $("#chatBody").scrollHeight;
  return div;
}
function resetChat() {
  chatHistory.length = 0;
  $("#chatBody").innerHTML = "";
  addMsg("bot", WELCOME);
  $("#suggestions").classList.remove("hidden");
}
let chatBusy = false;
async function sendChat(text) {
  text = text.trim();
  if (!text || chatBusy) return;
  chatBusy = true;
  $("#chatForm button[type=submit]").disabled = true;
  $("#suggestions").classList.add("hidden");
  addMsg("user", text);
  chatHistory.push({ role: "user", content: text });
  const bubble = addMsg("bot", "");
  bubble.innerHTML = '<span class="typing"><span></span><span></span><span></span></span>';
  const body = $("#chatBody");
  let reply = "";
  let frame = 0;
  // re-render markdown at most once per animation frame while words stream in
  const paint = () => {
    frame = 0;
    const nearBottom = body.scrollHeight - body.scrollTop - body.clientHeight < 80;
    bubble.innerHTML = md(reply);
    if (nearBottom) body.scrollTop = body.scrollHeight;
  };
  try {
    const res = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json", ...authHeaders() }, body: JSON.stringify({ messages: chatHistory }) });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || "Chat failed");
    }
    // Reply arrives as newline-delimited JSON: {"t":"..."} chunks, then {"done":true} or {"error":"..."}
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        const msg = JSON.parse(line);
        if (msg.error) throw new Error(msg.error);
        if (msg.t) { reply += msg.t; if (!frame) frame = requestAnimationFrame(paint); }
      }
    }
    if (frame) cancelAnimationFrame(frame);
    paint();
    if (!reply) throw new Error("No reply received. Please try again.");
    chatHistory.push({ role: "assistant", content: reply });
  } catch (err) {
    if (frame) cancelAnimationFrame(frame);
    bubble.innerHTML = (reply ? md(reply) : "") + `<p style="color:var(--err)">${esc(err.message)}</p>`;
    // keep the history alternating user/assistant
    if (reply) chatHistory.push({ role: "assistant", content: reply });
    else chatHistory.pop();
  } finally {
    chatBusy = false;
    $("#chatForm button[type=submit]").disabled = false;
    body.scrollTop = body.scrollHeight;
  }
}
$("#chatForm").onsubmit = (e) => { e.preventDefault(); if (chatBusy) return; const t = $("#chatText"); sendChat(t.value); t.value = ""; t.style.height = ""; };
$("#chatText").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("#chatForm").requestSubmit(); } });
$("#chatText").addEventListener("input", (e) => { e.target.style.height = "auto"; e.target.style.height = Math.min(140, e.target.scrollHeight) + "px"; });
$("#suggestions").onclick = (e) => { const c = e.target.closest(".chip"); if (c) sendChat(c.textContent); };
$("#clearChat").onclick = resetChat;

// ================= boot =================
(async function init() {
  try { config = await fetch("/api/config").then((r) => r.json()); } catch {}
  refreshKeyDot();
  resetChat();
  await loadJobs();
  const start = location.hash.slice(1);
  if (["home", "resume", "trends", "chat"].includes(start)) showTab(start);
})();
