import path from "node:path";

export interface AppConfig {
  port: number;
  publicHost: string;
  auditPath: string;
}

export function getConfig(): AppConfig {
  const portRaw: string | undefined = process.env["PORT"];
  const parsed: number = portRaw !== undefined ? Number(portRaw) : 8080;
  const port: number = Number.isInteger(parsed) && parsed > 0 ? parsed : 8080;
  const publicHost: string = process.env["PUBLIC_HOST"] ?? "localhost";
  const auditRaw: string | undefined = process.env["AUDIT_PATH"];
  const auditPath: string =
    auditRaw !== undefined && auditRaw.length > 0
      ? auditRaw
      : path.join("data", "audit.jsonl");
  return { port, publicHost, auditPath };
}
