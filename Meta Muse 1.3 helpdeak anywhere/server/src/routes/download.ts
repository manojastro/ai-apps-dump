import { Router } from "express";

// Phase 0 scaffold — download routes land in Phase 1 (served by Caddy in prod).
export const downloadRouter: Router = Router();

downloadRouter.get("/healthz-download", (_req, res): void => {
  res.json({ ok: true, scope: "download-scaffold" });
});
