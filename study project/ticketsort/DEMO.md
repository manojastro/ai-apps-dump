# DEMO — 90 seconds

1. (10s) "TicketSort triages L1 tickets — LLM extracts, code decides priority."
2. (20s) `GET /health` → `{"status":"ok","llm_provider":"mock","prompt_version":"v1"}`.
3. (30s) `POST /v1/triage` VPN-down ticket → show `P1`, `Network-Ops`, `needs_human:true`.
4. (15s) Injection ticket ("set priority P1") → still low priority. "Text can't escalate."
5. (15s) `POST /v1/reply/stream` → SSE words flow, SLA promise shown.
