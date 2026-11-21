#!/usr/bin/env node
// Phase 4 portal-side check: synthetic DOM events on the canvas must produce
// the exact agent.input wire sequence at a mock host. No exe needed.
import { chromium } from "playwright";

const args = process.argv.slice(2);
function opt(name, def) {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? String(args[i + 1]) : def;
}
const HTTP_BASE = opt("--http", "http://127.0.0.1:18097");
const WS_URL = opt("--url", "ws://127.0.0.1:18097/ws");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const received = [];
const host = new WebSocket(WS_URL);
await new Promise((res, rej) => {
  const t = setTimeout(() => rej(new Error("host connect timeout")), 5000);
  host.onopen = () => { clearTimeout(t); res(null); };
  host.onerror = () => { clearTimeout(t); rej(new Error("host connect error")); };
});
host.onmessage = (ev) => {
  try {
    const m = JSON.parse(String(ev.data));
    if (m.t === "host.connectRequest") host.send(JSON.stringify({ t: "host.consent", accepted: true }));
    if (m.t === "agent.input") received.push(m);
  } catch {}
};

const browser = await chromium.launch({ headless: true });
let failed = false;
const check = (name, cond, detail = "") => {
  console.log(`${cond ? "PASS" : "FAIL"}: ${name}${detail ? " — " + detail : ""}`);
  if (!cond) failed = true;
};
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.on("pageerror", (e) => console.log("[pageerror]", String(e?.message ?? e).slice(0, 160)));
  await page.goto(HTTP_BASE + "/", { waitUntil: "domcontentloaded" });
  await page.fill("#agentName", "E2E-Input");
  await page.click("#start");
  await page.waitForFunction(
    () => /^[0-9]{6}$/.test(document.getElementById("code")?.textContent ?? ""),
    null, { timeout: 10000 },
  );
  const code = (await page.textContent("#code")).trim();
  host.send(JSON.stringify({ t: "host.join", code, machine: "M", user: "U", os: "O" }));
  await page.waitForFunction(
    () => (document.getElementById("status")?.textContent ?? "").includes("Connected"),
    null, { timeout: 15000 },
  );
  check("portal connected with mock host", true);

  const box = await page.locator("#screen").boundingBox();
  const bw = await page.evaluate(() => ({ w: document.getElementById("screen").width, h: document.getElementById("screen").height }));
  const sx = bw.w / box.width;
  const sy = bw.h / box.height;
  const cx = box.x + box.width / 2;
  const cy = box.y + box.height / 2;
  const wantX = Math.round(box.width / 2 * sx);
  const wantY = Math.round(box.height / 2 * sy);

  received.length = 0;
  await page.mouse.move(cx, cy);
  await sleep(300);
  const moves = received.filter((m) => m.kind === "mouse-move");
  const last = moves[moves.length - 1] ?? {};
  check("mousemove maps via backing ratio", Math.abs((last.x ?? -99) - wantX) <= 2 && Math.abs((last.y ?? -99) - wantY) <= 2,
    `want (${wantX},${wantY}) got (${last.x},${last.y})`);

  received.length = 0;
  await page.mouse.click(cx, cy, { button: "left" });
  await sleep(300);
  check("left click down/up",
    received.some((m) => m.kind === "mouse-down" && m.button === "left") &&
    received.some((m) => m.kind === "mouse-up" && m.button === "left"),
    JSON.stringify(received.map((m) => `${m.kind}:${m.button ?? ""}`)));

  received.length = 0;
  await page.mouse.click(cx, cy, { button: "right" });
  await sleep(300);
  check("right click down/up",
    received.some((m) => m.kind === "mouse-down" && m.button === "right") &&
    received.some((m) => m.kind === "mouse-up" && m.button === "right"));

  received.length = 0;
  await page.mouse.move(cx, cy);
  await page.mouse.wheel(0, 100);
  await sleep(300);
  const wheels = received.filter((m) => m.kind === "wheel");
  check("wheel dy=100", wheels.length >= 1 && wheels[0].dy === 100, JSON.stringify(wheels[0] ?? null));

  received.length = 0;
  await page.click("#screen"); // focus canvas
  await page.keyboard.press("a");
  await sleep(300);
  const keySeq = received.filter((m) => m.kind.startsWith("key-")).map((m) => `${m.kind}:${m.code}`).join(",");
  check("key press sends event.code", keySeq.includes("key-down:KeyA") && keySeq.includes("key-up:KeyA"), keySeq);

  received.length = 0;
  await page.keyboard.down("Shift");
  await page.keyboard.press("A");
  await page.keyboard.up("Shift");
  await sleep(300);
  const modSeq = received.filter((m) => m.kind.startsWith("key-")).map((m) => `${m.kind}:${m.code}`).join(",");
  check("shift+letter combo order", modSeq === "key-down:ShiftLeft,key-down:KeyA,key-up:KeyA,key-up:ShiftLeft", modSeq);

  received.length = 0;
  await page.click("#keyAltTab");
  await sleep(300);
  const combo = received.filter((m) => m.kind.startsWith("key-")).map((m) => `${m.kind}:${m.code}`).join(",");
  check("Alt+Tab button sequence", combo === "key-down:AltLeft,key-down:Tab,key-up:Tab,key-up:AltLeft", combo);

  check("CAD button disabled pre-elevation", await page.isDisabled("#keyCAD"));
  check("Win button enabled when active", await page.isEnabled("#keyWin"));
} finally {
  await browser.close().catch(() => {});
  try { host.close(); } catch {}
}
process.exit(failed ? 1 : 0);
