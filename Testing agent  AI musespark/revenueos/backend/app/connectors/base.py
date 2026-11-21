"""Connector interface.

Why: the rest of the app only knows canonical table shapes. A Salesforce, HubSpot,
Stripe or ServiceNow connector can be added later by implementing `fetch`, without
touching the loader, ML code or API.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

# Parents come first, so foreign keys resolve in order during a load.
LOAD_ORDER = [
    "teams", "users", "accounts", "contacts", "deals", "deal_stage_history", "activities",
    "subscriptions", "invoices", "payments", "usage_daily", "tickets",
]


class Connector(ABC):
    """Reads one source system and returns rows in canonical table shape."""

    name: str

    @abstractmethod
    def fetch(self, table: str) -> pd.DataFrame:
        """Return every source row for a canonical table."""

    def fetch_all(self) -> dict[str, pd.DataFrame]:
        return {table: self.fetch(table) for table in LOAD_ORDER}
