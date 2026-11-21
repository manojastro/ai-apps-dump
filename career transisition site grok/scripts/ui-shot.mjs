import { chromium } from "@playwright/test";
import fs from "node:fs";

const out = "scripts/shots";
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch();

async function shot(name, viewport, path, after) {
  const page = await browser.newPage({ viewport });
  await page.goto("http://127.0.0.1:3010" + path, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(1200);
  if (after) await after(page);
  await page.screenshot({ path: `${out}/${name}.png`, fullPage: false });
  await page.close();
}

async function onboard(page) {
  if (await page.getByText("First run").isVisible().catch(() => false)) {
    for (let i = 0; i < 5; i += 1) {
      await page.getByRole("button", { name: "Continue" }).click();
    }
    await page.getByRole("button", { name: "Start Clean" }).click();
    await page.getByText("AI Career Transition").waitFor();
  }
}

await shot("desktop-onboard", { width: 1440, height: 900 }, "/", async () => {});
await shot("desktop-dash", { width: 1440, height: 900 }, "/", onboard);
await shot("desktop-jobs", { width: 1440, height: 900 }, "/jobs", onboard);
await shot("mobile-dash", { width: 390, height: 844 }, "/", onboard);
await browser.close();
console.log("ok");
