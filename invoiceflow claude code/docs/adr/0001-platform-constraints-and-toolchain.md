# ADR 0001: Platform constraints and toolchain

- **Status:** Accepted
- **Date:** 2026-10-25
- **Deciders:** Manoj (approved the Phase 0 plan and its three defaults on 2026-10-25), Claude Code

## Context

InvoiceFlow must run the same agent code on two backends: a local one (Windows 11 + Docker Desktop) and Databricks **Free Edition**. Rule 11 requires every platform or API decision to cite current official docs with a date. Databricks, MLflow and LangGraph change often, so this ADR records what was verified in Phase 0 and the toolchain built on it.

## Verified platform facts

All pages were read on **2026-10-25**. "Updated" is the date printed on the page.

### Databricks Free Edition

Source: [Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations), updated 2026-10-18.

| Area | Limit in Free Edition |
|---|---|
| Compute | Serverless only; custom compute is not supported. Outbound internet is restricted to a limited set of trusted domains. |
| SQL warehouses | One, limited to 2X-Small. |
| Jobs | Max 5 concurrent job tasks per account. |
| Lakeflow pipelines | One active pipeline per pipeline type. |
| Model serving | A limit on active endpoints; no GPU serving endpoints; no provisioned throughput; no custom models on GPU or batch inference; "certain models not available". |
| AI Search | One endpoint, one search unit. Direct Vector Access is not supported. |
| Apps | Up to 3 per account. An app stops automatically 24 hours after it is started, updated or redeployed. |
| Lakebase | One project per account, with scale-to-zero compute. |
| Not supported | R and Scala, custom workspace storage locations, online tables, clean rooms, legacy features, Knowledge Assistant. |
| Admin | One workspace and one metastore; no account console or account-level APIs; sign-in by email OTP, Google or Microsoft; no SSO or SCIM; non-commercial use only. |
| Quota | Exceeding the fair-usage quota shuts compute down for the rest of the day (in extreme cases, the month). Data and settings are kept. |
| LinkedIn verification | Raises some limits and gives limited access to AI Runtime. |

### Model serving catalog

Source: [Supported foundation models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models), updated 2026-10-23.

- Pay-per-token chat models from OpenAI, Google, Anthropic, Meta, Alibaba (Qwen), xAI, Zhipu, Moonshot, DeepSeek and others are listed. Embedding models listed include GTE Large (En), BGE Large (En) and Qwen3-Embedding-0.6B.
- Models can be called by model service name (`system.ai.<model>`) through Unity Gateway, or by pay-per-token endpoint name.
- **The page does not say which models Free Edition exposes.** The endpoint names used by this project must come from `databricks serving-endpoints list` in our workspace. No endpoint name is guessed or hardcoded.

### Endpoints in our workspace

Source: `databricks serving-endpoints list --profile invoiceflow -o json`, run 2026-10-25 with Databricks CLI v1.22.1. Evidence: [serving-endpoints-2026-10-25.log](../evidence/phase-0/serving-endpoints-2026-10-25.log) (the workspace host is omitted).

All 12 endpoints are READY, and all are open-weight models.

| Task | Endpoint | Model |
|---|---|---|
| chat | `databricks-deepseek-v4-flash-0731` | DeepSeek V4 Flash (0731) |
| chat | `databricks-gemma-3-12b` | Gemma 3 12B |
| chat | `databricks-gpt-oss-120b` | GPT OSS 120B |
| chat | `databricks-gpt-oss-20b` | GPT OSS 20B |
| chat | `databricks-llama-4-maverick` | Llama 4 Maverick |
| chat | `databricks-meta-llama-3-1-8b-instruct` | Meta Llama 3.1 8B Instruct |
| chat | `databricks-meta-llama-3-3-70b-instruct` | Meta Llama 3.3 70B Instruct |
| chat | `databricks-qwen3-next-80b-a3b-instruct` | Qwen3 Next 80B A3B Instruct |
| chat | `databricks-qwen35-122b-a10b` | Qwen3.5 122B A10B |
| embeddings | `databricks-bge-large-en` | BGE Large (En) |
| embeddings | `databricks-gte-large-en` | GTE Large (En) |
| embeddings | `databricks-qwen3-embedding-0-6b` | Qwen3 Embedding 0.6B |

