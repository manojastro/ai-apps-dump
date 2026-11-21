#!/usr/bin/env node
// Phase 3 end-to-end (no human): real Chromium drives the agent portal,
// real Applet.exe --headless --video streams the desktop. Asserts the browser
// actually renders frames: status flips to Connected, FPS counter moves,
// two canvas screenshots differ and are non-trivially sized.
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import path from "node:path";
import { chromium } from "playwright";

const args = process.argv.slice(2);
function opt(name, def) {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? String(args[i + 1]) : def;
}
const HTTP_BASE = opt("--http", "http://127.0.0.1:18086");
const WS_URL = opt("--url", "ws://127.0.0.1:18086/ws");
const EXE = opt("--exe", path.resolve("server/public/download/HelpdeskAnywhere.exe"));

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.on("pageerror", (e) => console.log("[pageerror]", String(e?.message ?? e).slice(0, 200)));
  await page.goto(HTTP_BASE + "/", { waitUntil: "domcontentloaded" });
  await page.fill("#agentName", "E2E-Browser");
  await page.click("#start");
  await page.waitForFunction(
    () => /^[0-9]{6}$/.test(document.getElementById("code")?.textContent ?? ""),
    null,
    { timeout: 10000 },
  );
  const code = (await page.textContent("#code"))?.trim();
  console.log(`portal session code=${code}`);
  const joinHref = await page.getAttribute("#joinUrl", "href");
  if (!joinHref?.endsWith(`/j/${code}`)) throw new Error(`bad join link ${joinHref}`);

  const exe = spawn(EXE, [
    "--headless", "--server", WS_URL, "--code", code,
    "--accept", "--video", "--duration", "30",
  ], { stdio: ["ignore", "pipe", "pipe"] });
  let exeOut = "";
  exe.stdout.on("data", (d) => { exeOut += String(d); });
  exe.stderr.on("data", (d) => { exeOut += String(d); });
  const exeDone = new Promise((resolve) => {
    const t = setTimeout(() => resolve(124), 45000);
    exe.on("close", (c) => { clearTimeout(t); resolve(c ?? 1); });
  });

  await page.waitForFunction(
    () => (document.getElementById("status")?.textContent ?? "").includes("Connected"),
    null,
    { timeout: 20000 },
  );
  console.log("portal status=Connected");
  // Let frames accumulate while the wrapper jiggles the cursor.
  await page.waitForTimeout(8000);
  const stats1 = ((await page.textContent("#stats")) ?? "").trim();
  const shot1 = await page.locator("#screen").screenshot();
  await page.waitForTimeout(2500);
  const stats2 = ((await page.textContent("#stats")) ?? "").trim();
  const shot2 = await page.locator("#screen").screenshot();
  console.log(`stats: '${stats1}' -> '${stats2}'`);
  console.log(`screenshots: ${shot1.length} bytes, ${shot2.length} bytes`);

  const h1 = createHash("sha256").update(shot1).digest("hex");
  const h2 = createHash("sha256").update(shot2).digest("hex");
  const m1 = /FPS:\s*(\d+)/.exec(stats2);
  const fps = m1 ? Number(m1[1]) : -1;

  let failed = false;
  const check = (name, cond, detail = "") => {
    console.log(`${cond ? "PASS" : "FAIL"}: ${name}${detail ? " — " + detail : ""}`);
    if (!cond) failed = true;
  };
  check("portal Connected", true);
  check("canvas non-blank", shot1.length > 10000, `${shot1.length} bytes`);
  check("canvas changes over time", h1 !== h2);
  check("FPS counter shows traffic", fps >= 1, `FPS=${fps}`);
  // Clean end from the agent side; exe should already be near its --duration exit.
  await page.click("#end").catch(() => {});
  const exit = await exeDone;
  check("exe clean exit", exit === 0, `exit=${exit}\n${exeOut.slice(0, 500)}`);
  if (/ObjectDisposedException|Unhandled exception/i.test(exeOut)) {
    check("exe no teardown crash", false, exeOut.slice(0, 300));
  }
  if (failed) process.exit(1);
  console.log("\nPhase 3 e2e: ALL browser-render checks passed.");
  process.exit(0);
} finally {
  await browser.close().catch(() => {});
}
