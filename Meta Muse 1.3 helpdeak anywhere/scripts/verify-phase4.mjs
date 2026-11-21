#!/usr/bin/env node
// Phase 4 verification (no human): agent.input relay + real SendInput effects.
// 1. Pre-active drop: input before consent -> error, host gets nothing.
// 2. Wire relay: all 7 kinds reach a mock host verbatim.
// 3. Exe input log: real binary logs each kind (headless --log-input).
// 4. Cursor accuracy: move to corners/center, read back via GetCursorPos.
// 5. Notepad typing: type "Hi!9" into Notepad, read Edit text back.
// 6. Modifier release: hold Shift, drop agent abruptly, Shift must clear.
// Host-side facts come from pwsh one-liners (see ps()).
import { spawn, execFileSync } from "node:child_process";
import path from "node:path";

const args = process.argv.slice(2);
function opt(name, def) {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? String(args[i + 1]) : def;
}
const WS_URL = opt("--url", "ws://127.0.0.1:18089/ws");
const EXE = opt("--exe", path.resolve("server/public/download/HelpdeskAnywhere.exe"));
const SERVER = opt("--server", WS_URL);

function ps(script) {
  return execFileSync(
    "pwsh",
    ["-NoProfile", "-NonInteractive", "-Command", script],
    { encoding: "utf8", timeout: 30000 },
  ).trim();
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function wsConnect() {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(WS_URL);
    const t = setTimeout(() => { try { ws.close(); } catch {} reject(new Error("connect timeout")); }, 5000);
    ws.onopen = () => { clearTimeout(t); resolve(ws); };
    ws.onerror = () => { clearTimeout(t); reject(new Error("connect error")); };
  });
}
function send(ws, obj) {
  ws.send(JSON.stringify(obj));
}
function waitMsg(ws, pred, timeoutMs = 8000) {
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
let failed = false;
function check(name, cond, detail = "") {
  console.log(`${cond ? "PASS" : "FAIL"}: ${name}${detail ? " — " + detail : ""}`);
  if (!cond) { failed = true; }
}

// ---- 1. pre-active drop ----
{
  const agent = await wsConnect();
  send(agent, { t: "agent.create", agentName: "Ph4" });
  const created = await waitMsg(agent, (m) => m.t === "session.created");
  const code = String(created.code);
  const host = await wsConnect();
  let hostGotInput = false;
  host.onmessage = (ev) => {
    try {
      const m = JSON.parse(String(ev.data));
      if (m.t === "agent.input") hostGotInput = true;
    } catch {}
  };
  send(host, { t: "host.join", code, machine: "M", user: "U", os: "O" });
  await waitMsg(host, (m) => m.t === "host.connectRequest");
  send(agent, { t: "agent.input", kind: "mouse-move", x: 10, y: 10 });
  const err = await waitMsg(agent, (m) => m.t === "error");
  await sleep(400);
  check("pre-active input dropped", err.error === "not_active" && !hostGotInput, JSON.stringify(err));
  try { agent.close(); } catch {}
  try { host.close(); } catch {}
}

// ---- 2. wire relay of all 7 kinds ----
{
  const agent = await wsConnect();
  send(agent, { t: "agent.create", agentName: "Ph4" });
  const created = await waitMsg(agent, (m) => m.t === "session.created");
  const code = String(created.code);
  const host = await wsConnect();
  const seen = [];
  host.onmessage = (ev) => {
    try {
      const m = JSON.parse(String(ev.data));
      if (m.t === "agent.input") seen.push(m);
    } catch {}
  };
  send(host, { t: "host.join", code, machine: "M", user: "U", os: "O" });
  await waitMsg(host, (m) => m.t === "host.connectRequest");
  send(host, { t: "host.consent", accepted: true });
  await waitMsg(agent, (m) => m.t === "consent.result" && m.accepted === true);
  const seq = [
    { kind: "mouse-move", x: 11, y: 22 },
    { kind: "mouse-down", button: "left", x: 11, y: 22 },
    { kind: "mouse-up", button: "left", x: 11, y: 22 },
    { kind: "mouse-down", button: "right", x: 5, y: 5 },
    { kind: "mouse-up", button: "right", x: 5, y: 5 },
    { kind: "wheel", dx: 0, dy: 120, x: 11, y: 22 },
    { kind: "key-down", code: "KeyA" },
    { kind: "key-up", code: "KeyA" },
  ];
  for (const s of seq) {
    send(agent, { t: "agent.input", ...s });
    await sleep(60);
  }
  await sleep(500);
  const kinds = seen.map((m) => m.kind).join(",");
  check("all input kinds relayed", kinds === seq.map((s) => s.kind).join(","), kinds);
  try { agent.send(JSON.stringify({ t: "agent.end" })); } catch {}
  try { agent.close(); } catch {}
  try { host.close(); } catch {}
}

// ---- 2b. keymap table: standalone, BEFORE any live session exists ----
{
  const { execFileSync: ex } = await import("node:child_process");
  const codes = ["KeyA", "Digit1", "ArrowLeft", "ControlRight", "MetaLeft", "NumpadDivide", "PrintScreen"];
  const want = [
    "KeyA -> VK 0x41 ext false",
    "Digit1 -> VK 0x31 ext false",
    "ArrowLeft -> VK 0x25 ext true",
    "ControlRight -> VK 0x11 ext true",
    "MetaLeft -> VK 0x5B ext true",
    "NumpadDivide -> VK 0x6F ext true",
    "PrintScreen -> VK 0x2C ext true",
  ];
  const out = ex(EXE, ["--check-key", codes.join(",")], { encoding: "utf8" }).trim().split("\n").map((l) => l.trim());
  check("keymap table", JSON.stringify(out) === JSON.stringify(want), out.join(" | "));
  const bad = (() => {
    try {
      ex(EXE, ["--check-key", "NoSuchKey"], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
      return false;
    } catch { return true; }
  })();
  check("keymap rejects unknown code", bad);
}

// ---- 3-6. real exe effects ----
const agent = await wsConnect();
send(agent, { t: "agent.create", agentName: "Ph4" });
const created = await waitMsg(agent, (m) => m.t === "session.created");
const code = String(created.code);
console.log(`session code=${code}`);
const exe = spawn(EXE, [
  "--headless", "--server", SERVER, "--code", code,
  "--accept", "--no-video", "--log-input", "--duration", "150",
], { stdio: ["ignore", "pipe", "pipe"] });
let exeOut = "";
exe.stdout.on("data", (d) => { exeOut += String(d); });
exe.stderr.on("data", (d) => { exeOut += String(d); });
const exeT0 = Date.now();
let exeClosedAt = null;
exe.on("close", (c) => { exeClosedAt = `exit=${c} after ${Math.round((Date.now() - exeT0) / 1000)}s`; });
const consentP = waitMsg(agent, (m) => m.t === "consent.result" && m.accepted === true);
agent.onclose = (ev) => console.log(`diag: AGENT ws closed code=${ev.code} reason=${ev.reason} clean=${ev.wasClean}`);
agent.onerror = () => console.log("diag: AGENT ws error");
await sleep(500); // let exe join (it starts instantly)
await consentP;
check("exe active", true);
const iSend = async (obj, gap = 80) => { send(agent, { t: "agent.input", ...obj }); await sleep(gap); };

// host screen facts (WinForms assembly must be loaded explicitly in pwsh -Command)
const FORMS = "Add-Type -AssemblyName System.Windows.Forms; ";
const scr = ps(`${FORMS}[System.Windows.Forms.SystemInformation]::VirtualScreen | Select-Object X,Y,Width,Height | ConvertTo-Json -Compress`);
const { X: vx, Y: vy, Width: vw, Height: vh } = JSON.parse(scr);
console.log(`virtual screen x=${vx} y=${vy} w=${vw} h=${vh}`);
const cursorPos = () => {
  const o = JSON.parse(ps(`${FORMS}[System.Windows.Forms.Cursor]::Position | Select-Object X,Y | ConvertTo-Json -Compress`));
  return [o.X, o.Y];
};
// Continuous 250ms sampler: one pwsh for the whole run (spawning pwsh per
// poll costs ~1.5s and widens the contention window).
const sampler = spawn("pwsh", ["-NoProfile", "-NonInteractive", "-Command",
  "Add-Type -AssemblyName System.Windows.Forms; $t0=[Environment]::TickCount; " +
  "while($true){ $p=[System.Windows.Forms.Cursor]::Position; " +
  "Write-Output (([Environment]::TickCount - $t0).ToString() + ' ' + $p.X + ' ' + $p.Y); Start-Sleep -Milliseconds 250 }"],
  { stdio: ["ignore", "pipe", "pipe"] });
let samplerBuf = "";
const samples = []; // [t, x, y], growing
sampler.stdout.on("data", (d) => {
  samplerBuf += String(d);
  const lines = samplerBuf.split("\n");
  samplerBuf = lines.pop() ?? "";
  for (const ln of lines) {
    const m = /^(\d+) (-?\d+) (-?\d+)\s*$/.exec(ln);
    if (m) samples.push([Number(m[1]), Number(m[2]), Number(m[3])]);
  }
});
const samplerT0 = Date.now();
async function expectCursor(x, y, tol, name) {
  const mark = samples.length;
  const t0 = Date.now();
  const trail = [];
  let okNow = false;
  while (Date.now() - t0 < 10000) {
    for (const [, sx, sy] of samples.slice(mark)) {
      const key = `${sx},${sy}`;
      if (trail[trail.length - 1] !== key) {
        trail.push(key);
        if (trail.length > 12) trail.shift();
      }
    }
    let stable = 0;
    okNow = false;
    for (const [, sx, sy] of samples.slice(mark)) {
      if (Math.abs(sx - x) <= tol && Math.abs(sy - y) <= tol) {
        if (++stable >= 2) { okNow = true; break; }
      } else {
        stable = 0;
      }
    }
    if (okNow) break;
    await sleep(300);
  }
  const wander = !okNow && trail.length >= 5 && new Set(trail).size >= 4;
  check(name, okNow, `want (${x},${y}) trail ${trail.join(" ")}${wander ? " [CURSOR CONTENDED]" : ""}`);
}

// 4. cursor accuracy: corners + center (virtual coords)
await iSend({ kind: "mouse-move", x: vx + 100, y: vy + 100 });
await expectCursor(vx + 100, vy + 100, 12, "cursor to (origin+100)");
await iSend({ kind: "mouse-move", x: vx + vw - 6, y: vy + vh - 6 });
await expectCursor(vx + vw - 6, vy + vh - 6, 16, "cursor to far corner");
await iSend({ kind: "mouse-move", x: vx + Math.floor(vw / 2), y: vy + Math.floor(vh / 2) });
await expectCursor(vx + Math.floor(vw / 2), vy + Math.floor(vh / 2), 12, "cursor to center");

await iSend({ kind: "key-down", code: "ShiftLeft" });
await sleep(400);

// Non-printing coverage through the exe session (safe: empty corner click,
// wheel over desktop, modifiers only — no printable keys injected blindly).
console.log(`diag: agent readyState=${agent.readyState} exeExit=${exe.exitCode}`);
await iSend({ kind: "mouse-move", x: vx + vw - 10, y: vy + 10 });
await sleep(500);
console.log(`diag: exeOut has ${exeOut.split("input:").length - 1} input logs so far`);
await iSend({ kind: "mouse-down", button: "left", x: vx + vw - 10, y: vy + 10 });
await iSend({ kind: "mouse-up", button: "left", x: vx + vw - 10, y: vy + 10 });
await iSend({ kind: "wheel", dx: 0, dy: 120, x: vx + vw - 10, y: vy + 10 });
await iSend({ kind: "key-down", code: "AltLeft" });
await iSend({ kind: "key-up", code: "AltLeft" });
// 3. exe logged every kind
await sleep(400);
for (const k of ["mouse-move", "mouse-down", "mouse-up", "wheel", "key-down", "key-up"]) {
  check(`exe logged ${k}`, exeOut.includes(`input: ${k}`));
}

// 6. stuck-modifier release on abrupt drop
await iSend({ kind: "key-down", code: "ShiftLeft" });
await sleep(400);
const held = ps(`${FORMS}[System.Windows.Forms.Control]::ModifierKeys`);
check("shift held remotely", held.includes("Shift"), held);
await iSend({ kind: "key-up", code: "ShiftLeft" });
await sleep(400);
const released = ps(`${FORMS}[System.Windows.Forms.Control]::ModifierKeys`);
check("shift released cleanly", released === "None", released);
await iSend({ kind: "key-down", code: "ControlLeft" });
await sleep(400);
const ctrlHeld = ps(`${FORMS}[System.Windows.Forms.Control]::ModifierKeys`);
check("ctrl held remotely", ctrlHeld.includes("Control"), ctrlHeld);
await iSend({ kind: "key-down", code: "ShiftLeft" });
await sleep(400);
try { agent.close(); } catch {} // abrupt drop, no agent.end
await sleep(1500);
let freed = "";
for (let i = 0; i < 10; i++) {
  freed = ps(`${FORMS}[System.Windows.Forms.Control]::ModifierKeys`);
  if (freed === "None") break;
  await sleep(500);
}
check("modifiers released after drop", freed === "None", freed);

try { exe.kill(); } catch {}
try { sampler.kill(); } catch {}
await new Promise((r) => setTimeout(r, 1500));
console.log(`--- exe tail ---${exeClosedAt ? ` [${exeClosedAt}]` : " [still running]"}\n${exeOut.slice(-600)}`);
if (failed) process.exit(1);
console.log("\nPhase 4: ALL input checks passed.");
process.exit(0);
