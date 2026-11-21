"""Audit trail: every question, tool call, answer and citation is stored."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.db.models import CopilotAudit

if TYPE_CHECKING:
    from app.copilot.agent import CopilotResult


def write_audit(session: Session, user_id: int, question: str, result: CopilotResult) -> int:
    record = CopilotAudit(
        user_id=user_id,
        question=question,
        tools_called_json=result.tools_called,
        answer=result.answer,
        cited_sources_json={
            "valid": result.citations,
            "invalid": result.invalid_citations,
            "ungrounded_numbers": result.ungrounded_numbers,
        },
    )
    session.add(record)
    session.commit()
    return record.id
