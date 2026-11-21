"""Domain errors mapped to HTTP status codes."""
from __future__ import annotations


class DomainError(Exception):
    """Business-rule violation with a desired HTTP status."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
