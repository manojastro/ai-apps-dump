"""Token bucket: pure math, stub atomicity, concurrency, API 429."""

from __future__ import annotations

import threading

from fastapi.testclient import TestClient

from gateway.rate_limit import InMemoryRedisStub, RedisTokenBucketStore, TokenBucket

from .conftest import auth_headers, make_tenant


def test_bucket_allows_up_to_capacity() -> None:
    b = TokenBucket(capacity=3, refill_rate=60.0)
    assert b.allow(now=1000.0)[0]
    assert b.allow(now=1000.0)[0]
    assert b.allow(now=1000.0)[0]
    ok, retry = b.allow(now=1000.0)
    assert not ok and retry > 0


def test_bucket_refills_over_time() -> None:
    b = TokenBucket(capacity=2, refill_rate=1.0)
    b.allow(now=1000.0)
    b.allow(now=1000.0)
    assert not b.allow(now=1000.0)[0]
    assert b.allow(now=1002.5)[0]  # 2.5s * 1/s refills the bucket


def test_retry_after_scales_with_deficit() -> None:
    b = TokenBucket(capacity=1, refill_rate=1.0)
    b.allow(now=500.0)
    ok, retry = b.allow(cost=1.0, now=500.0)
    assert not ok and retry == 1.0


def test_stub_wrapper_is_atomic_under_concurrency() -> None:
    store = RedisTokenBucketStore(InMemoryRedisStub())
    results: list[bool] = []
    lock = threading.Lock()

    def worker() -> None:
        ok, _ = store.allow("k", capacity=10, refill_rate=0.0, cost=1.0,
                            now=2000.0)
        with lock:
            results.append(ok)

    threads = [threading.Thread(target=worker) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sum(results) == 10  # exactly capacity passes, rest denied


def test_api_returns_429_with_retry_after(client: TestClient) -> None:
    raw, _ = make_tenant(client, name="ratelimited", rpm=2)
    for _ in range(2):
        r = client.post("/v1/chat/completions",
                        json={"model": "triage-cheap",
                              "messages": [{"role": "user", "content": "hi"}]},
                        headers=auth_headers(raw))
        assert r.status_code == 200
    r = client.post("/v1/chat/completions",
                    json={"model": "triage-cheap",
                          "messages": [{"role": "user", "content": "hi again"}]},
                    headers=auth_headers(raw))
    assert r.status_code == 429
    assert "Retry-After" in r.headers
