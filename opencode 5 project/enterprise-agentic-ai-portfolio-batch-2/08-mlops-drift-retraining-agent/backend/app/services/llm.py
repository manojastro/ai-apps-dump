"""LLM narration adapter with deterministic mock mode and OpenAI-compatible live mode."""
from __future__ import annotations

import threading

import httpx

from backend.app.config import settings

_TEMPLATES: dict[str, str] = {
    "window_summary": (
        "Window {window_id} ({name}): alert={alert}; {drift_count} features drifted "
        "beyond meaningful thresholds (max PSI {max_psi:.3f}); champion F1 on the "
        "window is {f1:.3f}."
    ),
    "decision_retrain": (
        "Retraining justified for window {window_id}: meaningful drift observed, "
        "performance degraded by {f1_drop:.3f} F1 and projected benefit "
        "{benefit:.2f} exceeds the minimum. Candidate must pass all deployment gates."
    ),
    "decision_monitor": (
        "Continued monitoring recommended for window {window_id}. Gate blocked by: "
        "{blockers}. No retraining will be triggered."
    ),
    "root_cause": (
        "Incident {incident_id}: {root_cause} Confidence {confidence:.0%}. Top drifted "
        "features: {top_features}."
    ),
    "promotion": (
        "Candidate {candidate_version} promoted to champion replacing "
        "{previous_champion} after approval by {approver}."
    ),
    "rejection": (
        "Candidate {version} rejected: {reasons}. Bad-model prevention prevented a "
        "degraded model from reaching production."
    ),
}


class LLMService:
    """Narration-only LLM access; mock mode is fully deterministic."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def narrate(self, key: str, context: dict[str, object]) -> str:
        template = _TEMPLATES.get(key, "")
        if not template:
            return ""
        if settings.llm_mode == "live" and settings.llm_api_key:
            prompt = f"Rewrite professionally in one sentence: {template.format(**{k: v for k, v in context.items()})}"
            live = self._complete(prompt)
            if live:
                return live
        return self._safe_format(template, context)

    def _safe_format(self, template: str, context: dict[str, object]) -> str:
        class _SafeDict(dict):
            def __missing__(self, key: str) -> str:
                return ""

        try:
            return template.format_map(_SafeDict(**context))
        except (ValueError, KeyError):
            return template.split(":")[0]

    def _complete(self, prompt: str) -> str | None:
        with self._lock:
            try:
                response = httpx.post(
                    f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                    json={
                        "model": settings.llm_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2,
                        "max_tokens": 160,
                    },
                    timeout=8.0,
                )
                response.raise_for_status()
                payload = response.json()
                return payload["choices"][0]["message"]["content"].strip()
            except Exception:
                return None


_service: LLMService | None = None


def get_llm() -> LLMService:
    """Return the process-wide LLM service singleton."""
    global _service
    if _service is None:
        _service = LLMService()
    return _service
