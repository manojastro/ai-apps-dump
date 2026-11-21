import { createServer, type Server } from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import express, { type Express } from "express";
import { WebSocketServer } from "ws";
import { getConfig } from "./config.js";
import { downloadRouter } from "./routes/download.js";
import { portalRouter } from "./routes/portal.js";
import { sweepExpired } from "./sessions.js";
import { handleConnection, startHeartbeat } from "./signaling.js";

const __filename: string = fileURLToPath(import.meta.url);
const __dirname: string = path.dirname(__filename);
// src/ -> ../public when running from dist/ or src/
const publicDir: string = path.resolve(__dirname, "..", "public");

export function createApp(): Express {
  const app: Express = express();
  app.use(express.json({ limit: "256kb" }));

  app.get("/healthz", (_req, res): void => {
    res.json({ ok: true, phase: 1 });
  });

  // Join page at path-style URL (easier to read aloud on support calls).
  app.get("/j/:code", (_req, res): void => {
    res.sendFile(path.join(publicDir, "join.html"));
  });

  // Agent console at root.
  app.get("/", (_req, res): void => {
    res.sendFile(path.join(publicDir, "portal.html"));
  });

  app.use("/api/portal", portalRouter);
  app.use("/api/download", downloadRouter);

  // Static: portal.js/css, join.html, download/* (Caddy serves download in prod).
  app.use(express.static(publicDir, { dotfiles: "deny", index: false }));

  return app;
}

function clientIp(req: { headers: Record<string, unknown>; socket: { remoteAddress?: string } }): string {
  const fwd: unknown = req.headers["x-forwarded-for"];
  if (typeof fwd === "string" && fwd.length > 0) {
    const first: string = fwd.split(",")[0]?.trim() ?? "";
    if (first.length > 0) return first;
  }
  return req.socket.remoteAddress ?? "unknown";
}

function isTlsRequest(req: {
  headers: Record<string, unknown>;
  socket: { encrypted?: boolean };
}): boolean {
  const proto: unknown = req.headers["x-forwarded-proto"];
  if (typeof proto === "string" && proto.toLowerCase().startsWith("https")) return true;
  if (req.socket.encrypted === true) return true;
  return false;
}

const app: Express = createApp();
const server: Server = createServer(app);
const wss = new WebSocketServer({ noServer: true });

server.on("upgrade", (req, socket, head) => {
  let pathname = "";
  try {
    const url = new URL(req.url ?? "/", "http://localhost");
    pathname = url.pathname;
  } catch {
    socket.destroy();
    return;
  }
  if (pathname !== "/ws") {
    socket.destroy();
    return;
  }
  wss.handleUpgrade(req, socket, head, (ws) => {
    const ip: string = clientIp({
      headers: req.headers as Record<string, unknown>,
      socket: req.socket,
    });
    const tls: boolean = isTlsRequest({
      headers: req.headers as Record<string, unknown>,
      socket: req.socket as { encrypted?: boolean },
    });
    wss.emit("connection", ws, req);
    handleConnection(ws, ip, tls);
  });
});

setInterval(() => {
  sweepExpired();
}, 60_000).unref?.();

startHeartbeat(wss, 20_000);

const { port } = getConfig();
server.listen(port, (): void => {
  console.log(`helpdesk-anywhere server (phase1) listening on :${port.toString()}`);
});
