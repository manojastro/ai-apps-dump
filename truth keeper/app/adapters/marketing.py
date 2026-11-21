from __future__ import annotations

from app.adapters.base import SystemAdapter
from app.core.models import CustomerRecord, System
from app.core.normalize import normalize_email, normalize_name, normalize_status


class MarketingAdapter(SystemAdapter):
    system = System.MARKETING
    filename = "marketing.db"

    def read_all(self) -> list[CustomerRecord]:
        rows = self._query(
            "SELECT contact_id, email, name, lifecycle_stage, subscribed, last_campaign FROM contacts"
            " ORDER BY contact_id"
        )
        return [
            CustomerRecord(
                system=System.MARKETING,
                record_id=r["contact_id"],
                name=normalize_name(r["name"]),
                raw_name=r["name"],
                email=normalize_email(r["email"]),
                raw_email=r["email"],
                status=normalize_status(r["lifecycle_stage"]),
                attrs={
                    "lifecycle_stage": normalize_status(r["lifecycle_stage"]),
                    "subscribed": bool(r["subscribed"]),
                    "last_campaign": r["last_campaign"],
                },
            )
            for r in rows
        ]
