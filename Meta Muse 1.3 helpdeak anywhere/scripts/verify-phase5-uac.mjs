#!/usr/bin/env node
// Phase 5 elevated UAC cycle (runs UNDER scripts/test-phase5-elevated.ps1 as
// admin). The .mjs orchestrates; privileged steps are delegated via stdout:
//   ACTION:INSTALL pipe=<name>   -> ps1 installs service, replies DONE ...
//   ACTION:TRIGGER_UAC           -> ps1 raises a real UAC prompt, replies DONE
//   ACTION:UNINSTALL             -> ps1 removes service, replies DONE ...
// Replies arrive on stdin as DONE lines. Exit 0 pass, 1 fail, 2 pending-human.
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import readline from "node:readline";

const args = process.argv.slice(2);
function opt(name, def) {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? String(args[i + 1]) : def;
}
const HTTP_BASE = opt("--http", "http://127.0.0.1:18103");
const WS_URL = opt("--url", "ws://127.0.0.1:18103/ws");
const EXE = opt("--exe", path.resolve("server/public/download/HelpdeskAnywhere.exe"));
const OUTDIR = opt("--outdir", path.resolve("server/data/uac-samples"));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let failed = false;
let pending = "";
const check = (name, cond, detail = "") => {
  console.log(`${cond ? "PASS" : "FAIL"}: ${name}${detail ? " — " + detail : ""}`);
  if (!cond) failed = true;
};

const rl = readline.createInterface({ input: process.stdin });
const doneQueue = [];
rl.on("line", (line) => {
  if (line.startsWith("DONE")) {
    const w = doneQueue.shift();
    if (w) w(line);
  }
});
function action(line, timeoutMs = 120000) {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error(`no DONE for ${line}`)), timeoutMs);
    doneQueue.push((reply) => { clearTimeout(t); resolve(reply); });
    console.log(line);
  });
}

function wsConnect() {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(WS_URL);
    const t = setTimeout(() => { try { ws.close(); } catch {} reject(new Error("connect timeout")); }, 5000);
    ws.onopen = () => { clearTimeout(t); resolve(ws); };
    ws.onerror = () => { clearTimeout(t); reject(new Error("connect error")); };
  });
}
const send = (ws, obj) => ws.send(JSON.stringify(obj));
function waitMsg(ws, pred, timeoutMs = 10000) {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("wait timeout")), timeoutMs);
    const prev = ws.onmessage;
    ws.onmessage = (ev) => {
      if (typeof prev === "function") { try { prev.call(ws, ev); } catch {} }
      if (typeof ev.data !== "string") return;
      let m = null;
      try { m = JSON.parse(String(ev.data)); } catch { return; }
      if (pred(m)) { clearTimeout(t); ws.onmessage = prev; resolve(m); }
    };
  });
}

fs.mkdirSync(OUTDIR, { recursive: true });
const agent = await wsConnect();
send(agent, { t: "agent.create", agentName: "Ph5-UAC" });
const created = await waitMsg(agent, (m) => m.t === "session.created");
const code = String(created.code);
console.log(`session code=${code}`);

const exe = spawn(EXE, ["--headless", "--server", WS_URL, "--code", code,
  "--accept", "--video", "--duration", "150"], { stdio: ["ignore", "pipe", "pipe"] });
let exeOut = "";
exe.stdout.on("data", (d) => { exeOut += String(d); });
exe.stderr.on("data", (d) => { exeOut += String(d); });
await waitMsg(agent, (m) => m.t === "consent.result" && m.accepted === true);
console.log("active, pipe starting");
let pipeName = "";
for (let i = 0; i < 40 && !pipeName; i++) {
  const m = /headless: pipe (\S+)/.exec(exeOut);
  if (m) pipeName = m[1];
  else await sleep(500);
}
check("session pipe up", pipeName.length > 0, pipeName);
if (!pipeName) process.exit(1);

// Save a Default-desktop frame + count pre-UAC traffic.
let defaultJpg = null;
let preFrames = 0;
const countTap = (ev) => {
  if (typeof ev.data === "string") return;
  const b = ev.data instanceof ArrayBuffer ? Buffer.from(ev.data) : null;
  if (!b || b.length < 4 || (b[0] !== 0x01 && b[0] !== 0x02)) return;
  preFrames++;
  if (!defaultJpg && b[0] === 0x01) defaultJpg = b.subarray(1);
};
agent.onmessage = (ev) => { try { countTap(ev); } catch {} };
await sleep(5000);
check("default frames flowing pre-UAC", preFrames > 0, `${preFrames} msgs`);
if (defaultJpg) fs.writeFileSync(path.join(OUTDIR, "default.jpg"), defaultJpg);

// Install the service (privileged).
const installReply = await action(`ACTION:INSTALL pipe=${pipeName}`);
check("service installed+running", installReply.startsWith("DONE install ok"), installReply);
if (!installReply.startsWith("DONE install ok")) process.exit(1);

// Raise a real UAC consent prompt from an unelevated process.
const trigReply = await action("ACTION:TRIGGER_UAC");
console.log(`trigger: ${trigReply}`);

// Wait for the secure desktop to appear on the wire.
let winlogonAt = 0;
try {
  await waitMsg(agent, (m) => m.t === "host.desktopChanged" && m.desktop === "Winlogon", 40000);
  winlogonAt = Date.now();
  check("desktopChanged Winlogon", true);
} catch {
  check("desktopChanged Winlogon", false, "timed out — is the prompt on screen?");
}

// Count secure frames + save a sample, then dismiss with Escape.
let secureFrames = 0;
let secureJpg = null;
agent.onmessage = (ev) => {
  try { countTap(ev); } catch {}
  if (typeof ev.data === "string") return;
  const b = ev.data instanceof ArrayBuffer ? Buffer.from(ev.data) : null;
  if (!b || b.length < 4) return;
  if (b[0] === 0x01 || b[0] === 0x02) {
    secureFrames++;
    if (!secureJpg && b[0] === 0x01) secureJpg = b.subarray(1);
  }
};
await sleep(6000);
if (secureJpg) fs.writeFileSync(path.join(OUTDIR, "secure.jpg"), secureJpg);
check("secure frames flow", secureFrames > 0, `${secureFrames} msgs`);
if (defaultJpg && secureJpg) {
  const same = createHash("sha256").update(defaultJpg).digest("hex") ===
    createHash("sha256").update(secureJpg).digest("hex");
  check("secure content differs from desktop", !same);
}

send(agent, { t: "agent.input", kind: "key-down", code: "Escape" });
await sleep(300);
send(agent, { t: "agent.input", kind: "key-up", code: "Escape" });
let backToDefault = false;
try {
  await waitMsg(agent, (m) => m.t === "host.desktopChanged" && m.desktop === "Default", 30000);
  backToDefault = true;
} catch {}
if (backToDefault) check("desktop returned to Default", true);
else {
  pending = "UAC prompt did not dismiss via Escape — click No on the user's screen once.";
  console.log(`PENDING: ${pending}`);
}

const unReply = await action("ACTION:UNINSTALL");
check("service fully removed", unReply.startsWith("DONE uninstall ok"), unReply);

try { agent.send(JSON.stringify({ t: "agent.end" })); } catch {}
try { agent.close(); } catch {}
try { exe.kill(); } catch {}
await sleep(1000);
if (failed) process.exit(1);
if (pending || !backToDefault) process.exit(2);
console.log("\nPhase 5 UAC cycle: ALL checks passed (real consent prompt streamed + dismissed).");
process.exit(0);
