# Architecture

```mermaid
flowchart LR
  subgraph Browser
    UI["Next.js UI<br/>10 review screens"]
  end
  subgraph Web["web/ (Next.js server)"]
    BFF["BFF route handlers<br/>httpOnly session cookie<br/>correlation id"]
  end
  subgraph Engine["engine/ (Python, FastAPI)"]
    API["REST API<br/>server-side authz<br/>Decimal-as-string JSON"]
    COORD["Coordinator<br/>allowed transitions"]
    WORKER["Durable worker<br/>leased tasks, SKIP LOCKED"]
    TOOLS["Deterministic tools<br/>PDF text · local OCR · XLSX<br/>parse · scale · normalize"]
    RULES["Rules engine R01–R10<br/>metrics · rounding tolerance"]
    AGENTS["Agents A–E<br/>demo adapters | live client"]
    EXPORT["Snapshot → XLSX + PDF"]
  end
  subgraph Eve["agent-runtime/ (eve, live mode only)"]
    E1[document-understanding]
    E2[table-extraction]
    E3[financial-mapping]
    E4[reconciliation]
    E5[analyst-pack]
  end
  DB[(PostgreSQL<br/>NUMERIC money)]
  FS[(File storage<br/>local | GCS)]
  GW[[Vercel AI Gateway]]

  UI --> BFF --> API
  API --> COORD --> WORKER
  WORKER --> AGENTS
  AGENTS --> TOOLS
  AGENTS --> RULES
  AGENTS -- "live: /eve/v1 + outputSchema" --> Eve
  Eve -- "typed tools + signed scope" --> API
  Eve --> GW
  API --> EXPORT
  API & WORKER & EXPORT --> DB
  API & TOOLS & EXPORT --> FS
```

## Responsibilities

| Component | AI? | Responsibility |
|---|---|---|
| Integrity checks | code | type/magic bytes, size, page count, encryption, zip-bomb ratio, macro-enabled formats rejected |
| Extraction tools | code | pdfplumber words+coordinates, RapidOCR (local ONNX) for scanned pages, openpyxl cached values (no macros/formulas executed), layout → rows/cells with bbox or cell ref |
| A. Document Understanding | demo: code · live: eve | entity, statements, periods, currency, scale, scope, notes, scanned pages, unsupported entities; questions instead of guesses; live answers accepted only with verifiable evidence quotes |
| B. Table Extraction | demo: code · live: eve flags | persists immutable rows/cells; targeted re-OCR of low-confidence pages (bounded); live model may *flag* layout issues, never add a cell |
| C. Financial Mapping | demo: scorer · live: eve | label + section + total flag + unit + note scoring; live model picks only from offered candidates |
| Normalization | code | exact Decimal scale factors, recorded sign flips, EPS/percent/shares never scaled, single-scope single-currency spreads |
| D. Reconciliation | code rules + demo heuristics · live: eve causes | runs rules (tool), explains mismatches (transposed digits, omitted component, OCR), requests targeted re-extraction; never edits a figure |
| E. Analyst Pack | demo: template · live: eve | narrative claims each referencing stored records; a verifier rejects claims with unsupported numbers or forbidden judgements |
| Coordinator / worker | code | stage transitions, gates, retries, budgets, idempotency, recovery |
| Review service | code | corrections, mapping changes, unit/period confirmation, adjustments, exception acceptance, four-eyes approval, invalidation |
| Exports | code | immutable snapshot → workbook + PDF, formula-injection sanitising, Excel precision handling |

## Key design choices (and why)

* **The coordinator is ordinary code, not an LLM.** Allowed transitions are a fixed table (`NEXT` in
  `workflow/coordinator.py`). A model can never skip a gate, approve, or write data.
* **Agents exchange typed artifacts.** Each agent writes a pydantic-validated artifact (`agents/contracts.py`)
  into the `artifacts` table; the next stage reads that artifact. `agent_executions` records the agent, mode,
  tools (with digests and timings), input and output artifact IDs, tokens and cost.
* **Demo vs live is decided per run and recorded.** `workflow_runs.agent_mode` is fixed at start. A live failure
  raises `LiveAgentError`, the task fails visibly (and is retryable) — there is no silent demo fallback.
* **eve hosts the live agents** (one workspace, five members) with `defaultTools: false`, so models reading
  untrusted documents get no shell, file, web or sub-agent tools — only their read-only typed tools. Tools call
  back with a service token and an HMAC-signed scope; the engine derives the workspace from the signature.
* **Durability lives in PostgreSQL** (a task table with leases) rather than an extra queue service: it is enough
  for a solo developer and the same database already holds the state. eve's own workflow durability covers the
  agent sessions in live mode.
* **Money is `NUMERIC(28,6)` + Python `Decimal`, and strings in JSON.** The API response class never lets FastAPI
  turn a Decimal into a float; the UI formats decimal strings with string arithmetic.
* **Immutable raw extraction.** `extracted_cells` is never updated. Corrections write `analyst_adjustments` and
  `observations.current_value`; the original `parsed_value`/`normalized_value` stay.
* **Spread = review unit** (entity + scope + currency). A `spread_version` (the statement-set version) is
  created whenever figures, mappings or units change; calculation results and approvals are tied to a version.

## Request path and correlation

Browser → `/api/engine/*` (Next.js adds bearer from cookie + `x-correlation-id`) → engine middleware sets a
context-var correlation ID, opens an OpenTelemetry span, logs JSON → workflow runs store the correlation ID →
worker logs and agent HTTP calls (`x-correlation-id` header to eve) carry it.
