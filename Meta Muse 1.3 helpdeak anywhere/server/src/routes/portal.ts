import { Router } from "express";

// Phase 0 scaffold — agent portal routes land in Phase 1.
export const portalRouter: Router = Router();

portalRouter.get("/healthz-portal", (_req, res): void => {
  res.json({ ok: true, scope: "portal-scaffold" });
});
