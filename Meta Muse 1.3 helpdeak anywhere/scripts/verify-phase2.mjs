#!/usr/bin/env node
// Phase 2 transport verification: real Applet.exe --headless vs local server.
// Assumes server running at --url/--http and exe at --exe.
// Tests accept + decline flows end-to-end over the Phase 1 relay.
import { spawn } from "node:child_process";
import path from "node:path";

const args = process.argv.slice(2);
function opt(name, def) {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? String(args[i + 1]) : def;
}
const WS_URL = opt("--url", "ws://127.0.0.1:18082/ws");
const EXE = opt("--exe", path.resolve("server/public/download/HelpdeskAnywhere.exe"));
const SERVER = opt("--server", WS_URL);

function wsConnect(url) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(url);
    const t = setTimeout(() => { try { ws.close(); } catch {} reject(new Error("connect timeout")); }, 5000);
    ws.onopen = () => { clearTimeout(t); resolve(ws); };
    ws.onerror = () => { clearTimeout(t); reject(new Error("connect error")); };
  });
}
function runExe(code, accept) {
  return new Promise((resolve) => {
    const p = spawn(EXE, [
      "--headless", "--server", SERVER, "--code", code,
      accept ? "--accept" : "--decline", "--duration", "2",
    ], { stdio: ["ignore", "pipe", "pipe"] });
    let out = "";
    let err = "";
    p.stdout.on("data", (d) => { out += String(d); });
    p.stderr.on("data", (d) => { err += String(d); });
    const t = setTimeout(() => { try { p.kill(); } catch {} resolve({ exit: 124, out, err }); }, 25000);
    p.on("close", (c) => { clearTimeout(t); resolve({ exit: c ?? 1, out, err }); });
    p.on("error", (e) => { clearTimeout(t); resolve({ exit: 127, out, err: err + String(e?.message ?? e) }); });
  });
}

async function oneFlow(accept) {
  const agent = await wsConnect(WS_URL);
  try {
    agent.send(JSON.stringify({ t: "agent.create", agentName: "Phase2Verify" }));
    const code = await new Promise((resolve, reject) => {
      const t = setTimeout(() => reject(new Error("no session.created")), 5000);
      agent.onmessage = (ev) => {
        try {
          const m = JSON.parse(String(ev.data));
          if (m.t === "session.created") { clearTimeout(t); resolve(String(m.code)); }
        } catch {}
      };
    });
    if (!/^[0-9]{6}$/.test(code)) throw new Error(`bad code ${code}`);
    // Arm agent listeners BEFORE spawning host (avoid race).
    const consentP = new Promise((resolve, reject) => {
      const t = setTimeout(() => reject(new Error("no consent.result")), 20000);
      const prev = agent.onmessage;
      agent.onmessage = (ev) => {
        if (typeof prev === "function") { try { prev.call(agent, ev); } catch {} }
        try {
          const m = JSON.parse(String(ev.data));
          if (m.t === "consent.result") { clearTimeout(t); resolve(m.accepted === true); }
        } catch {}
      };
    });
    const r = await runExe(code, accept);
    console.log(`exe --${accept ? "accept" : "decline"} code=${code} exit=${r.exit}\n${r.out}${r.err}`);
    if (r.exit !== 0) throw new Error(`exe exited ${r.exit}`);
    if (/ObjectDisposedException|Unhandled exception/i.test(r.out + r.err)) {
      throw new Error("exe threw during teardown");
    }
    const consented = await consentP;
    if (consented !== accept) throw new Error(`consent.result=${consented}, expected ${accept}`);
    try { agent.send(JSON.stringify({ t: "agent.end" })); } catch {}
    return code;
  } finally {
    try { agent.close(); } catch {}
  }
}

const c1 = await oneFlow(true);
console.log(`PASS: accept flow code=${c1} (agent Connected)`);
const c2 = await oneFlow(false);
console.log(`PASS: decline flow code=${c2} (agent declined)`);
console.log("\nPhase 2 transport: ALL checks passed (real binary, headless).");
process.exit(0);
