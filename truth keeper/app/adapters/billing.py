from __future__ import annotations

from datetime import date

from app.adapters.base import SystemAdapter
from app.core.models import CustomerRecord, System
from app.core.normalize import normalize_email, normalize_name, normalize_plan, normalize_status


class BillingAdapter(SystemAdapter):
    """One CustomerRecord per billing customer, joined with its subscription."""

    system = System.BILLING
    filename = "billing.db"

    def read_all(self) -> list[CustomerRecord]:
        rows = self._query(
            "SELECT c.customer_id, c.crm_account_id, c.name, c.email, c.merged_into,"
            " s.subscription_id, s.plan, s.status, s.monthly_amount, s.currency, s.next_charge_date,"
            " s.past_due_since"
            " FROM customers c LEFT JOIN subscriptions s ON s.customer_id = c.customer_id"
            " ORDER BY c.customer_id"
        )
        return [
            CustomerRecord(
                system=System.BILLING,
                record_id=r["customer_id"],
                crm_account_id=(r["crm_account_id"] or None),
                name=normalize_name(r["name"]),
                raw_name=r["name"],
                email=normalize_email(r["email"]),
                raw_email=r["email"],
                status=normalize_status(r["status"]),
                plan=normalize_plan(r["plan"]),
                attrs={
                    "subscription_id": r["subscription_id"],
                    "raw_plan": r["plan"],
                    "monthly_amount": r["monthly_amount"],
                    "currency": (r["currency"] or "USD").upper(),
                    "next_charge_date": r["next_charge_date"],
                    "past_due_since": r["past_due_since"],
                    "merged_into": r["merged_into"],
                },
            )
            for r in rows
        ]

    def read_as_of(self) -> date:
        rows = self._query("SELECT value FROM meta WHERE key = 'as_of'")
        return date.fromisoformat(rows[0]["value"]) if rows else date.today()

    def read_open_flag_conflict_ids(self) -> set[str]:
        rows = self._query("SELECT conflict_id FROM review_flags WHERE status = 'open'")
        return {r["conflict_id"] for r in rows}
