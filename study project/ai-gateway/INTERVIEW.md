# Interview Q&A (learner writes answers; agent reviews)

1. Why put a gateway in front of LLMs? What does it cost in latency?
2. How do you isolate tenants (keys, cache, budgets, data)?
3. Explain the token bucket. Why Redis? Why atomic?
4. What guardrails did you build? What's your false-positive rate?
5. Walk me through the OWASP LLM Top 10 items you tested.
6. How much KV-cache memory does an 8k context need? Show the math.
7. Draw your cloud architecture. How are secrets handled? Cost per month?
8. What happens when the primary model fails?
9. Estimate-before vs settle-after metering — why both?
10. Why does streaming make token counting harder?
11. Token bucket vs fixed window?
12. Why do guardrails create false positives?
13. How do you revoke a tenant without downtime?
14. What is cached, and why never across tenants?
15. What would you do next (real Redis, Postgres, LiteLLM)?

(Answers: learner-written. Numbers must come from `reports/`.)