None of the catalog's OpenAI GPT-5.x/6, Google Gemini, Anthropic Claude, xAI, Zhipu or Moonshot models are present. The endpoints were **listed, not queried**. Tool calling, structured output and rate limits are still unverified for each endpoint.

### AI Search (formerly Vector Search)

Source: [Query an AI Search index](https://docs.databricks.com/aws/en/ai-search/query-ai-search), updated 2026-10-22.

- Query types: ANN (default), hybrid keyword + similarity (`query_type="hybrid"`), and full-text (`query_type="FULL_TEXT"`, Beta).
- Filters work on any indexed column. A reranker is available.
- The Python SDK is `databricks-ai-search` (`from databricks.ai_search.client import AISearchClient`).

### Agent authoring and deployment

Sources: [Deploy agents on Databricks](https://docs.databricks.com/aws/en/agents/deploy/) (updated 2026-10-13), [Agent Runtime](https://docs.databricks.com/aws/en/agents/deploy/agent-runtime) (updated 2026-10-06), [Run agents on Apps using the legacy agent server](https://docs.databricks.com/aws/en/agents/custom-agents/author-agent) (updated 2026-10-07), [Agent Bricks CLI](https://docs.databricks.com/aws/en/agents/custom-agents/agent-bricks-cli) (updated 2026-10-13), [MLflow ResponsesAgent](https://mlflow.org/docs/latest/genai/serving/responses-agent/).

- A deployed agent has three layers: a **framework** (LangGraph is supported), an **agent server**, and an **agent runtime**.
- The recommended server is `DurableAgentServer`, run on **Agent Runtime** (Databricks Apps) through the **Agent Bricks CLI** (`databricks-agentbricks`). That CLI is in **Beta**.
- `ResponsesAgent` + MLflow `AgentServer` on Databricks Apps is now labeled **legacy**. That server lacks persistent run state, crash recovery and idempotent invocations. Agents on that legacy path support only medium and large app compute sizes.
- Model Serving as an agent runtime is also legacy.
- `ResponsesAgent` is still part of MLflow (3.17.2 on PyPI on 2026-10-25).

### Serverless Python version

Source: [Serverless environment versions](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/), updated 2026-10-18.

| Environment version | Python | Databricks Connect |
|---|---|---|
| 6 (Sep 3, 2026) | 3.12.3 | 19 |
| 5 (Feb 25, 2026) | 3.12.3 | 18 |
| 4 (Aug 13, 2025) | 3.12.3 | 17.3.2 |
| 3 (Jun 13, 2025) | 3.12.3 | 16.4.2 |
| 2 (Nov 21, 2024) | 3.11.10 | 15.4.5 |

`databricks-connect` 19.3.0 on PyPI declares `requires_python ==3.12.*`.

### LangGraph human-in-the-loop

Source: [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) (LangGraph 1.2.17 on PyPI on 2026-10-25).

- Pause with `interrupt(payload)`; resume with `Command(resume=value)` and the same `thread_id`. This needs a checkpointer.
- On resume, **the node restarts from the beginning**, so code before `interrupt()` runs again. Side effects before an interrupt must be idempotent or moved to a separate node. Do not wrap `interrupt()` in `try/except`.

## Corrections to the spec

| Spec says | Current docs say |
|---|---|
| One Databricks App | Up to 3 Apps, each auto-stopping after 24 hours |
| Agent Bricks is not in Free Edition | Only Knowledge Assistant is listed as unsupported. The Agent Bricks CLI is Beta. Availability on Free Edition is untested. |
| Vector Search | Renamed AI Search; the SDK is `databricks-ai-search` |
| Agent wrapped in MLflow `ResponsesAgent` | Still supported, but serving it through MLflow AgentServer is now the legacy path |

## Decisions

1. **Python 3.12.** `requires-python = ">=3.12,<3.13"` and `.python-version`. This matches serverless environments 3–6 and `databricks-connect` 19.
2. **Toolchain:**
   - uv 0.11, with the `uv_build` backend and a lockfile
   - ruff 0.17 for lint and format
   - mypy 2.4 in strict mode over `src` and `tests`
   - pytest 9 + pytest-cov
   - pre-commit 4.7 running gitleaks 8.30.1, a `.env` guard and standard hygiene hooks
   - one Python CLI (`uv run invoiceflow …`) instead of separate `.ps1` and `.sh` scripts
3. **Layout:** interfaces in `src/invoiceflow/ports/`, implementations in `src/invoiceflow/adapters/{local,databricks}/`. Details go in ADR 0002.
4. **Local backend:** Postgres 17 + pgvector in Docker for data, retrieval, checkpoints, audit and outbox. Manoj chose this default on 2026-10-25; ADR 0003 records the detailed comparison in Phase 1.
5. **"Runs on Databricks" in Phase 4** means the LangGraph graph runs in a serverless notebook or job against the Databricks backend, behind a thin `ResponsesAgent` wrapper for MLflow evaluation. Serving it as a live endpoint is optional and will be decided in ADR 0007. Manoj chose this default on 2026-10-25.
6. **Model endpoint names come only from config.** They are set from the workspace's own endpoint list, never guessed.
7. **Workflow:** one branch per phase (`phase/<N>-<name>`), merged into `main` only after Manoj approves the phase.

## Consequences

- The Free Edition quota can lock compute for a day, so live Databricks evaluations run in small batches.
- Without Direct Vector Access, retrieval uses a **Delta Sync** index. The workspace has three embedding endpoints, so the index can let Databricks compute embeddings; a self-managed embedding column remains the fallback. ADR 0005 picks the embedding model by measured recall@k.
- The workspace offers only open-weight chat models. The agent's default model will be picked from the nine chat endpoints by a measured comparison on the dev set (Phase 4), not by reputation. Proprietary models are reachable only through the optional Azure OpenAI provider, which costs money and needs Manoj's approval.
- Outbound internet is restricted, so a Databricks run cannot call a sandbox ERP on a laptop. The ERP port needs an adapter that works inside Databricks (ADR 0009).
- Lakebase is a free hosted Postgres option for the LangGraph checkpointer. It avoids paid Azure Postgres but must be verified (ADR 0008).
- Because the Agent Bricks CLI is Beta and untested on Free Edition, no phase depends on it.
- Strict mypy may need per-module overrides for third-party libraries without type hints. Each override goes in `pyproject.toml` with a comment explaining why.

## Alternatives considered

- **Python 3.13** (the local default): rejected because Databricks serverless and `databricks-connect` run 3.12.
- **pip-tools or Poetry**: rejected because uv also manages the Python version, is faster, and is what the Databricks agent templates use.
- **detect-secrets** as the scanner: rejected because its last release was 1.5.0 in May 2024, while gitleaks is actively maintained and runs the same way in CI.
- **Paired `.ps1` and `.sh` scripts**: rejected because two copies of each script drift apart; a single Python CLI behaves the same on both platforms.

## Open items

| Item | How it gets verified | When |
|---|---|---|
| ~~Which LLM and embedding endpoints the workspace has~~ | **Done 2026-10-25:** 12 READY endpoints (9 chat, 3 embeddings); see "Endpoints in our workspace" | Phase 0 |
| Which chat endpoints support tool calling and JSON-schema structured output, and their Free Edition rate limits | One small test query per candidate endpoint | Phase 3 (embeddings), Phase 4 (chat) |
| Whether Unity Catalog Python functions run on Free Edition serverless | Phase 2 setup notebook | Phase 2 |
| Whether PyPI is among the trusted outbound domains | `%pip install` in a serverless notebook | Phase 2 |
| Whether Lakebase works with `langgraph-checkpoint-postgres` | Integration test | Phase 4 |
| Which app compute sizes Free Edition allows | Workspace UI | Phase 4, only if ADR 0007 needs an app |
| Whether the Agent Bricks CLI works on Free Edition | `agentbricks init` / `agentbricks dev` | Phase 4, only if ADR 0007 needs it |
