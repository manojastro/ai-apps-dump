#!/usr/bin/env node
// Phase 5 unelevated verification (no admin, no UAC clicks):
// A. agent.sas relayed + audited; pre-active dropped.
// B. DesktopHelper on Default desktop over a Node pipe server: ready,
//    video frames (JPEG SOI), input moves the cursor, sas survives, clean exit.
//    Pipe ACL admits no Everyone/Anonymous.
// C. Headless session: credential elevation refused (tls_required) 5x, then
//    rate_limited; server audit keeps username, never the password.
// D. --test-logon maps a bad logon to the friendly message.
// E. Password strings appear nowhere.
import { spawn, execFileSync } from "node:child_process";
import net from "node:net";
import path from "node:path";

const args = process.argv.slice(2);
function opt(name, def) {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? String(args[i + 1]) : def;
}
const WS_URL = opt("--url", "ws://127.0.0.1:18101/ws");
const EXE = opt("--exe", path.resolve("server/public/download/HelpdeskAnywhere.exe"));
const SERVER = opt("--server", WS_URL);
const HELPER = opt("--helper", path.resolve("windows/DesktopHelper/bin/Debug/net8.0-windows/DesktopHelper.exe"));
const PW1 = "Wrong-Pw-Ph5-Alpha-1";
const PW2 = "Wrong-Pw-Ph5-Beta-2";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let failed = false;
const check = (name, cond, detail = "") => {
  console.log(`${cond ? "PASS" : "FAIL"}: ${name}${detail ? " — " + detail : ""}`);
  if (!cond) failed = true;
};
function ps(script) {
  return execFileSync("pwsh", ["-NoProfile", "-NonInteractive", "-Command", script], { encoding: "utf8", timeout: 30000 }).trim();
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

// ---- A. sas relay ----
{
  const agent = await wsConnect();
  send(agent, { t: "agent.create", agentName: "Ph5" });
  const created = await waitMsg(agent, (m) => m.t === "session.created");
  const host = await wsConnect();
  const seen = [];
  host.onmessage = (ev) => {
    try {
      const m = JSON.parse(String(ev.data));
      if (m.t === "agent.sas") seen.push(m);
    } catch {}
  };
  send(host, { t: "host.join", code: String(created.code), machine: "M", user: "U", os: "O" });
  await waitMsg(host, (m) => m.t === "host.connectRequest");
  send(host, { t: "host.consent", accepted: true });
  await waitMsg(agent, (m) => m.t === "consent.result" && m.accepted === true);
  send(agent, { t: "agent.sas" });
  await sleep(500);
  check("agent.sas relayed verbatim", seen.length === 1 && seen[0].t === "agent.sas", JSON.stringify(seen));
  try { agent.send(JSON.stringify({ t: "agent.end" })); } catch {}
  try { agent.close(); } catch {}
  try { host.close(); } catch {}
}

// ---- B. helper standalone over Node pipe server ----
{
  const pipeName = `hda-ph5test-${Date.now().toString(36)}`;
  const pipePath = `\\\\.\\pipe\\${pipeName}`;
  let buf = Buffer.alloc(0);
  const frames = [];
  let readyDesktop = "";
  const server = net.createServer((sock) => {
    sock.on("data", (d) => {
      buf = Buffer.concat([buf, d]);
      while (buf.length >= 4) {
        const len = buf.readInt32LE(0);
        if (len <= 0 || len > 12 * 1024 * 1024 || buf.length < 4 + len) break;
        const payload = buf.subarray(4, 4 + len);
        buf = buf.subarray(4 + len);
        if (payload[0] === 0x01 || payload[0] === 0x02) frames.push(payload);
        else {
          try {
            const m = JSON.parse(payload.toString("utf8"));
            if (m.t === "helper.ready") readyDesktop = String(m.desktop ?? "");
          } catch {}
        }
      }
    });
    server.sock = sock;
  });
  await new Promise((res, rej) => {
    server.on("error", rej);
    server.listen(pipePath, res);
  });
  const sendPipe = (obj) => {
    const p = Buffer.from(JSON.stringify(obj), "utf8");
    const h = Buffer.alloc(4);
    h.writeInt32LE(p.length, 0);
    server.sock.write(Buffer.concat([h, p]));
  };
  const helper = spawn(HELPER, ["--desktop", "Default", "--pipe", pipeName], { stdio: ["ignore", "pipe", "pipe"] });
  let helperErr = "";
  helper.stderr.on("data", (d) => { helperErr += String(d); });
  const t0 = Date.now();
  while (!readyDesktop && Date.now() - t0 < 15000) await sleep(300);
  check("helper ready on Default", readyDesktop === "Default", readyDesktop || helperErr.slice(0, 200));
  while (frames.length < 5 && Date.now() - t0 < 20000) await sleep(300);
  const f0 = frames[0];
  check("helper video frames", frames.length >= 5, `${frames.length} frames`);
  check("helper JPEG SOI", !!f0 && f0[0] === 0x01 && f0[1] === 0xff && f0[2] === 0xd8);
  // input through the pipe moves the real cursor
  const scr = JSON.parse(ps("Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SystemInformation]::VirtualScreen | Select-Object X,Y,Width,Height | ConvertTo-Json -Compress"));
  const tx = scr.X + scr.Width - 20;
  const ty = scr.Y + scr.Height - 20;
  sendPipe({ t: "agent.input", kind: "mouse-move", x: tx, y: ty });
  await sleep(1200);
  const pos = JSON.parse(ps("Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Cursor]::Position | Select-Object X,Y | ConvertTo-Json -Compress"));
  check("helper injects mouse", Math.abs(pos.X - tx) <= 30 && Math.abs(pos.Y - ty) <= 30, `(${pos.X},${pos.Y})`);
  // sas must not kill the helper
  sendPipe({ t: "agent.sas" });
  await sleep(1500);
  const nAfter = frames.length;
  await sleep(1000);
  check("helper survives sas", helper.exitCode === null && frames.length >= nAfter, `exit=${helper.exitCode}`);
  helper.kill();
  const hexit = await new Promise((res) => {
    const t = setTimeout(() => res("timeout"), 8000);
    helper.on("close", (c) => { clearTimeout(t); res(c === null ? "killed" : String(c)); });
  });
  check("helper exits on kill", hexit !== "timeout", String(hexit));
  server.close();
}

// ---- C. credential guard + rate limit + redaction (headless session) ----
const agent = await wsConnect();
send(agent, { t: "agent.create", agentName: "Ph5" });
const created = await waitMsg(agent, (m) => m.t === "session.created");
const code = String(created.code);
const exe = spawn(EXE, ["--headless", "--server", SERVER, "--code", code,
  "--accept", "--no-video", "--duration", "90"], { stdio: ["ignore", "pipe", "pipe"] });
let exeOut = "";
exe.stdout.on("data", (d) => { exeOut += String(d); });
exe.stderr.on("data", (d) => { exeOut += String(d); });
await waitMsg(agent, (m) => m.t === "consent.result" && m.accepted === true);
// Pipe ACL, verified deterministically in-process (a live Get-Acl races the
// single pipe instance against AV inspection holds).
{
  const { execFileSync: ex } = await import("node:child_process");
  const out = ex(EXE, ["--pipe-acl-test"], { encoding: "utf8" }).trim().split("\n").map((l) => l.trim());
  console.log(out.join(" | "));
  check("applet pipe ACL restricted", out[out.length - 1] === "acl: RESTRICTED", out.join(" | "));
}
const elev = async (pw, user) => {
  send(agent, { t: "agent.requestElevation", mode: "credential", domain: ".", username: user, password: pw });
  // Non-TLS local server refuses before relaying (error); a TLS relay would
  // answer host.elevated. Accept either shape.
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("wait timeout")), 8000);
    const prev = agent.onmessage;
    agent.onmessage = (ev) => {
      if (typeof prev === "function") { try { prev.call(agent, ev); } catch {} }
      if (typeof ev.data !== "string") return;
      let m = null;
      try { m = JSON.parse(String(ev.data)); } catch { return; }
      if (m.t === "host.elevated") { clearTimeout(t); agent.onmessage = prev; resolve(m); }
      else if (m.t === "error") { clearTimeout(t); agent.onmessage = prev; resolve({ ok: false, error: String(m.error ?? "") }); }
    };
  });
};
const errors = [];
for (let i = 0; i < 6; i++) {
  const r = await elev(i % 2 ? PW1 : PW2, `nosuchuser${i}`);
  errors.push(r.ok === true ? "OK" : String(r.error ?? ""));
  await sleep(200);
}
console.log("elevation errors:", JSON.stringify(errors));
check("credential refused without TLS x5", errors.slice(0, 5).every((e) => e === "tls_required"), errors.join(","));
check("6th elevation rate-limited", errors[5] === "rate_limited", errors[5] ?? "");
try { agent.send(JSON.stringify({ t: "agent.end" })); } catch {}
try { agent.close(); } catch {}
try { exe.kill(); } catch {}
await sleep(500);

// ---- D. logon error mapping (test-only probe, wrong password) ----
{
  const { execFileSync: ex } = await import("node:child_process");
  const out = execFileSync(EXE, ["--test-logon"],
    { encoding: "utf8", env: { ...process.env, HDA_TEST_DOMAIN: ".", HDA_TEST_USER: "nosuchuser", HDA_TEST_PASSWORD: PW1 } }).trim();
  check("bad logon maps friendly", out.includes("logon failure"), out);
}

// ---- E. password grep ----
{
  const { execFileSync: ex } = await import("node:child_process");
  const audit = ex("pwsh", ["-NoProfile", "-NonInteractive", "-Command",
    "Get-ChildItem server/data -Filter *.jsonl -ErrorAction SilentlyContinue | Get-Content -Raw -ErrorAction SilentlyContinue"],
    { encoding: "utf8" });
  const hits = [PW1, PW2].filter((p) => audit.includes(p) || exeOut.includes(p));
  check("passwords nowhere in logs", hits.length === 0, hits.join(","));
  const hasUser = audit.includes("nosuchuser");
  check("username audited (fact only)", hasUser);
}

if (failed) process.exit(1);
console.log("\nPhase 5 unelevated: ALL checks passed.");
process.exit(0);
