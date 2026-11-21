import { randomInt } from "node:crypto";
import type { WebSocket } from "ws";
import { isSixDigitCode, type SessionState } from "./protocol.js";

export interface HostInfo {
  machine: string;
  user: string;
  os: string;
}

export interface Session {
  code: string;
  agentWs: WebSocket | null;
  hostWs: WebSocket | null;
  state: SessionState;
  createdAt: number;
  consentedAt: number | null;
  hostInfo: HostInfo | null;
  agentName: string;
  elevationAttempts: number;
}

const CODE_TTL_MS = 10 * 60 * 1000;
const JOIN_ATTEMPTS_PER_MIN = 5;
const JOIN_WINDOW_MS = 60 * 1000;

const sessions = new Map<string, Session>();
const joinAttempts = new Map<string, number[]>();

export function generateCode(): string {
  for (let i = 0; i < 50; i++) {
    const n: number = randomInt(0, 1_000_000);
    const code: string = n.toString().padStart(6, "0");
    if (!sessions.has(code)) return code;
  }
  const fallback: number = randomInt(0, 1_000_000);
  return fallback.toString().padStart(6, "0");
}

export function createSession(agentWs: WebSocket, agentName: string): Session {
  const code: string = generateCode();
  const s: Session = {
    code,
    agentWs,
    hostWs: null,
    state: "waiting_for_host",
    createdAt: Date.now(),
    consentedAt: null,
    hostInfo: null,
    agentName,
    elevationAttempts: 0,
  };
  sessions.set(code, s);
  return s;
}

export function getSession(code: string): Session | undefined {
  return sessions.get(code);
}

export function isExpired(s: Session, now: number = Date.now()): boolean {
  return (
    s.state === "waiting_for_host" && now - s.createdAt > CODE_TTL_MS
  );
}

export type JoinResult =
  | { ok: true; session: Session }
  | { ok: false; error: string };

function pruneAttempts(ip: string, now: number): number[] {
  const arr: number[] = joinAttempts.get(ip) ?? [];
  const fresh: number[] = arr.filter((t) => now - t < JOIN_WINDOW_MS);
  joinAttempts.set(ip, fresh);
  return fresh;
}

export function checkJoinRateLimit(ip: string): boolean {
  return pruneAttempts(ip, Date.now()).length < JOIN_ATTEMPTS_PER_MIN;
}

function recordJoinAttempt(ip: string): void {
  const now: number = Date.now();
  const fresh: number[] = pruneAttempts(ip, now);
  fresh.push(now);
  joinAttempts.set(ip, fresh);
}

export function tryHostJoin(
  code: unknown,
  hostWs: WebSocket,
  hostInfo: HostInfo,
  ip: string,
): JoinResult {
  recordJoinAttempt(ip);
  if (!checkJoinRateLimitAfterRecord(ip)) {
    return { ok: false, error: "rate_limited" };
  }
  if (!isSixDigitCode(code)) {
    return { ok: false, error: "invalid_code" };
  }
  const s: Session | undefined = sessions.get(code);
  if (s === undefined) {
    return { ok: false, error: "invalid_code" };
  }
  if (isExpired(s)) {
    s.state = "ended";
    sessions.delete(s.code);
    return { ok: false, error: "expired" };
  }
  // Single-use: burn on first successful join. Any non-waiting state rejects.
  if (s.state !== "waiting_for_host") {
    return { ok: false, error: "invalid_code" };
  }
  s.hostWs = hostWs;
  s.hostInfo = hostInfo;
  s.state = "waiting_for_consent";
  return { ok: true, session: s };
}

function checkJoinRateLimitAfterRecord(ip: string): boolean {
  // recordJoinAttempt already pushed; allow up to 5, reject on 6th+.
  const arr: number[] = joinAttempts.get(ip) ?? [];
  return arr.length <= JOIN_ATTEMPTS_PER_MIN;
}

export const MAX_ELEVATION_ATTEMPTS_PER_SESSION = 5;

/** Counts an elevation attempt; returns the new total. */
export function noteElevationAttempt(s: Session): number {
  s.elevationAttempts += 1;
  return s.elevationAttempts;
}

export function setConsent(
  s: Session,
  accepted: boolean,
): void {  if (accepted) {
    s.consentedAt = Date.now();
    s.state = "active";
  } else {
    s.state = "ended";
  }
}

export function endSession(s: Session): void {
  s.state = "ended";
}

export function removeSession(code: string): void {
  sessions.delete(code);
}

export function sweepExpired(): void {
  const now: number = Date.now();
  for (const [code, s] of sessions) {
    if (s.state === "ended") {
      sessions.delete(code);
      continue;
    }
    if (isExpired(s, now)) {
      s.state = "ended";
      sessions.delete(code);
    }
  }
}

export function sessionCount(): number {
  return sessions.size;
}

/** Test-only reset. */
export function __resetForTests(): void {
  sessions.clear();
  joinAttempts.clear();
}
