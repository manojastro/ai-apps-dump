import { appendFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { getConfig } from "./config.js";
import { redactForLog, type WireMessage } from "./protocol.js";

let ensuredDir: string | null = null;

function auditPath(): string {
  return getConfig().auditPath;
}

function ensureDir(): void {
  const p: string = auditPath();
  const dir: string = path.dirname(p);
  if (ensuredDir === dir) return;
  mkdirSync(dir, { recursive: true });
  ensuredDir = dir;
}

/** Append-only JSONL. Never logs passwords — elevation payloads are redacted. */
export function auditEvent(event: Record<string, unknown>): void {
  try {
    ensureDir();
    const line: string =
      JSON.stringify({ ts: new Date().toISOString(), ...event }) + "\n";
    appendFileSync(auditPath(), line, { encoding: "utf8" });
  } catch {
    // Audit must never crash the relay. Swallow (server logs the failure).
  }
}

/** Redact-then-audit an inbound wire message (fact + result only for elevation). */
export function auditWireMessage(
  direction: string,
  msg: WireMessage,
  extra: Record<string, unknown> = {},
): void {
  const safe: WireMessage = redactForLog(msg);
  // Explicitly drop password even if redaction shape changes in future.
  const { password: _dropped, ...rest } = safe as Record<string, unknown>;
  void _dropped;
  auditEvent({ direction, ...rest, ...extra });
}
