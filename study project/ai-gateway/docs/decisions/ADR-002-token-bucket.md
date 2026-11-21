# ADR-002 — Token bucket for rate limiting

Date: 2026-09-18. Status: accepted.
Context: need smooth rpm/tpm limits per tenant under concurrency.
Decision: token bucket (capacity + refill_rate), check-and-take done
atomically (single lock in the stub; Lua script / transaction in real Redis).
Why not fixed window: fixed windows allow 2x bursts at boundaries and need
the same atomicity anyway.
Consequences: one small math unit (`TokenBucket`) plus one atomic wrapper;
concurrency test proves exactly-capacity passes.
