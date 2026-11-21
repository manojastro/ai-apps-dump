# INTERVIEW — TicketSort (draft answers, learner to review)

1. Why does code compute priority? So injected text can't escalate; deterministic ITIL matrix is auditable.
2. What does structured output guarantee? JSON matches schema; still can have wrong values, needs validation + repair.
3. Retry strategy? Tenacity 3 tries, exponential backoff + jitter — avoids hammering provider like retry storms on vendors.
4. How measured? 150 dev / 50 test frozen split; accuracy per field + confusion matrix; test never used for tuning.
5. p95 vs p50? p95 shows worst-case SLA breach; mock is 0ms, real LLM varies by tokens + throttling.
6. Cost per triage? Mock $0; real = in/1K*price + out/1K*price; halve by smaller model + shorter prompts + cache.
7. Injection defence? Treat text as data, code decides priority, Extraction has no priority field.
8. When human? conf<threshold, unknown service, security, or 1x1 possible P1.
9-15. (SSE, semaphore, Docker non-root, CI mock, SLA table, routing fallback, next steps) — see README + code.
