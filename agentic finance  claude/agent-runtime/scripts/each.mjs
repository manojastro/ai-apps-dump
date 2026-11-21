// Run an eve CLI command in every workspace member: `node scripts/each.mjs info` / `build`.
import { spawnSync } from "node:child_process";
import { readdirSync } from "node:fs";
import { join } from "node:path";

const cmd = process.argv.slice(2);
const root = join(import.meta.dirname, "..", "agents");
let failed = 0;
for (const name of readdirSync(root)) {
  console.log(`\n=== ${name}: eve ${cmd.join(" ")}`);
  const r = spawnSync("npx", ["eve", ...cmd], { cwd: join(root, name), stdio: "inherit", shell: process.platform === "win32" });
  if (r.status !== 0) failed++;
}
process.exit(failed ? 1 : 0);
