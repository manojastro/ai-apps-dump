"""LLM adapter: deterministic mock narration by default, optional OpenAI-compatible live mode.

The LLM never controls control flow; it only renders human-readable narration of
already-computed validation results.
"""
from __future__ import annotations

import os
from typing import Any

import httpx

from app.services.metrics import METRICS


class LlmSettings:
    def __init__(self) -> None:
        self.mode = os.environ.get("LLM_MODE", "mock").strip().lower()
        self.api_key = os.environ.get("LLM_API_KEY", "")
        self.base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    @property
    def live(self) -> bool:
        return self.mode == "live" and bool(self.api_key)


class LlmAdapter:
    def __init__(self, settings: LlmSettings | None = None) -> None:
        self.settings = settings or LlmSettings()

    def narrate_validation(self, report: dict[str, Any]) -> str:
        if self.settings.live:
            try:
                return self._live_narrate(report)
            except Exception:
                METRICS.incr("llm_calls_total", {"mode": "live", "error": "true"})
        return self._mock_narrate(report)

    def _prompt(self, report: dict[str, Any]) -> str:
        regressions = report.get("regressions") or []
        lines = [
            f"Change {report.get('change_id')} validated with verdict "
            f"{report.get('verdict')} and risk {report.get('risk', {}).get('band')}.",
            f"{len(regressions)} regressions detected.",
        ]
        for r in regressions[:6]:
            lines.append(f"- [{r.get('severity')}] {r.get('kind')}: {r.get('message')}")
        intents = report.get("intents") or []
        failed = [i for i in intents if not i.get("passed")]
        if failed:
            lines.append(f"Failing intent policies: {', '.join(i['name'] for i in failed)}.")
        fix = report.get("proposed_fix_diff")
        if fix:
            lines.append("A safer configuration has been proposed and re-validated.")
        return "\n".join(lines)

    def _mock_narrate(self, report: dict[str, Any]) -> str:
        METRICS.incr("llm_calls_total", {"mode": "mock"})
        risk = (report.get("risk") or {}).get("band", "UNKNOWN")
        verdict = report.get("verdict", "UNKNOWN")
        n_reg = len(report.get("regressions") or [])
        top = report.get("rca") or {}
        parts = [
            f"[mock-llm] Validation verdict {verdict}; composite risk band {risk}.",
            f"{n_reg} regression(s) detected against the digital twin.",
        ]
        root_cause = top.get("root_cause")
        if root_cause:
            parts.append(f"Most probable root cause: {root_cause}")
        if report.get("fix_validated"):
            parts.append("Proposed remediation re-simulated clean; safe to approve the fixed config.")
        elif n_reg:
            parts.append("Do not apply this change without remediation or explicit sign-off.")
        else:
            parts.append("No impact detected on reachability, routing, security or services.")
        return " ".join(parts)

    def _live_narrate(self, report: dict[str, Any]) -> str:
        METRICS.incr("llm_calls_total", {"mode": "live"})
        prompt = (
            "Summarize this network change validation for an operations engineer in "
            "under 120 words. Facts only:\n" + self._prompt(report)
        )
        response = httpx.post(
            f"{self.settings.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.settings.api_key}"},
            json={
                "model": self.settings.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
            timeout=20.0,
        )
        response.raise_for_status()
        data = response.json()
        return str(data["choices"][0]["message"]["content"]).strip()


LLM = LlmAdapter()
