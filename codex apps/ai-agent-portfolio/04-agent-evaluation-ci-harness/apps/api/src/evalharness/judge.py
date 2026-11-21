from __future__ import annotations

from abc import ABC, abstractmethod

from .metrics import f1, tokens
from .models import TargetResponse, TestCase


class Judge(ABC):
    provider: str
    model: str
    version: str

    @abstractmethod
    def score(self, case: TestCase, response: TargetResponse) -> dict[str, float]: ...

    def config(self) -> dict[str, str]:
        return {"provider": self.provider, "model": self.model, "version": self.version}


class MockJudge(Judge):
    """Pinned, deterministic CI judge; it never calls a paid model."""

    provider = "mock"
    model = "mock-judge-v1"
    version = "1.0.0"

    def score(self, case: TestCase, response: TargetResponse) -> dict[str, float]:
        score = f1(tokens(response.answer), tokens(case.expected_answer)) if case.answerable else 1.0
        return {"judge_correctness": round(score, 6)}


def make_judge(provider: str = "mock", model: str = "mock-judge-v1") -> Judge:
    if provider != "mock" or model != "mock-judge-v1":
        raise ValueError("only the explicitly pinned mock-judge-v1 is configured by default")
    return MockJudge()

