from __future__ import annotations

from app.adapters.base import SystemAdapter
from app.core.models import CustomerRecord, System
from app.core.normalize import normalize_email, normalize_name, normalize_plan, normalize_status


class CRMAdapter(SystemAdapter):
    system = System.CRM
    filename = "crm.db"

    def read_all(self) -> list[CustomerRecord]:
        rows = self._query("SELECT id, name, email, status, plan, owner FROM accounts ORDER BY id")
        return [
            CustomerRecord(
                system=System.CRM,
                record_id=r["id"],
                crm_account_id=r["id"],
                name=normalize_name(r["name"]),
                raw_name=r["name"],
                email=normalize_email(r["email"]),
                raw_email=r["email"],
                status=normalize_status(r["status"]),
                plan=normalize_plan(r["plan"]),
                attrs={"owner": r["owner"]},
            )
            for r in rows
        ]
