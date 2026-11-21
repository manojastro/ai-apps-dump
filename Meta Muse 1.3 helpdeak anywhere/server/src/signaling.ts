import type { WebSocket, WebSocketServer } from "ws";
import { auditEvent, auditWireMessage } from "./audit.js";
import {
  getBoolField,
  getStringField,
  isWireMessage,
  redactForLog,
  type WireMessage,
} from "./protocol.js";
import {
  createSession,
  endSession,
  getSession,
  MAX_ELEVATION_ATTEMPTS_PER_SESSION,
  noteElevationAttempt,
  removeSession,
  setConsent,
  tryHostJoin,
  type HostInfo,
  type Session,
} from "./sessions.js";

interface ConnMeta {
  role: "agent" | "host" | null;
  code: string | null;
  isAlive: boolean;
  ip: string;
}

const meta = new Map<WebSocket, ConnMeta>();

function sendJson(ws: WebSocket, msg: WireMessage): void {
  if (ws.readyState !== ws.OPEN) return;
  try {
    ws.send(JSON.stringify(msg));
  } catch {
    // ignore send failures; close handler will clean up
  }
}

function sendError(ws: WebSocket, error: string): void {
  sendJson(ws, { t: "error", error });
}

function peerOf(s: Session, ws: WebSocket): WebSocket | null {
  if (ws === s.agentWs) return s.hostWs;
  if (ws === s.hostWs) return s.agentWs;
  return null;
}

function closeBoth(s: Session, reason: string): void {
  endSession(s);
  for (const sock of [s.agentWs, s.hostWs] as const) {
    if (sock !== null && sock.readyState === sock.OPEN) {
      try {
        sendJson(sock, { t: "peer.left", reason });
      } catch {
        // ignore
      }
    }
  }
  for (const sock of [s.agentWs, s.hostWs] as const) {
    if (sock !== null) {
      try {
        sock.close(1000, reason);
      } catch {
        // ignore
      }
    }
  }
  auditEvent({ event: "session.ended", code: s.code, reason });
  removeSession(s.code);
}

export function handleConnection(
  ws: WebSocket,
  ip: string,
  isTls: boolean,
): void {
  meta.set(ws, { role: null, code: null, isAlive: true, ip });
  ws.on("pong", () => {
    const m: ConnMeta | undefined = meta.get(ws);
    if (m !== undefined) m.isAlive = true;
  });
  ws.on("message", (data: Buffer | ArrayBuffer | Buffer[] | string, isBinary: boolean) => {
    handleMessage(ws, data, isBinary, isTls);
  });
  ws.on("close", () => {
    handleClose(ws);
  });
  ws.on("error", () => {
    handleClose(ws);
  });
}

