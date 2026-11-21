"""Token-bucket rate limiting.

Pure-Python bucket + thread-safe in-memory Redis stub with an atomic wrapper.

Production note: docker-compose wires a REAL Redis service and REDIS_URL.
The stub below mirrors the atomic semantics (one lock around check-and-take,
like a Lua script / transaction in real Redis) so concurrency behaviour matches.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class TokenBucket:
    """Pure-python token bucket used by tests and as the math reference."""

    capacity: float
    refill_rate: float  # tokens per second
    tokens: float = field(init=False)
    last: float = field(init=False)

    def __post_init__(self) -> None:
        self.tokens = float(self.capacity)
        self.last = time.monotonic()

    def allow(self, cost: float = 1.0, now: float | None = None) -> tuple[bool, float]:
        """Try to take `cost` tokens. Returns (allowed, retry_after_seconds)."""
        t = time.monotonic() if now is None else now
        elapsed = max(0.0, t - self.last)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last = t
        if self.tokens >= cost:
            self.tokens -= cost
            return True, 0.0
        deficit = cost - self.tokens
        retry_after = deficit / self.refill_rate if self.refill_rate > 0 else 60.0
        return False, retry_after


class InMemoryRedisStub:
    """Minimal in-memory Redis stand-in (dict + single global lock).

    The lock makes check-and-decrement atomic across threads, the same reason
    real Redis uses a Lua script / MULTI transaction for rate limiting.
    """

    def __init__(self) -> None:
        self._data: dict[str, tuple[float, float]] = {}  # key -> (tokens, last)
        self._lock = threading.Lock()


class RedisTokenBucketStore:
    """Atomic token-bucket wrapper on top of the stub (or real Redis later)."""

    def __init__(self, client: InMemoryRedisStub) -> None:
        self._client = client

    def allow(
        self,
        key: str,
        *,
        capacity: float,
        refill_rate: float,
        cost: float = 1.0,
        now: float | None = None,
    ) -> tuple[bool, float]:
        t = time.monotonic() if now is None else now
        with self._client._lock:  # atomic section (cf. Lua script in real Redis)
            tokens, last = self._client._data.get(key, (capacity, t))
            tokens = min(capacity, tokens + max(0.0, t - last) * refill_rate)
            if tokens >= cost:
                self._client._data[key] = (tokens - cost, t)
                return True, 0.0
            deficit = cost - tokens
            retry_after = deficit / refill_rate if refill_rate > 0 else 60.0
            self._client._data[key] = (tokens, t)
            return False, retry_after
