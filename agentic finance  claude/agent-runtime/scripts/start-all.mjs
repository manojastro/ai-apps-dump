// Start each built agent on its own port (self-hosted, local workflow world).
// document-understanding 3101, table-extraction 3102, financial-mapping 3103, reconciliation 3104, analyst-pack 3105.
import { spawn } from "node:child_process";
import { join } from "node:path";

const agents = {
  "document-understanding": 3101,
  "table-extraction": 3102,
  "financial-mapping": 3103,
  reconciliation: 3104,
  "analyst-pack": 3105,
};
const host = process.env.EVE_HOST ?? "127.0.0.1";
for (const [name, port] of Object.entries(agents)) {
  const child = spawn("npx", ["eve", "start", "--host", host, "--port", String(port)], {
    cwd: join(import.meta.dirname, "..", "agents", name),
    stdio: "inherit",
    shell: process.platform === "win32",
  });
  child.on("exit", (code) => console.log(`${name} exited with ${code}`));
}
