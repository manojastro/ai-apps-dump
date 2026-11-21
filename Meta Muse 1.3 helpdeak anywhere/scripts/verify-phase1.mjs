#!/usr/bin/env node
// Phase 1 acceptance verification (no deps, Node 22 global WebSocket).
// Assumes server already running at --url / --http.
// Tests: happy pair + consent, wrong code rejected, reuse rejected, rate-limited.
const args = process.argv.slice(2);
function opt(name, def) {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? String(args[i + 1]) : def;
}
const WS_URL = opt("--url", "ws://127.0.0.1:18080/ws");
const HTTP_BASE = opt("--http", "http://127.0.0.1:18080");

function wsConnect(url) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(url);
    const t = setTimeout(() => { try { ws.close(); } catch {} reject(new Error("connect timeout")); }, 5000);
    ws.onopen = () => { clearTimeout(t); resolve(ws); };
    ws.onerror = () => { clearTimeout(t); reject(new Error("connect error")); };
  });
}
function waitFor(ws, pred, timeoutMs = 5000) {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => { ws.onmessage = null; reject(new Error("wait timeout")); }, timeoutMs);
    ws.onmessage = (ev) => {
      let msg = null;
      try { msg = JSON.parse(String(ev.data)); } catch { return; }
      if (pred(msg)) { clearTimeout(t); resolve(msg); }
    };
  });
}
async function httpGet(path) {
  const res = await fetch(HTTP_BASE + path);
  const text = await res.text();
  return { status: res.status, text };
}
function pickUnusedCodes(used, n) {
  const out = [];
  let c = 100000;
  while (out.length < n && c < 999999) {
    const s = String(c);
    if (!used.has(s)) out.push(s);
    c += 11111;
  }
  return out;
}

const used = new Set();
let pass = 0;
function ok(name) { pass++; console.log(`PASS: ${name}`); }
function fail(name, detail) {
  console.error(`FAIL: ${name} — ${detail}`);
  process.exit(1);
}

// 0. HTTP checks
try {
  const h = await httpGet("/healthz");
  if (h.status !== 200 || !h.text.includes('"ok":true')) fail("healthz", h.text.slice(0, 200));
  ok("GET /healthz");
  const root = await httpGet("/");
  if (root.status !== 200 || !root.text.includes("Agent Console")) fail("portal", `status=${root.status}`);
  ok("GET / serves portal");
} catch (e) {
  fail("http", String(e?.message ?? e));
}

// 1. Happy path: agent.create -> host.join -> consent:true -> Connected
let agentWs;
let codeA = "";
try {
  agentWs = await wsConnect(WS_URL);
  agentWs.send(JSON.stringify({ t: "agent.create", agentName: "VerifyAgent" }));
  const created = await waitFor(agentWs, (m) => m.t === "session.created");
  codeA = String(created.code || "");
  if (!/^[0-9]{6}$/.test(codeA)) fail("agent.create", JSON.stringify(created));
  used.add(codeA);
  ok(`agent.create -> code ${codeA}`);

  const joinPage = await httpGet(`/j/${codeA}`);
  if (joinPage.status !== 200 || !joinPage.text.includes("Join your support session") || !joinPage.text.includes("/download/HelpdeskAnywhere.exe")) fail("join page", `status=${joinPage.status}`);
  ok(`GET /j/${codeA} serves join page`);

  const hostWs = await wsConnect(WS_URL);
  const agentPeerJoined = waitFor(agentWs, (m) => m.t === "peer.joined");
  const hostReq = waitFor(hostWs, (m) => m.t === "host.connectRequest");
  hostWs.send(JSON.stringify({ t: "host.join", code: codeA, machine: "VERIFY-PC", user: "verify", os: "Windows 11" }));
  const req = await hostReq;
  if (!String(req.agentName || "").includes("VerifyAgent")) fail("connectRequest", JSON.stringify(req));
  ok("host.join -> host.connectRequest names agent");
  await agentPeerJoined;
  ok("agent sees peer.joined (Waiting -> Awaiting consent)");

  const consentResult = waitFor(agentWs, (m) => m.t === "consent.result");
  hostWs.send(JSON.stringify({ t: "host.consent", accepted: true }));
  const cr = await consentResult;
  if (cr.accepted !== true) fail("consent", JSON.stringify(cr));
  ok("host.consent:true -> agent consent.result:true (Connected)");
  try { hostWs.close(); } catch {}
} catch (e) {
  fail("happy path", String(e?.message ?? e));
}

// 2. Wrong code rejected
try {
  const [bad] = pickUnusedCodes(used, 1);
  const w = await wsConnect(WS_URL);
  w.send(JSON.stringify({ t: "host.join", code: bad, machine: "X", user: "y", os: "z" }));
  const err = await waitFor(w, (m) => m.t === "error");
  if (err.error !== "invalid_code") fail("wrong code", JSON.stringify(err));
  ok(`wrong code ${bad} -> invalid_code`);
  try { w.close(); } catch {}
} catch (e) {
  fail("wrong code", String(e?.message ?? e));
}

// 3. Reuse rejected (single-use burn)
try {
  const w = await wsConnect(WS_URL);
  w.send(JSON.stringify({ t: "host.join", code: codeA, machine: "X", user: "y", os: "z" }));
  const err = await waitFor(w, (m) => m.t === "error");
  if (err.error !== "invalid_code") fail("reuse", JSON.stringify(err));
  ok(`reuse code ${codeA} -> invalid_code`);
  try { w.close(); } catch {}
} catch (e) {
  fail("reuse", String(e?.message ?? e));
}

// 4. Rate-limit: 6 rapid bad joins -> first invalid_code, last rate_limited
try {
  const bads = pickUnusedCodes(used, 6);
  bads.forEach((c) => used.add(c));
  const errors = [];
  for (const b of bads) {
    const w = await wsConnect(WS_URL);
    w.send(JSON.stringify({ t: "host.join", code: b, machine: "X", user: "y", os: "z" }));
    const err = await waitFor(w, (m) => m.t === "error");
    errors.push(String(err.error || ""));
    try { w.close(); } catch {}
  }
  console.log("rate-limit batch errors:", JSON.stringify(errors));
  if (errors[0] !== "invalid_code") fail("rate-limit[0]", JSON.stringify(errors));
  if (errors[errors.length - 1] !== "rate_limited") fail("rate-limit[last]", JSON.stringify(errors));
  ok("6 rapid bad joins -> rate_limited");
} catch (e) {
  fail("rate-limit", String(e?.message ?? e));
}

try { agentWs?.close(); } catch {}
console.log(`\nPhase 1 acceptance: ALL ${pass} checks passed.`);
process.exit(0);
