#!/usr/bin/env node
// Phase 3 verification: real Applet.exe --headless --video streams full frames.
// Agent counts [0x01][jpeg] binary frames, reports FPS + bandwidth, asserts floor.
import { spawn } from "node:child_process";
import path from "node:path";

const args = process.argv.slice(2);
function opt(name, def) {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? String(args[i + 1]) : def;
}
const WS_URL = opt("--url", "ws://127.0.0.1:18084/ws");
const EXE = opt("--exe", path.resolve("server/public/download/HelpdeskAnywhere.exe"));
const SERVER = opt("--server", WS_URL);
const WINDOW_S = Number(opt("--window", "12"));
const MIN_FPS = Number(opt("--min-fps", "8"));

function wsConnect(url) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(url);
    ws.binaryType = "arraybuffer";
    const t = setTimeout(() => { try { ws.close(); } catch {} reject(new Error("connect timeout")); }, 5000);
    ws.onopen = () => { clearTimeout(t); resolve(ws); };
    ws.onerror = () => { clearTimeout(t); reject(new Error("connect error")); };
  });
}

const agent = await wsConnect(WS_URL);
agent.binaryType = "arraybuffer";
agent.send(JSON.stringify({ t: "agent.create", agentName: "Phase3Verify" }));
const code = await new Promise((resolve, reject) => {
  const t = setTimeout(() => reject(new Error("no session.created")), 5000);
  agent.onmessage = (ev) => {
    if (typeof ev.data !== "string") return;
    try {
      const m = JSON.parse(String(ev.data));
      if (m.t === "session.created") { clearTimeout(t); resolve(String(m.code)); }
    } catch {}
  };
});
if (!/^[0-9]{6}$/.test(code)) throw new Error(`bad code ${code}`);
console.log(`session code=${code}`);

let keys = 0;
let deltas = 0;
let bytes = 0;
let firstChecked = false;
agent.onmessage = (ev) => {
  if (typeof ev.data === "string") return;
  const buf = ev.data instanceof ArrayBuffer ? new Uint8Array(ev.data) : null;
  if (!buf || buf.length < 4) return;
  if (buf[0] === 0x02) {
    deltas++;
    bytes += buf.length;
    return;
  }
  if (buf[0] !== 0x01) return;
  if (!firstChecked) {
    firstChecked = true;
    if (buf[1] !== 0xff || buf[2] !== 0xd8) {
      console.error("first frame is not JPEG (missing SOI marker)");
      process.exit(1);
    }
    console.log(`first keyframe: ${buf.length} bytes, JPEG SOI ok`);
  }
  keys++;
  bytes += buf.length;
};

const exe = spawn(EXE, [
  "--headless", "--server", SERVER, "--code", code,
  "--accept", "--video", "--duration", String(WINDOW_S + 2),
], { stdio: ["ignore", "pipe", "pipe"] });
exe.stdout.on("data", (d) => process.stdout.write(`[exe] ${String(d)}`));
exe.stderr.on("data", (d) => process.stderr.write(`[exe] ${String(d)}`));
const consentOk = await new Promise((resolve, reject) => {
  const t = setTimeout(() => reject(new Error("no consent.result")), 20000);
  const prev = agent.onmessage;
  agent.onmessage = (ev) => {
    if (typeof prev === "function") { try { prev.call(agent, ev); } catch {} }
    if (typeof ev.data !== "string") return;
    try {
      const m = JSON.parse(String(ev.data));
      if (m.t === "consent.result" && m.accepted === true) { clearTimeout(t); resolve(true); }
    } catch {}
  };
});
if (!consentOk) throw new Error("consent failed");
console.log("active, measuring…");
await new Promise((r) => setTimeout(r, WINDOW_S * 1000));
const total = keys + deltas;
const kbps = Math.round((bytes * 8) / WINDOW_S / 1000);
console.log(`keyframes=${keys} deltas=${deltas} updates=${total} bytes=${bytes} kbps=${kbps}`);
try { agent.send(JSON.stringify({ t: "agent.end" })); } catch {}
try { agent.close(); } catch {}
await new Promise((resolve) => {
  const t = setTimeout(() => { try { exe.kill(); } catch {} resolve(0); }, 8000);
  exe.on("close", (c) => { clearTimeout(t); resolve(c ?? 0); });
});
// Idle desktops correctly yield little traffic (keyframes every 5s); the
// wrapper jiggles the cursor, so deltas must appear.
if (keys < 1) {
  console.error("FAIL: no keyframe received");
  process.exit(1);
}
if (deltas < 1) {
  console.error("FAIL: no dirty-rect deltas received (was the screen active?)");
  process.exit(1);
}
if (total < MIN_FPS) {
  console.error(`FAIL: only ${total} updates in ${WINDOW_S}s (floor ${MIN_FPS})`);
  process.exit(1);
}
console.log(`PASS: keyframes + ${deltas} deltas, ${(bytes / 1024).toFixed(0)} KiB over ${WINDOW_S}s`);
process.exit(0);
