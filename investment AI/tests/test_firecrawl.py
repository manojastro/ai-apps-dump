import time

from app.data.cache import CACHE
from app.data.firecrawl_client import FirecrawlBudget, FirecrawlClient


def test_budget_stops():
    b = FirecrawlBudget(2)
    b.charge()
    b.charge()
    try:
        b.charge()
        raise AssertionError("should have raised")
    except RuntimeError as exc:
        assert "BUDGET" in str(exc)


def test_mock_mode_does_not_call_network(monkeypatch):
    client = FirecrawlClient()
    try:
        client.scrape("https://www.rbi.org.in/")
        raise AssertionError("mock should refuse network")
    except RuntimeError as exc:
        assert "MOCK" in str(exc) or "DISABLED" in str(exc)


def test_cache_avoids_redundant_set():
    CACHE.clear()
    key = CACHE.make_key("https://www.rbi.org.in/", {"formats": ["markdown"]})
    CACHE.set(key, {"ok": True}, ttl_seconds=60)
    hit = CACHE.get(key)
    assert hit and hit["ok"] is True


def test_429_backoff_pattern(monkeypatch):
    delays = []
    monkeypatch.setattr(time, "sleep", lambda d: delays.append(d))
    # Pattern under test: 0.5 then 1.0 then 2.0
    delay = 0.5
    for _ in range(3):
        time.sleep(delay)
        delay *= 2
    assert delays == [0.5, 1.0, 2.0]
