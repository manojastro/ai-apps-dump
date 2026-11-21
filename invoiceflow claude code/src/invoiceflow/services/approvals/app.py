"""Approval service and inbox UI.

Run locally: `uv run uvicorn invoiceflow.services.approvals.app:build --factory --port 8080`
then open http://localhost:8080 and paste a dev token (`uv run invoiceflow approvals dev-tokens`).

Server-side controls, before the graph is resumed:
- identity and role come from the token (auth.py), never from the request body;
- only AP Clerk, AP Manager and Finance Controller may decide; Auditors read only;
- the approver's role must meet the case's required role;
- the case must be awaiting approval.
The policy engine then re-checks everything (segregation of duties, authority, the bank
call-back) inside the graph, so a bug here cannot approve on its own.
"""

from pathlib import Path
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict

from invoiceflow.agent.runner import AgentRunner
from invoiceflow.data.models import Role
from invoiceflow.policy.models import Identity
from invoiceflow.services.approvals.auth import Authenticator, AuthError

APPROVER_RANK = {Role.AP_CLERK: 0, Role.AP_MANAGER: 1, Role.FINANCE_CONTROLLER: 2}
READ_ROLES = {*APPROVER_RANK, Role.AUDITOR}


class DecisionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["approve", "reject"]
    comment: str = ""
    verification_performed: bool = False  # bank call-back done by this approver


def create_app(runner: AgentRunner, auth: Authenticator) -> FastAPI:
    app = FastAPI(title="InvoiceFlow approvals", version="1")
    cases = runner.deps.cases

    def caller(authorization: str | None = Header(default=None)) -> Identity:
        try:
            return auth.identify(authorization)
        except AuthError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    def reader(identity: Identity = Depends(caller)) -> Identity:
        if identity.role not in READ_ROLES:
            raise HTTPException(status_code=403, detail=f"{identity.role} cannot view cases")
        return identity

    @app.get("/api/me")
    def me(identity: Identity = Depends(caller)) -> dict[str, Any]:
        return identity.model_dump()

    @app.get("/api/cases")
    def list_cases(
        status: str = "AWAITING_APPROVAL", identity: Identity = Depends(reader)
    ) -> list[dict[str, Any]]:
        return [c.model_dump() for c in cases.list(status)]

    @app.get("/api/cases/{case_id}")
    def get_case(case_id: str, identity: Identity = Depends(reader)) -> dict[str, Any]:
        case = cases.get(case_id)
        if case is None:
            raise HTTPException(status_code=404, detail="no such case")
        trail = [e.model_dump() for e in runner.deps.audit.entries(case_id)]
        return {"case": case.model_dump(), "audit": trail}

    @app.post("/api/cases/{case_id}/decision")
    def decide(
        case_id: str, body: DecisionIn, identity: Identity = Depends(caller)
    ) -> dict[str, Any]:
        if identity.role not in APPROVER_RANK:
            raise HTTPException(status_code=403, detail=f"{identity.role} may not decide cases")
        case = cases.get(case_id)
        if case is None:
            raise HTTPException(status_code=404, detail="no such case")
        if case.status != "AWAITING_APPROVAL":
            raise HTTPException(status_code=409, detail=f"case is {case.status}")
        if identity.id == case.preparer_id:
            raise HTTPException(status_code=403, detail="preparer cannot approve (AP-POL §2.2)")
        required = Role(case.required_role) if case.required_role else Role.AP_CLERK
        if body.decision == "approve" and APPROVER_RANK[identity.role] < APPROVER_RANK.get(
            required, 0
        ):
            raise HTTPException(status_code=403, detail=f"requires {required.value}")
        resume: dict[str, Any] = {
            "decision": body.decision,
            "approver": identity.model_dump(),
            "comment": body.comment,
        }
        if body.verification_performed:
            resume["verification"] = {
                "kind": "BANK_DETAILS_CALLBACK",
                "performed_by": identity.model_dump(),
            }
        outcome = runner.resume(case_id, resume)
        return {
            "case_id": case_id,
            "status": outcome.status,
            "fail_reason": outcome.fail_reason,
            "note": (outcome.interrupt or {}).get("note", ""),
        }

    @app.get("/", response_class=HTMLResponse)
    def inbox() -> str:
        return INBOX_HTML

    return app


INBOX_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>InvoiceFlow approvals</title>
<style>
body{font-family:system-ui,sans-serif;margin:0 auto;max-width:960px;padding:16px;color:#1b1b1b}
h1{font-size:1.3rem} .banner{background:#fff4ce;padding:8px;border-radius:6px}
table{border-collapse:collapse;width:100%} td,th{border-bottom:1px solid #ddd;padding:6px;
text-align:left;vertical-align:top} input,button{font:inherit;padding:4px 8px} pre{white-space:pre-wrap}
</style></head><body>
<h1>InvoiceFlow approval inbox</h1>
<p class="banner">Synthetic data. The ERP is SIMULATED. Nothing here moves real money.</p>
<p><label>Bearer token <input id="tok" size="40" type="password"></label>
<button onclick="load()">Load inbox</button> <span id="who"></span></p>
<table><thead><tr><th>Case</th><th>Proposal</th><th>Needs</th><th>Decide</th></tr></thead>
<tbody id="rows"></tbody></table><pre id="out"></pre>
<script>
const h = () => ({"Authorization": "Bearer " + document.getElementById("tok").value,
                  "Content-Type": "application/json"});
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
async function load(){
  const me = await fetch("/api/me", {headers: h()}); if(!me.ok){out.textContent = await me.text(); return;}
  const m = await me.json(); who.textContent = m.id + " (" + m.role + ")";
  const r = await fetch("/api/cases", {headers: h()}); const cs = await r.json();
  rows.innerHTML = cs.map(c => `<tr><td>${esc(c.case_id)}</td><td><b>${esc(c.summary.exception)}</b> -> ${esc(c.summary.action)}<br>${esc(c.summary.rationale)}<br><small>${esc((c.summary.citations||[]).join(", "))}</small></td>
  <td>${esc(c.required_role)}${c.summary.requires_out_of_band_verification ? "<br>+ bank call-back" : ""}</td>
  <td><label><input type="checkbox" id="v-${esc(c.case_id)}"> call-back done</label><br>
  <button onclick="decide('${esc(c.case_id)}','approve')">Approve</button>
  <button onclick="decide('${esc(c.case_id)}','reject')">Reject</button></td></tr>`).join("");
}
async function decide(id, d){
  const v = document.getElementById("v-" + id); const body = {decision: d, verification_performed: !!(v && v.checked)};
  const r = await fetch(`/api/cases/${encodeURIComponent(id)}/decision`, {method:"POST", headers:h(), body: JSON.stringify(body)});
  out.textContent = await r.text(); load();
}
</script></body></html>"""


def build() -> FastAPI:
    """Factory for uvicorn: local runner, dev-token or OIDC auth from settings."""
    import jwt as pyjwt

    from invoiceflow.agent.wiring import build_runner
    from invoiceflow.config import Settings
    from invoiceflow.services.approvals.auth import DevTokenAuth, OidcAuth

    settings = Settings()
    root = Path(settings.invoiceflow_state_dir)
    auth: Authenticator
    if settings.approvals_auth == "oidc":
        auth = OidcAuth(
            settings.require("oidc_issuer"),
            settings.require("oidc_audience"),
            pyjwt.PyJWKClient(settings.require("oidc_jwks_url")),
        )
    else:
        auth = DevTokenAuth.load_or_create(root / "dev_tokens.json")
    return create_app(build_runner(settings, root), auth)
