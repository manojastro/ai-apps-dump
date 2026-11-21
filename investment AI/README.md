# Aegis Plan India

**Research Indian investments. Understand the trade-offs. Leave with an actionable financial plan.**

India-focused educational investment research and financial-planning simulator.

This application is **not** a broker, not an order-execution platform, not an automated trading system, not a stock-tip bot, not a guaranteed-return engine, not a portfolio-management service, and **not a SEBI-registered investment adviser**.

No trade, SIP, redemption, transfer, payment, brokerage action or investment order is ever executed.

## Important disclaimer

Educational research and financial-planning simulation only. This application is not a SEBI-registered investment adviser. Nothing shown constitutes an instruction to buy, sell or hold a security. Market, tax and regulatory information can change. Verify important decisions using current official sources and, where appropriate, a SEBI-registered professional.

No investment transaction or payment was executed by Aegis Plan India.

## Architecture

See `docs/architecture.md` for Mermaid diagrams of the system and the LangGraph flow.

Frontend (Next.js) → FastAPI → IPS, holdings, regulatory snapshot, market data, deterministic engine, LangGraph research orchestrator, risk policy, stress, comparison, PDF, audit, jobs.

## Deterministic-vs-LLM boundary

Python owns arithmetic, allocation normalisation, eligibility, caps, tax thresholds after retrieval, loan mathematics, emergency-fund calculation, contributions, stress, vetoes, constraint enforcement, percentages, and source coverage.

The LLM owns summarization, explanation, research synthesis, trade-off narrative, and failure-mode discussion. It must never add percentages, invent rates, or override a veto.

## Agent graph

Profile Analyst → Holdings Analyst (after PII redaction) → Regulatory Research → Macro Research → Universe Research → Construction → Risk Officer (one tighter retry on veto) → Plan Critic → user compare/select → Financial Action Plan → PDF.

## Data provenance

Every numerical fact carries source URL, tier, as-of, fetched-at, confidence, and verification (`verified | stale | conflicting | unverified`). Conflicting sources are labelled, never silently picked. Mock mode is labelled `MOCK_DATA` / `DEGRADED_DATA`.

## Firecrawl

Adapter: `app/data/firecrawl_client.py` (v2 scrape, scrape JSON, search, extract, agent). Hostname allowlist in `app/data/allowlist.py`. Cache key = normalised URL + schema hash + parser version. Default TTL 6 hours. HTTP 429 uses exponential backoff (three attempts). Call budget `FIRECRAWL_MAX_CALLS_PER_PLAN`. Mock mode never calls the network.

## Mock mode

```env
DATA_MODE=mock
```

The full product flow works without Firecrawl or LLM credentials.

```env
DATA_MODE=live
```

enables Firecrawl + OpenAI-compatible LLM (defaults target SpaceXAI / xAI: `https://api.x.ai/v1`, `grok-4.5`).

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -e ".[dev]"
copy .env.example .env
mkdir data
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000

## Docker setup

```bash
docker compose up --build
```

API: http://localhost:8000/health  
Web: http://localhost:3000

## Environment variables

See `.env.example`.

| Variable | Purpose |
|---|---|
| `DATA_MODE` | `mock` or `live` |
| `DATABASE_URL` | SQLite default; PostgreSQL-ready |
| `LLM_API_KEY` / `XAI_API_KEY` | OpenAI-compatible key |
| `LLM_BASE_URL` | Default `https://api.x.ai/v1` |
| `LLM_MODEL` | Default `grok-4.5` |
| `FIRECRAWL_API_KEY` | Live research only |
| `FIRECRAWL_MAX_CALLS_PER_PLAN` | Default 8 |
| `CACHE_TTL_SECONDS` | Default 21600 |
| `CORS_ORIGINS` | Comma-separated |

## Database migration commands

```bash
alembic upgrade head
```

Local demo also calls `create_all` on startup so SQLite works without a manual migration.

## Tests

```bash
pytest
cd apps/web && npm test
```

## Evals

`evals/households.json` contains twelve fixtures (first-job, tech salaried with home loan, dual-income, 55-year-old, thin-reserve crypto request, chit fund, old/new tax regime, forbidden international/crypto, Firecrawl down, conflicting sources, PII paste).

```bash
python scripts/run_evals.py
```

## Regulatory snapshot

`app/regulatory/` assembles tax, NPS, LRS and market-data restriction fields, each with source metadata. Live retrieval must come from allowlisted official domains. Values are never treated as permanent law.

## Security model

- Environment secrets only
- CORS, request size limits, secure headers
- Hostname allowlist + SSRF blocks
- Deterministic PII redaction before any LLM
- Scraped HTML treated as untrusted; injection phrases detected
- No Aadhaar/PAN collection

## Known limitations

- Mock mode uses labelled fixture snapshots, not live RBI/ITD page extraction.
- Live Firecrawl/LLM paths require credentials and still refuse to invent missing thresholds.
- PDF is ReportLab (print-friendly grayscale), not WeasyPrint.
- Jobs run in-process (no Redis) — suitable for local/demo, not multi-replica production.
- Image OCR for holdings is behind a non-implemented feature flag; paste/CSV is the MVP.
- Age-eligible products (SCSS, SSY) are flagged for dynamic evaluation; live eligibility still needs the current official page.

## Eight-minute demo script

1. `docker compose up --build` (or local uvicorn + next dev).
2. Open http://localhost:3000 and read the mandate.
3. Click **Load demo household #2** (Meera, 33, Bengaluru, ₹1.2L take-home, ₹35k home-loan EMI, EPF + two SIPs).
4. Watch the war room eight-agent cards move queued → running → complete.
5. Open Compare: Protect | Balance | Grow. Grow is labelled more aggressive, not better.
6. Inspect Risk Officer flags (reserve, constraints, source coverage).
7. Select Balance (or Protect).
8. Open the Financial Action Plan; confirm disclaimer, `plan_id`, IST timestamp, `snapshot_id`, `rules_version`.
9. Open Sources; confirm official domains and as-of/fetched metadata.
10. Download the PDF. Confirm disclaimer and “No investment transaction or payment was executed by Aegis Plan India.”

## Production hardening checklist

- [ ] PostgreSQL instead of SQLite
- [ ] Shared job queue if running multiple API replicas
- [ ] Live Firecrawl allowlist scrape for tax/NPS/LRS before any tax-sensitive PDF
- [ ] Secret manager; never bake keys into images
- [ ] Rate limits and auth beyond the local household abstraction
- [ ] Object storage for PDFs
- [ ] Log redaction review
- [ ] Disable mock fixtures in production
