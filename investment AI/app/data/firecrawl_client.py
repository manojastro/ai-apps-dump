from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import get_settings
from app.data.allowlist import assert_no_ssrf, is_allowlisted
from app.data.cache import CACHE
from app.logging import get_logger
from app.security.sanitize import detect_prompt_injection

log = get_logger(component="firecrawl")


class FirecrawlBudget:
    def __init__(self, max_calls: int) -> None:
        self.max_calls = max_calls
        self.calls = 0

    def charge(self) -> None:
        if self.calls >= self.max_calls:
            raise RuntimeError("FIRECRAWL_BUDGET_EXCEEDED")
        self.calls += 1


class FirecrawlClient:
    """Version-aware Firecrawl v2 adapter. Mock mode never calls the network."""

    def __init__(self, budget: FirecrawlBudget | None = None) -> None:
        self.settings = get_settings()
        self.budget = budget or FirecrawlBudget(self.settings.firecrawl_max_calls_per_plan)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.firecrawl_api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self.settings.data_mode == "mock" or not self.settings.firecrawl_api_key:
            raise RuntimeError("FIRECRAWL_DISABLED_IN_MOCK")
        url = self.settings.firecrawl_base_url.rstrip("/") + path
        delay = 0.5
        last_error: Exception | None = None
        for attempt in range(3):
            self.budget.charge()
            try:
                with httpx.Client(timeout=30.0) as client:
                    res = client.post(url, headers=self._headers(), json=payload)
                if res.status_code == 429:
                    log.warning("firecrawl_429", attempt=attempt)
                    time.sleep(delay)
                    delay *= 2
                    last_error = RuntimeError("HTTP 429")
                    continue
                res.raise_for_status()
                return res.json()
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(delay)
                delay *= 2
        raise RuntimeError(f"firecrawl failed: {last_error}")

    def scrape(self, target_url: str, *, formats: list[str] | None = None) -> dict[str, Any]:
        if not is_allowlisted(target_url):
            raise ValueError("url not on allowlist")
        assert_no_ssrf(target_url)
        key = CACHE.make_key(target_url, {"formats": formats or ["markdown"]})
        cached = CACHE.get(key)
        if cached:
            cached = {**cached, "cache_hit": True}
            return cached
        data = self._request("/v2/scrape", {"url": target_url, "formats": formats or ["markdown"]})
        markdown = ""
        body = data.get("data") or data
        if isinstance(body, dict):
            markdown = str(body.get("markdown") or "")
        injection = detect_prompt_injection(markdown)
        result = {"ok": True, "data": data, "injection_attempt": injection, "cache_hit": False, "url": target_url}
        CACHE.set(key, result)
        return result

    def scrape_json(self, target_url: str, schema: dict[str, Any], prompt: str | None = None) -> dict[str, Any]:
        if not is_allowlisted(target_url):
            raise ValueError("url not on allowlist")
        assert_no_ssrf(target_url)
        key = CACHE.make_key(target_url, schema)
        cached = CACHE.get(key)
        if cached:
            return {**cached, "cache_hit": True}
        fmt: dict[str, Any] = {"type": "json", "schema": schema}
        if prompt:
            fmt["prompt"] = prompt
        data = self._request("/v2/scrape", {"url": target_url, "formats": [fmt]})
        result = {"ok": True, "data": data, "cache_hit": False, "url": target_url}
        CACHE.set(key, result)
        return result

    def search(self, query: str, *, domains: list[str] | None = None, limit: int = 5) -> dict[str, Any]:
        payload: dict[str, Any] = {"query": query, "limit": limit}
        if domains:
            payload["sources"] = [{"type": "web"}]
        return self._request("/v2/search", payload)

    def extract_multi_page(self, urls: list[str], schema: dict[str, Any], prompt: str) -> dict[str, Any]:
        for u in urls:
            if not is_allowlisted(u):
                raise ValueError(f"url not on allowlist: {u}")
            assert_no_ssrf(u)
        return self._request("/v2/extract", {"urls": urls, "schema": schema, "prompt": prompt})

    def agent_research(self, prompt: str) -> dict[str, Any]:
        """Expensive path — only if scrape/search cannot do the job."""
        return self._request("/v2/agent", {"prompt": prompt})
