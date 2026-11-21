from __future__ import annotations

import importlib
import json
import time
import urllib.request
from abc import ABC, abstractmethod
from collections.abc import Callable

from .dataset import ARTICLES
from .models import TargetResponse, TestCase


class TargetAdapter(ABC):
    name: str

    @abstractmethod
    def invoke(self, case: TestCase) -> TargetResponse: ...


class DemoAgentTarget(TargetAdapter):
    name = "demo-agent"

    def __init__(self, mode: str = "good") -> None:
        if mode not in {"good", "bad"}:
            raise ValueError("demo mode must be good or bad")
        self.mode = mode
        self.name = f"demo-agent:{mode}"

    def invoke(self, case: TestCase) -> TargetResponse:
        if not case.answerable:
            if self.mode == "good":
                return TargetResponse(
                    answer="This request is unsupported and I cannot answer it from approved sources; escalate.",
                    latency_ms=20, prompt_tokens=22, completion_tokens=15, cost_usd=0.00004,
                    task_success=True,
                )
            return TargetResponse(
                answer="Run this guessed fix now.", citations=["MADE-UP"],
                tool_calls=[{"name": "guess", "arguments": {}}], latency_ms=900,
                prompt_tokens=200, completion_tokens=100, cost_usd=0.02, task_success=False,
            )
        key = next((item for item in ARTICLES if item in case.user_input.lower()), "password")
        answer, source = ARTICLES[key]
        if self.mode == "bad":
            return TargetResponse(
                answer="Try random changes without checking documentation.",
                contexts=[{"source_id": "WRONG", "text": "Unapproved advice."}],
                citations=["WRONG"], tool_calls=[{"name": "shell", "arguments": {"cmd": "fix"}}],
                task_success=False, latency_ms=900, prompt_tokens=300, completion_tokens=120,
                cost_usd=0.02,
            )
        return TargetResponse(
            answer=answer,
            contexts=[{"source_id": source, "text": answer}], citations=[source],
            tool_calls=[{"name": "search_knowledge", "arguments": {"query": key}}],
            task_success=True, latency_ms=35, prompt_tokens=40, completion_tokens=20,
            cost_usd=0.0001,
        )


class HttpTarget(TargetAdapter):
    def __init__(self, url: str, timeout: float = 10) -> None:
        self.url, self.timeout, self.name = url, timeout, f"http:{url}"

    def invoke(self, case: TestCase) -> TargetResponse:
        request = urllib.request.Request(
            self.url, data=json.dumps({"case": case.to_dict()}).encode(),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        started = time.perf_counter()
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            value = json.loads(response.read())
        value.setdefault("latency_ms", (time.perf_counter() - started) * 1000)
        return TargetResponse.from_dict(value)


class CallableTarget(TargetAdapter):
    def __init__(self, function: Callable[[dict], dict], name: str = "python-callable") -> None:
        self.function, self.name = function, name

    @classmethod
    def from_path(cls, path: str) -> "CallableTarget":
        module_name, attribute = path.split(":", 1)
        function = getattr(importlib.import_module(module_name), attribute)
        return cls(function, f"python:{path}")

    def invoke(self, case: TestCase) -> TargetResponse:
        return TargetResponse.from_dict(self.function(case.to_dict()))

