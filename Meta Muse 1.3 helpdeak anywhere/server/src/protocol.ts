// Mirrors shared/protocol.md + windows/Shared/Protocol.cs.
// Change all three together.
export const PROTOCOL_VERSION: string = "1.0.0-phase1";

export type Role = "agent" | "host";

export type SessionState =
  | "waiting_for_host"
  | "waiting_for_consent"
  | "active"
  | "ended";

export interface WireMessage {
  t: string;
  [key: string]: unknown;
}

export function isWireMessage(value: unknown): value is WireMessage {
  if (typeof value !== "object" || value === null) return false;
  const rec = value as Record<string, unknown>;
  return typeof rec["t"] === "string";
}

export function getStringField(msg: WireMessage, key: string): string | null {
  const v: unknown = msg[key];
  return typeof v === "string" ? v : null;
}

export function getBoolField(msg: WireMessage, key: string): boolean | null {
  const v: unknown = msg[key];
  return typeof v === "boolean" ? v : null;
}

export function isSixDigitCode(code: unknown): code is string {
  return typeof code === "string" && /^[0-9]{6}$/.test(code);
}

/** Redact credential payloads so they can never reach logs. */
export function redactForLog(msg: WireMessage): WireMessage {
  if (msg.t === "agent.requestElevation") {
    const { password: _pw, ...rest } = msg;
    void _pw;
    return { ...rest, password: "[REDACTED]" };
  }
  return msg;
}
