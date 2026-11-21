#!/usr/bin/env node
// Tiny mock host for Phase 1 acceptance (no deps, uses Node 22 global WebSocket).
// Usage:
//   node scripts/mock-host.js --url ws://127.0.0.1:8080/ws --code 482913 [--consent true|false] [--expect-error invalid_code]
const args = process.argv.slice(2);
function opt(name, def) {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? String(args[i + 1]) : def;
}
const url = opt("--url", "ws://127.0.0.1:8080/ws");
const code = opt("--code", "");
const consent = opt("--consent", "true") !== "false";
const expectError = opt("--expect-error", "");
const machine = opt("--machine", "TEST-PC");
const user = opt("--user", "tester");
const os = opt("--os", "Windows 11");

if (!/^[0-9]{6}$/.test(code) && !expectError) {
  console.error("mock-host: --code must be 6 digits");
  process.exit(2);
}

const ws = new WebSocket(url);
const timer = setTimeout(() => {
  console.error("mock-host: timeout waiting for server");
  try { ws.close(); } catch {}
  process.exit(1);
}, 8000);

ws.onopen = () => {
  ws.send(JSON.stringify({ t: "host.join", code, machine, user, os }));
};
ws.onmessage = (ev) => {
  let msg;
  try { msg = JSON.parse(String(ev.data)); } catch { return; }
  console.log("mock-host recv:", JSON.stringify(msg));
  if (msg && msg.t === "error") {
    clearTimeout(timer);
    if (expectError && String(msg.error || "").includes(expectError)) {
      console.log(`mock-host: got expected error '${msg.error}'`);
      try { ws.close(); } catch {}
      process.exit(0);
    }
    console.error(`mock-host: unexpected error '${msg.error}' (expected '${expectError || "(none)"}')`);
    try { ws.close(); } catch {}
    process.exit(1);
  }
  if (msg && msg.t === "host.connectRequest") {
    if (expectError) {
      console.error("mock-host: expected error but got connectRequest");
      clearTimeout(timer);
      try { ws.close(); } catch {}
      process.exit(1);
    }
    ws.send(JSON.stringify({ t: "host.consent", accepted: consent }));
    if (!consent) {
      clearTimeout(timer);
      console.log("mock-host: sent consent:false");
      setTimeout(() => { try { ws.close(); } catch {} process.exit(0); }, 500);
    }
    return;
  }
  if (msg && (msg.t === "peer.joined" || msg.t === "consent.result")) {
    // consent:true flow stays open briefly so the agent side can observe, then exits 0.
    if (!expectError) {
      clearTimeout(timer);
      console.log("mock-host: paired OK");
      setTimeout(() => { try { ws.close(); } catch {} process.exit(0); }, 800);
    }
  }
};
ws.onerror = (e) => {
  console.error("mock-host: ws error", e?.message ?? e);
};
ws.onclose = () => {
  // If we were expecting an error and never got one, fail (unless already exited).
};
