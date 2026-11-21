import fs from "node:fs";
import path from "node:path";

const skipDirs = new Set(["node_modules", ".next", "coverage", ".git", "playwright-report", "test-results", "scripts"]);
const skipFiles = new Set([
  "MASTER PROMPT.txt",
  "GROK-BUILD-STARTER-PROMPT.md",
  "GROK-BUILD-VERCEL-ADDENDUM.md",
  "package-lock.json",
  "tsconfig.tsbuildinfo",
  "_vercel_files.json",
]);

function walk(dir, out) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    if (skipDirs.has(ent.name)) continue;
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) walk(p, out);
    else if (!skipFiles.has(ent.name)) out.push(p);
  }
}

const files = [];
walk(".", files);
let bytes = 0;
const payload = files.map((abs) => {
  const file = abs.split(path.sep).join("/");
  const data = fs.readFileSync(abs, "utf8");
  bytes += Buffer.byteLength(data);
  return { file, data };
});
fs.writeFileSync("_vercel_meta.json", JSON.stringify({ count: payload.length, bytes, files: payload.map((f) => f.file) }, null, 2));
fs.writeFileSync("_vercel_files.json", JSON.stringify(payload));
console.log("count", payload.length, "bytes", bytes);
