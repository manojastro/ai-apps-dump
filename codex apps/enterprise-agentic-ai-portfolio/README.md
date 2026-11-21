# Enterprise Agentic AI Portfolio

Five independent, local-first agentic AI control-plane POCs. Each converts a domain event into deterministic detection, evidence collection, typed investigation, bounded action, explicit approval, execution, independent outcome validation, audit history, and measurable evaluation.

This repository is intentionally not a shared monolith. Every project owns its backend, persistence, frontend, dependencies, tests, Docker configuration, documentation, and demo workflow.

## Projects

| Project | Domain | Distinguishing proof | Tests | Port |
|---|---|---|---:|---:|
| [01 Agent Reliability](01-agent-reliability-platform/README.md) | AI evaluation and LLMOps | Read-only artifact provider, outcome mismatch detection, payload-bound policy change, executed candidate gate | 37 | 8101 |
| [02 Cloud FinOps](02-cloud-finops-agent/README.md) | FinOps and SRE | History-derived peak schedule, unsafe cheapest-plan rejection, observed savings and verified rollback | 29 | 8102 |
| [03 Data Pipeline Reliability](03-data-pipeline-reliability-agent/README.md) | Data quality and lineage | Silent failure behind operational SUCCESS, exact SQL shadow execution, fresh deployment revalidation | 23 | 8103 |
| [04 Kafka Streaming Reliability](04-kafka-streaming-reliability-agent/README.md) | Kafka and distributed systems | Seven labeled RCAs, exact action/parameter coupling, recollected state, retryable validation failures | 11 | 8104 |
| [05 DevSecOps Remediation](05-devsecops-remediation-agent/README.md) | AppSec and release engineering | Exact patch/source hash approval, separation of duties, AST side-effect rejection, rescan | 31 | 8105 |

The current implementation truth and diagnosed build failures are recorded in [PROJECT_STATUS.md](PROJECT_STATUS.md) and [BUILD_LOG.md](BUILD_LOG.md). The optional static [portfolio index](portfolio/index.html) provides a visual overview without creating runtime coupling.

## Run a project

Each project supports the same outer launch shape:

```bash
cd 01-agent-reliability-platform  # choose exactly one project
docker compose up --build
```

Open the project's port from the table. FastAPI OpenAPI docs are available at `/docs`; health, readiness, and Prometheus-text metrics are at `/health`, `/ready`, and `/metrics`. Each project README also documents a Python 3.11 path, credentials for its explicit demo/secure modes, failure injection, and a complete scripted demo.

Docker Compose configuration has been validated for all five projects. Image builds require Docker Desktop's Linux engine; that engine was unavailable during this build, so no image-build success is claimed.

## Engineering properties

- Credential-free deterministic/mock reasoning is the default and is visibly labeled.
- Integrations sit behind adapter/provider boundaries; POCs use synthetic state rather than paid infrastructure.
- SQLite provides project-local persistence and migration ledgers. Production PostgreSQL remains a documented substitution path.
- Typed Pydantic schemas constrain evidence, RCA, risk, actions, approvals, validation, and evaluation results.
- Destructive or state-changing actions are allow-listed, risk-scored, rollback-described, approval-gated, and simulator-scoped.
- Approval binds the reviewed artifact where execution correctness depends on code, SQL, Terraform, policy payloads, or source patches.
- Evaluation predictions are produced from evidence before comparison with separately stored labels.
- Adversarial tests cover forged evidence, stale state, artifact mutation, role bypass, wrong actions, failed rollback, operational drift, and misleading aggregate metrics.

## Portfolio index

```bash
python -m http.server 8000 --directory portfolio
```

Open <http://localhost:8000>. Dashboard links expect the individual project services on ports 8101–8105.

## Scope

These are serious local POCs, not production deployments. Their security documents call out the remaining gaps: synthetic infrastructure, single-node SQLite, demo/static credentials, process-local metrics, and the need for enterprise IAM, durable orchestration, OpenTelemetry backends, policy-as-code, and real adapter certification before production mutation.
