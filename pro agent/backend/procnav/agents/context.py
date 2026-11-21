"""Per-run execution context: DB-backed step sink, budgets, cancellation and model accounting."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from ..browser.tools import (
    BudgetExhausted,
    HumanHandoff,
    RunCanceled,
    StepSink,
    SupplierHandle,
    ToolResult,
)
from ..core.audit import run_event
from ..core.config import REPO_ROOT, Settings, get_settings
from ..core.db import tenant_session
from ..core.models import (
    BrowserSessionState,
    BrowserStep,
    PolicyVersion,
    ProcurementRequest,
    ProcurementRun,
    Supplier,
    SupplierCredentialMetadata,
)
from ..evidence import store
from .models import Decision, ModelAdapter, build_model

FIXTURES = Path(REPO_ROOT) / "fixtures"


def load_master_data() -> tuple[dict[str, Any], dict[str, Any]]:
    sku_map = json.loads((FIXTURES / "sku_map.json").read_text(encoding="utf-8"))
    canonical = json.loads((FIXTURES / "canonical_products.json").read_text(encoding="utf-8"))
    sku_map.pop("_comment", None)
    canonical.pop("_comment", None)
    return sku_map, canonical


class DbSink(StepSink):
    def __init__(self, ctx: RunContext):
        self.ctx = ctx

    def before_action(self, tool: str, side_effect: bool) -> None:
        s = self.ctx.settings
        with tenant_session(self.ctx.tenant_id) as db:
            run = db.get(ProcurementRun, self.ctx.run_id)
            if run.cancel_requested and not side_effect:
                raise RunCanceled()
            if run.pause_requested and not side_effect:
                raise HumanHandoff("paused_by_user", "Paused by a user; resume from the run page.")
            run.action_count += 1
            if run.action_count > s.max_browser_actions:
                raise BudgetExhausted("browser_actions", f"Reached the {s.max_browser_actions}-action budget")
            if run.active_ms > s.active_run_timeout_seconds * 1000:
                raise BudgetExhausted("active_time", f"Reached {s.active_run_timeout_seconds}s of active browsing")

    def record(
        self, result: ToolResult, *, supplier_key, tool_input, side_effect, explanation, decided_by, observation
    ) -> int:
        with tenant_session(self.ctx.tenant_id) as db:
            seq = (db.scalar(select(func.max(BrowserStep.seq)).where(BrowserStep.run_id == self.ctx.run_id)) or 0) + 1
            db.add(
                BrowserStep(
                    tenant_id=self.ctx.tenant_id,
                    run_id=self.ctx.run_id,
                    seq=seq,
                    supplier_key=supplier_key,
                    tool=result.tool,
                    side_effect=side_effect,
                    input=tool_input,
                    status=result.status,
                    observation={"result": _jsonable(result.data), "page": observation, "message": result.message},
                    error_code=result.error_code,
                    url=(result.url or "")[:500],
                    evidence_ids=result.evidence_ids,
                    explanation=explanation,
                    decided_by=decided_by,
                    started_at=result.at,
                    duration_ms=result.duration_ms,
                )
            )
            run = db.get(ProcurementRun, self.ctx.run_id)
            run.active_ms += result.duration_ms
            run.current_supplier = supplier_key
            run_event(
                db,
                self.ctx.tenant_id,
                self.ctx.run_id,
                "step",
                {
                    "seq": seq,
                    "tool": result.tool,
                    "status": result.status,
                    "supplier": supplier_key,
                    "error_code": result.error_code,
                    "message": result.message,
                    "evidence_ids": result.evidence_ids,
                    "explanation": explanation,
                    "duration_ms": result.duration_ms,
                },
            )
        return seq

    def save_evidence(self, kind, label, data, content_type, ext) -> str:
        with tenant_session(self.ctx.tenant_id) as db:
            art = store.save(
                db,
                tenant_id=self.ctx.tenant_id,
                run_id=self.ctx.run_id,
                kind=kind,
                label=label,
                data=data,
                content_type=content_type,
                ext=ext,
            )
            return str(art.id)

    def load_state(self, supplier: SupplierHandle) -> bytes | None:
        with tenant_session(self.ctx.tenant_id) as db:
            row = db.scalar(select(BrowserSessionState).where(BrowserSessionState.supplier_id == supplier.id))
            if row is None or row.expires_at <= datetime.now(UTC):
                return None
            return row.encrypted_state

    def store_state(self, supplier: SupplierHandle, encrypted: bytes, ttl_seconds: int) -> None:
        with tenant_session(self.ctx.tenant_id) as db:
            meta = db.scalar(
                select(SupplierCredentialMetadata).where(SupplierCredentialMetadata.supplier_id == supplier.id)
            )
            ttl = min(ttl_seconds, meta.session_retention_seconds if meta else ttl_seconds)
            row = db.scalar(select(BrowserSessionState).where(BrowserSessionState.supplier_id == supplier.id))
            expires = datetime.now(UTC) + timedelta(seconds=ttl)
            if row is None:
                db.add(
                    BrowserSessionState(
                        tenant_id=self.ctx.tenant_id,
                        supplier_id=supplier.id,
                        encrypted_state=encrypted,
                        expires_at=expires,
                    )
                )
            else:
                row.encrypted_state, row.expires_at, row.updated_at = encrypted, expires, datetime.now(UTC)

    def note_recovery(self, kind: str) -> None:
        with tenant_session(self.ctx.tenant_id) as db:
            run = db.get(ProcurementRun, self.ctx.run_id)
            run.retries += 1
            run_event(db, self.ctx.tenant_id, self.ctx.run_id, "recovery", {"kind": kind, "retries": run.retries})


def _jsonable(v: Any) -> Any:
    return json.loads(json.dumps(v, default=str))


@dataclass
class RunContext:
    tenant_id: uuid.UUID
    run_id: uuid.UUID
    worker_id: str
    settings: Settings = field(default_factory=get_settings)
    model: ModelAdapter | None = None
    workflow: str = "bounded"
    _playwright: Any = None
    _browser: Any = None

    def __post_init__(self) -> None:
        self.sink = DbSink(self)
        with tenant_session(self.tenant_id) as db:
            run = db.get(ProcurementRun, self.run_id)
            self.workflow = run.workflow
            self.mode = run.mode
            self.fixture_options = dict(run.fixture_options or {})
        if self.model is None:
            self.model = build_model(self.mode, self.fixture_options)
        self.sku_map, self.canonical = load_master_data()

    @property
    def verify(self) -> bool:
        return self.workflow == "bounded"

    @property
    def decided_by(self) -> str:
        return "fixture_model" if self.model.simulated else "model"

    # ---------------------------------------------------------------- browser lifecycle
    def browser(self):
        if self._browser is None:
            from playwright.sync_api import sync_playwright

            from ..browser.tools import launch_browser

            self._playwright = sync_playwright().start()
            self._browser = launch_browser(self._playwright)
        return self._browser

    def close(self) -> None:
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    # ---------------------------------------------------------------- data access
    def request(self, db) -> ProcurementRequest:
        run = db.get(ProcurementRun, self.run_id)
        return db.get(ProcurementRequest, run.request_id)

    def policy(self, db) -> PolicyVersion:
        return db.get(PolicyVersion, db.get(ProcurementRun, self.run_id).policy_version_id)

    def supplier_handle(self, db, key: str) -> tuple[SupplierHandle, Supplier]:
        sup = db.scalar(select(Supplier).where(Supplier.key == key))
        meta = db.scalar(select(SupplierCredentialMetadata).where(SupplierCredentialMetadata.supplier_id == sup.id))
        handle = SupplierHandle(
            sup.id,
            sup.key,
            sup.name,
            sup.base_url,
            tuple(sup.allowed_origins),
            meta.credential_ref if meta else "",
            sup.is_simulated,
        )
        return handle, sup

    def event(self, type_: str, data: dict[str, Any]) -> None:
        with tenant_session(self.tenant_id) as db:
            run_event(db, self.tenant_id, self.run_id, type_, data)

    def set_run(self, **values: Any) -> None:
        with tenant_session(self.tenant_id) as db:
            run = db.get(ProcurementRun, self.run_id)
            for k, v in values.items():
                setattr(run, k, v)
            if "phase" in values:
                run_event(db, self.tenant_id, self.run_id, "phase", {"phase": values["phase"]})

    def charge(self, decision: Decision, what: str, summary: dict[str, Any]) -> None:
        """Account model usage, persist the decision as an addressable step, enforce the cost ceiling."""
        with tenant_session(self.tenant_id) as db:
            run = db.get(ProcurementRun, self.run_id)
            run.model_input_tokens += decision.usage.input_tokens
            run.model_output_tokens += decision.usage.output_tokens
            run.model_cost += decision.usage.cost()
            seq = (db.scalar(select(func.max(BrowserStep.seq)).where(BrowserStep.run_id == self.run_id)) or 0) + 1
            db.add(
                BrowserStep(
                    tenant_id=self.tenant_id,
                    run_id=self.run_id,
                    seq=seq,
                    supplier_key=summary.get("supplier"),
                    tool=f"decide:{what}",
                    side_effect=False,
                    input={},
                    status="ok",
                    observation={"decision": summary, "label": decision.label, "simulated": decision.simulated},
                    explanation=summary.get("reason") or summary.get("note"),
                    decided_by="fixture_model" if decision.simulated else "model",
                    duration_ms=0,
                )
            )
            run_event(
                db,
                self.tenant_id,
                self.run_id,
                "model_decision",
                {"what": what, "simulated": decision.simulated, "label": decision.label, **summary},
            )
            if run.model_cost > self.settings.max_run_cost:
                raise BudgetExhausted("model_cost", f"Model cost {run.model_cost:.4f} exceeded the run ceiling")


CONTEXTS: dict[str, RunContext] = {}
