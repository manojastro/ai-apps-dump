"""Incident Commander target adapter (P4 placeholder).

P4 will implement search()/ask() against the Incident Commander endpoint
so AgentJudge can evaluate it with zero runner changes.
"""

from agentjudge.schemas import TargetAnswer


class IncidentCommanderTarget:
    """LEARNER TASK (P4): implement search() + ask() for Incident Commander."""

    name = "incident_commander"

    def search(self, query: str, top_k: int = 5) -> list[str]:
        raise NotImplementedError("LEARNER TASK (P4) — see LEARNING_LOG.md")

    def ask(self, question: str, top_k: int = 5) -> TargetAnswer:
        raise NotImplementedError("LEARNER TASK (P4) — see LEARNING_LOG.md")
