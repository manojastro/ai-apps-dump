# Integration status

| Integration | Implementation | Validation scope |
|---|---|---|
| Replay metrics, traces, logs, deployments | Versioned fixtures and normalized evidence | API, unit, browser and benchmark tests |
| FastAPI / SQLAlchemy / SQLite | Real local persisted state | Exercised locally |
| LangGraph / SQLite checkpoints | Real graph and checkpoints | Replay workflows and resume checks |
| Local demo services | Real checkout, payment and inventory HTTP services | Measured fault traffic; see evidence JSON |
| OpenTelemetry propagation | FastAPI and HTTPX instrumentation | Nonzero trace/span IDs observed in demo logs |
| Prometheus | Fixed query templates, bounded HTTP adapter, scraper config | Container integration not verified |
| Jaeger / Collector | Bounded read adapter and OTLP export config | Collector and trace-search integration not verified |
| PostgreSQL checkpoints and ORM | Prepared Compose profile | Docker engine unavailable at initial inspection; see BUILD_STATUS for latest outcome |
| Redis / RQ | Dispatch plus database reconciliation | Prepared, not deployment-validated |
| OpenAI-compatible model | Destination validation, capability test, dynamic tools, usage | No provider key supplied; real requests unverified |
| Anthropic-specific adapter | Not implemented | OpenAI-compatible transport only |
| GitHub adapter | Not implemented | Optional integration deferred |

Provider credentials are environment-only. Never use a NEXT_PUBLIC variable for a secret. `MODEL_ALLOWED_HOSTS` is an administrator allowlist, and `MODEL_DEV_HOSTS` permits explicit development-only local endpoints. Link-local metadata destinations remain blocked. Redirects are disabled. Network-level egress controls are still advised before deploying this on an untrusted network.

Connector response limit: 32 KiB. Default HTTP timeout: 8 seconds, at most two retries. Source errors are normalized. Sources are not silently replaced with fixtures. Live telemetry URLs are fixed server configuration; tools cannot supply URL or PromQL strings.

The Jaeger adapter uses the deployed query service's HTTP `/api/traces` interface, which must be compatibility-tested against the chosen image. Replay health is never reported as a successful live connectivity test.