function handleMessage(ws: WebSocket, data: Buffer | ArrayBuffer | Buffer[] | string, isBinary: boolean, isTls: boolean): void {
  const m: ConnMeta | undefined = meta.get(ws);
  if (m === undefined) return;
  // Any inbound traffic proves liveness (belts-and-braces alongside pong).
  m.isAlive = true;

  // Binary frames (video): relay only when active, else drop.
  // Note: ws delivers TEXT frames as Buffer too — must branch on isBinary, not type.
  if (isBinary) {
    let bin: Buffer;
    if (Buffer.isBuffer(data)) bin = data;
    else if (data instanceof ArrayBuffer) bin = Buffer.from(data);
    else if (Array.isArray(data)) bin = Buffer.concat(data);
    else bin = Buffer.from(String(data), "utf8");
    const session: Session | null = sessionFor(ws);
    if (session === null || session.state !== "active") return;
    const peer: WebSocket | null = peerOf(session, ws);
    if (peer !== null && peer.readyState === peer.OPEN) {
      try {
        peer.send(bin, { binary: true });
      } catch {
        // ignore
      }
    }
    return;
  }

  const text: string =
    typeof data === "string"
      ? data
      : Buffer.isBuffer(data)
        ? data.toString("utf8")
        : Array.isArray(data)
          ? Buffer.concat(data).toString("utf8")
          : Buffer.from(data as ArrayBuffer).toString("utf8");
  let parsed: unknown;
  try {
    parsed = JSON.parse(text) as unknown;
  } catch {
    sendError(ws, "bad_json");
    return;
  }
  if (!isWireMessage(parsed)) {
    sendError(ws, "bad_message");
    return;
  }
  const msg: WireMessage = parsed;

  // Never log passwords.
  const logged: WireMessage = redactForLog(msg);
  void logged;

  switch (msg.t) {
    case "agent.create": {
      if (m.code !== null) {
        sendError(ws, "already_in_session");
        return;
      }
      const agentName: string = getStringField(msg, "agentName") ?? "Agent";
      const s: Session = createSession(ws, agentName);
      m.role = "agent";
      m.code = s.code;
      sendJson(ws, { t: "session.created", code: s.code });
      auditEvent({ event: "session.created", code: s.code, agentName });
      return;
    }
    case "host.join": {
      if (m.code !== null) {
        sendError(ws, "already_in_session");
        return;
      }
      const codeRaw: unknown = msg["code"];
      const machine: string = getStringField(msg, "machine") ?? "unknown";
      const user: string = getStringField(msg, "user") ?? "unknown";
      const os: string = getStringField(msg, "os") ?? "unknown";
      const hostInfo: HostInfo = { machine, user, os };
      const result = tryHostJoin(codeRaw, ws, hostInfo, m.ip);
      if (!result.ok) {
        sendError(ws, result.error);
        auditEvent({ event: "host.join.rejected", reason: result.error, ip: m.ip });
        return;
      }
      const s: Session = result.session;
      m.role = "host";
      m.code = s.code;
      // To host: connect request naming the agent.
      sendJson(ws, { t: "host.connectRequest", agentName: s.agentName });
      // To agent: peer joined.
      if (s.agentWs !== null) {
        sendJson(s.agentWs, {
          t: "peer.joined",
          role: "host",
          machine,
          user,
          os,
        });
      }
      auditEvent({
        event: "session.joined",
        code: s.code,
        machine,
        user,
        os,
      });
      return;
    }
    case "host.consent": {
      const s: Session | null = sessionFor(ws);
      if (s === null || m.role !== "host") {
        sendError(ws, "no_session");
        return;
      }
      if (s.state !== "waiting_for_consent") {
        sendError(ws, "bad_state");
        return;
      }
      const accepted: boolean | null = getBoolField(msg, "accepted");
      if (accepted === null) {
        sendError(ws, "bad_message");
        return;
      }
      setConsent(s, accepted);
      auditEvent({ event: "session.consent", code: s.code, accepted });
      if (s.agentWs !== null) {
        sendJson(s.agentWs, { t: "consent.result", accepted });
      }
      if (!accepted) {
        closeBoth(s, "consent_declined");
      } else {
        // Notify both that the peer is present (agent already got peer.joined on join).
        sendJson(ws, { t: "peer.joined", role: "agent" });
      }
      return;
    }
    case "agent.end": {
      const s: Session | null = sessionFor(ws);
      if (s === null) {
        sendError(ws, "no_session");
        return;
      }
      closeBoth(s, "agent_ended");
      return;
    }
    case "agent.requestElevation": {
      const s: Session | null = sessionFor(ws);
      if (s === null) {
        sendError(ws, "no_session");
        return;
      }
      // Audit fact/result only — never the password.
      auditWireMessage("agent->server", msg, { code: s.code });
      // Rate-limit elevation attempts per session (5.2c): an unauthenticated
      // portal plus unlimited attempts would be an online password guesser.
      if (noteElevationAttempt(s) > MAX_ELEVATION_ATTEMPTS_PER_SESSION) {
        auditEvent({ event: "elevation.rate_limited", code: s.code });
        sendError(ws, "rate_limited");
        return;
      }
      const mode: string | null = getStringField(msg, "mode");
      if (mode === "credential" && !isTls) {
        sendError(ws, "tls_required");
        return;
      }
      if (s.state !== "active") return; // drop before active
      const peer: WebSocket | null = peerOf(s, ws);
      if (peer !== null) sendJson(peer, msg);
      return;
    }
    case "agent.exec": {
      const s: Session | null = sessionFor(ws);
      if (s === null) {
        sendError(ws, "no_session");
        return;
      }
      auditWireMessage("agent->server", msg, { code: s.code });
      if (s.state !== "active") return;
      const peer: WebSocket | null = peerOf(s, ws);
      if (peer !== null) sendJson(peer, msg);
      return;
    }
    case "agent.sas": {
      // Software Secure Attention Sequence (Phase 5): audit the fact, relay
      // only when elevated streaming is active (the applet enforces the rest).
      const s: Session | null = sessionFor(ws);
      if (s === null) {
        sendError(ws, "no_session");
        return;
      }
      auditWireMessage("agent->server", msg, { code: s.code });
      if (s.state !== "active") return;
      const peer: WebSocket | null = peerOf(s, ws);
      if (peer !== null) sendJson(peer, msg);
      return;
    }
    default: {
      // Generic relay for paired control messages when active.
      const s: Session | null = sessionFor(ws);
      if (s === null) {
        sendError(ws, "no_session");
        return;
      }
      if (s.state !== "active") {
        // Drop pre-active frames (Phase 1 rule). Inform sender for testability.
        sendError(ws, "not_active");
        return;
      }
      const peer: WebSocket | null = peerOf(s, ws);
      if (peer === null) {
        sendError(ws, "peer_left");
        return;
      }
      sendJson(peer, msg);
    }
  }
}

function sessionFor(ws: WebSocket): Session | null {
  const m: ConnMeta | undefined = meta.get(ws);
  if (m === undefined || m.code === null) return null;
  const s: Session | undefined = getSession(m.code);
  return s ?? null;
}

function handleClose(ws: WebSocket): void {
  const m: ConnMeta | undefined = meta.get(ws);
  meta.delete(ws);
  if (m === undefined || m.code === null) return;
  const s: Session | undefined = getSession(m.code);
  if (s === undefined) return;
  // If this socket is part of the session, tear down both sides.
  if (s.agentWs === ws || s.hostWs === ws) {
    auditEvent({
      event: "session.dropped",
      code: m.code,
      role: m.role ?? "unknown",
      state: s.state,
    });
    closeBoth(s, "peer_disconnected");
  }
}

export function startHeartbeat(wss: WebSocketServer, ms = 20_000): NodeJS.Timeout {
  const timer: NodeJS.Timeout = setInterval(() => {
    wss.clients.forEach((ws: WebSocket) => {
      const m: ConnMeta | undefined = meta.get(ws);
      if (m === undefined) return;
      if (!m.isAlive) {
        auditEvent({
          event: "heartbeat.terminated",
          role: m.role ?? "unknown",
          code: m.code,
        });
        try {
          ws.terminate();
        } catch {
          // ignore
        }
        return;
      }
      m.isAlive = false;
      try {
        ws.ping();
      } catch {
        // ignore
      }
    });
  }, ms);
  timer.unref?.();
  return timer;
}
