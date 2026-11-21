"""ServiceNow client contract shared by the simulator and the real Table API adapter."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

CHANGE_STATES = {
    "-5": "New",
    "-4": "Assess",
    "-3": "Authorize",
    "-2": "Scheduled",
    "-1": "Implement",
    "0": "Review",
    "3": "Closed",
    "4": "Canceled",
}
CHANGE_STATE_FLOW = ["-5", "-4", "-3", "-2", "-1", "0", "3"]
TASK_STATES = {"1": "Open", "2": "Work in Progress", "3": "Closed Complete", "4": "Closed Incomplete", "7": "Closed Skipped"}


class ServiceNowError(Exception):
    """Base error. ``outcome_unknown`` means the write may have been applied remotely."""

    retryable = True
    outcome_unknown = False

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class ServiceNowAuthError(ServiceNowError):
    retryable = False


class ServiceNowPermissionError(ServiceNowError):
    retryable = False


class ServiceNowTimeout(ServiceNowError):
    outcome_unknown = True


class ServiceNowServerError(ServiceNowError):
    pass


class ServiceNowSchemaError(ServiceNowError):
    retryable = False


class ServiceNowClient(ABC):
    mode: str
    instance_label: str

    @abstractmethod
    def query(self, table: str, query: str = "", fields: list[str] | None = None, limit: int = 100) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get(self, table: str, sys_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def create(self, table: str, fields: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def update(self, table: str, sys_id: str, fields: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def table_fields(self, table: str) -> set[str] | None:
        """Field names that exist on the table (None when the schema cannot be read)."""

    @abstractmethod
    def test_connection(self) -> dict[str, Any]: ...

    def record_url(self, table: str, sys_id: str) -> str | None:
        """Deep link for a *real* record; the simulator returns None (no fabricated links)."""
        return None
