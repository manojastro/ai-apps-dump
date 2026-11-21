import { spawn } from "node:child_process";
import path from "node:path";
import fs from "node:fs";
const python = path.resolve(
  process.platform === "win32"
    ? ".venv/Scripts/python.exe"
    : ".venv/bin/python",
);
if (!fs.existsSync(python)) {
  console.error("Run npm run bootstrap first.");
  process.exit(1);
}
const children = [];
function start(command, args) {
  const child = spawn(command, args, { stdio: "inherit", windowsHide: true });
  children.push(child);
  child.on("error", (error) => {
    console.error(error.message);
    stop(1);
  });
  child.on("exit", (code) => {
    if (code && !stopping) stop(code);
  });
}
let stopping = false;
function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  for (const child of children) child.kill("SIGTERM");
  setTimeout(() => process.exit(code), 700);
}
process.on("SIGINT", () => stop());
process.on("SIGTERM", () => stop());
start(python, [
  "-m",
  "uvicorn",
  "services.api.main:app",
  "--host",
  "127.0.0.1",
  "--port",
  "8000",
  "--timeout-keep-alive",
  "65",
  "--no-access-log",
]);
start(python, ["-m", "services.worker.runner"]);
start(process.execPath, [
  "node_modules/next/dist/bin/next",
  "dev",
  "--hostname",
  "127.0.0.1",
  "--port",
  "3000",
]);
