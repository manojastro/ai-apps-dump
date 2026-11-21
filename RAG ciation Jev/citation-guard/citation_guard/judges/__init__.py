from .base import LABELS, BudgetExceeded, CallBudget, Judge, JudgeResult
from .mock import MockJudge

JUDGE_NAMES = ("jev", "llm", "mock", "stringmatch")


def make_judge(name: str, cfg):
    """Return a judge instance, or None for the string-match-only baseline (Check A alone)."""
    if name == "mock":
        return MockJudge()
    if name == "jev":
        from .jev import JevJudge

        return JevJudge(cfg)
    if name == "llm":
        from .llm import LLMJudge

        return LLMJudge(cfg)
    if name == "stringmatch":
        return None
    raise ValueError(f"unknown judge {name!r}; choose from {JUDGE_NAMES}")


__all__ = ["LABELS", "BudgetExceeded", "CallBudget", "Judge", "JudgeResult", "MockJudge", "make_judge", "JUDGE_NAMES"]
