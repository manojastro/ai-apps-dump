# Architecture

InvoiceFlow resolves Accounts Payable exceptions: invoices that fail the three-way match
(invoice vs purchase order vs goods receipt). The design rule throughout:

> **AI proposes → policy authorizes → a human approves when required → only the executor
> writes → the harness records everything.**

All data is synthetic, and the ERP is a SIMULATED sandbox.

## Components

```mermaid
flowchart LR
  subgraph Data["Data (ports/data.py)"]
    mem[MemoryReader] --- pg[PostgresReader] --- dbx[DatabricksReader<br/>Unity Catalog]
  end
  subgraph Retrieval["Retrieval (ports/retrieval.py)"]
    local[Local BM25 + hashing embedder + RRF] --- ais[AI Search hybrid index]
  end
  subgraph LLM["LLM (ports/llm.py)"]
    stub[Stub] --- replay[Record / replay] --- oai[OpenAI-compatible:<br/>Databricks serving, Azure OpenAI]
  end
  core[core: matcher, tolerance,<br/>GSTIN, GST, duplicates]
  policy[policy: control matrix +<br/>Python evaluator / OPA Rego]
  graph[agent: LangGraph state machine]
  tools[tools/readonly.py<br/>read-only, masked]
  exec[tools/executor.py<br/>require_allow, idempotent]
  erp[(SIMULATED ERP<br/>idempotency + outbox)]
  audit[(audit hash chain +<br/>evidence packs)]
  approvals[approval service<br/>dev tokens / Entra OIDC]
  graph --> core & policy & tools & exec & audit
  tools --> Data & Retrieval
  graph --> LLM
  exec --> erp
  approvals -- resume --> graph
```

| Package | Responsibility |
|---|---|
| `core/` | Pure deterministic checks. No I/O, no free text |
| `policy/` | Control matrix (YAML), Python evaluator, OPA client, Rego policy in `policy/rego` |
| `ports/` | Interfaces: data, retrieval, LLM, ERP |
| `adapters/` | Local (memory, Postgres), Databricks (UC SQL, AI Search), LLM, ERP |
| `retrieval/` | Section chunking, access scopes, local hybrid retriever |
| `agent/` | Graph, prompts, proposal validation, text screen, runner, case store, ResponsesAgent |
| `tools/` | Read-only tools (for the LLM), executor (write), email drafts (never sent) |
| `audit/` | Hash chain, verifier, evidence packs |
| `services/` | SIMULATED ERP API, approval service + inbox |
| `evals/` | Baseline, agent eval, retrieval eval, reports, CI gate |

## One case, step by step

1. **intake.** Checks the kill switch (re-read on every case; flipping it needs no redeploy)
   and loads the invoice through the data port.
2. **deterministic_match.** Runs the three-way match plus duplicate, PO, GST and bank checks
   and records every finding. The *primary* exception follows a fixed severity order.
3. **screen_text.** Applies deterministic regexes to vendor text. These can only make the
   system more cautious (a remittance-change request forces a bank-change escalation).
4. **Routing.** A clean invoice with no vendor text takes a deterministic fast path.
   Everything else goes to **investigate**: a bounded tool loop where the model calls
   read-only tools (max tool steps, tokens, wall clock and retries per tool).
5. **retrieve.** Pulls policy and contract sections in the agent's scope (the invoice's own
   vendor).
6. **propose.** The model returns JSON matching `ResolutionProposal`.
7. **validate.** The proposal must parse. Its exception must equal the matcher's, except
   for an evidenced escalation to bank change. The screen's signals must be honoured,
   citations must have been retrieved in this case, and the action must be allowed.
   Failing proposals get one retry with feedback, then go to the manual queue.
8. **policy_authorize.** ALLOW (holds), REQUIRE_APPROVAL or DENY.
9. **await_approval.** A LangGraph `interrupt`. It persists to the checkpointer and survives
   process restarts.
10. **apply_approval.** Re-evaluates policy with the approval and any bank call-back. An
    invalid approver (self, agent, auditor) is refused and the case keeps waiting.
11. **execute.** `require_allow` runs first, then the ERP is called with an idempotency key.
12. **record.** Writes the evidence pack, the audit entries and, where relevant, an email
    **draft** (never sent).

Any failure goes to **fail_safe**: the manual queue with a reason (KILL_SWITCH, NOT_FOUND,
BUDGET_EXCEEDED, LLM_ERROR, VALIDATION_FAILED, POLICY_DENY, REJECTED_BY_APPROVER,
ERP_ERROR, and so on).

## Why AI or deterministic code at each step

| Step | Who | Why |
|---|---|---|
| Three-way match, tolerance, duplicates, GSTIN, tax type | Deterministic | Exact, testable, auditable; an LLM adds risk and nothing else |
| Primary exception | Deterministic (LLM may only escalate) | Prevents downgrades driven by prompt injection |
| Reading vendor text for warning signs | Regex screen **and** the LLM | The screen is a reliable floor; the LLM catches phrasing the regex misses |
| Reading contracts (e.g. an escalation clause) | LLM, with retrieval | Clauses are prose; this is where an LLM is worth having |
| Choosing among allowed actions, writing the rationale | LLM | Judgment and explanation, inside policy limits |
| Authorization, approval level, segregation of duties | Deterministic policy (Python and Rego) | Must never depend on model output |
| Writing to the ERP | Deterministic executor | Only after ALLOW, idempotently |

## Trust boundaries

| Boundary | Control |
|---|---|
| Vendor text → model | Labelled `untrusted_vendor_text`; the system prompt says it is data; validators reject downgrades and ignored signals |
| Model → system | Read-only tools only; structured output validated; policy decides; the executor is unreachable from the model |
| Approver → system | Identity from token only (dev tokens or Entra ID JWT); role checked server-side and again by policy |
| Process → storage | Bank numbers masked in tools, traces, audit and evidence; ground truth in a separate schema |
| System → ERP | Idempotency keys; conflict on key reuse; outbox in the same transaction |

## Backends

| Concern | Local | Databricks |
|---|---|---|
| Data | in-memory or Docker Postgres | Unity Catalog Delta tables (from a volume via `read_files`) |
| Governed tools | Python read-only tools (masked) | UC SQL functions (masked) |
| Retrieval | BM25 + hashing embedder + RRF | AI Search Delta Sync index, hybrid |
| LLM | stub, replay | serving endpoints (open-weight models in Free Edition) |
| Checkpoints, audit, cases, ERP | SQLite under `.invoiceflow/` | same code; hosted choice in ADR 0008 |
| Tracing | off, or MLflow if `MLFLOW_TRACING=true` | MLflow |

See [PROGRESS.md](../PROGRESS.md) for what has actually run on each backend.
