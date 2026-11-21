import { spawnSync } from "node:child_process";
const steps = [
  ["uv", ["sync", "--locked"]],
  [
    process.platform === "win32"
      ? ".venv/Scripts/python.exe"
      : ".venv/bin/python",
    ["-m", "services.api.setup"],
  ],
];
for (const [command, args] of steps) {
  const r = spawnSync(command, args, { stdio: "inherit", windowsHide: true });
  if (r.status !== 0) process.exit(r.status || 1);
}
