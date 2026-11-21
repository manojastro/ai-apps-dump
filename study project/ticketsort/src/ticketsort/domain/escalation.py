"""Escalation rules — when a ticket needs a human look."""

from ticketsort.config import Settings
from ticketsort.domain.models import Category, Extraction, Service


def should_escalate_to_human(extraction: Extraction, settings: Settings) -> bool:
    """True if confidence low, service unknown, security, or possible P1.

    Like a major-incident rule: a possible P1 always gets a human look.
    """
    if extraction.confidence < settings.confidence_threshold:
        return True
    if extraction.affected_service == Service.UNKNOWN:
        return True
    if extraction.category == Category.SECURITY:
        return True
    return extraction.impact == 1 and extraction.urgency == 1
