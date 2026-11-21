# Interview notes

Everything here points at code and numbers in this repository. Numbers are quoted from the
generated reports; re-check them there before an interview, because they change when the
code or data changes.

## The 2-minute walkthrough

> AP teams spend hours on invoices that fail the three-way match against the purchase order
> and goods receipt, and that's also where invoice fraud hides. I built InvoiceFlow, an
> agent that resolves those exceptions on Databricks.
>
> The key design choice is that the LLM never decides anything that matters. Deterministic
> code does the matching, GST checks and duplicate detection. The LLM investigates with
> read-only tools, reads the policy and the vendor's contract, and proposes a resolution as
> structured JSON. Validators check that it didn't downgrade the exception and only cited
> sections it actually retrieved. A policy engine, in Python and in OPA with a 6,496-case
> parity test, decides whether it can run or needs a human. Approvals pause the LangGraph
> workflow durably, and only an executor with idempotency keys writes to a simulated ERP.
> Everything goes into a hash-chained audit log.
>
> It's measured honestly: a rule-only baseline, an agent eval with a deterministic stub, a
> live-model run on the hard cases, and a CI gate that fails on any policy violation. The
> data is all synthetic, and the reports say where the numbers are optimistic.

## The 10-minute walkthrough

1. **The problem (1 min).** Three-way match, the eight exception types, why bank-change
   requests in invoice notes are dangerous. Show `docs/CONTROL_MATRIX.md`.
2. **Data (1 min).** A seeded generator. Labels come from scenario *intent*, never from the
   matcher, because otherwise the baseline would be circular. There are 25 adversarial
   invoices (prompt injection, a hidden bank change, conflicting signals). Show
   `data/generator/build.py`, the `MAIN` and `ADVERSARIAL` lists.
3. **The deterministic core (1.5 min).** Decimal money, inclusive boundaries tested on both
   sides, a GSTIN Luhn mod-36 check worked by hand in a test, and 8 mutation checks that
   prove the tests catch bugs. Show `core/matcher.py` and its docstring ("free text is never
   read").
4. **Policy (1.5 min).** Ten rules, each with an allow and a deny test, enforced by a
   meta-test. Three outcomes, and why DENY differs from REQUIRE_APPROVAL. Segregation of
   duties; the agent can never approve. OPA parity. Show `policy/evaluator.py` and
   `policy/rego/invoiceflow.rego`.
5. **The agent (2.5 min).** Walk `agent/graph.py`:
   - the bounded tool loop;
   - "escalate never downgrade";
   - citations must have been retrieved;
   - the interrupt node holds only `interrupt()`, because nodes re-run on resume;
   - idempotent side effects;
   - resume proven across two processes.

   Demo `agent run INV-00042`, then `agent approve`, then `audit verify`.
6. **Evaluation (1.5 min).** Baseline vs agent; per-kind adversarial results; the CI gate;
   what the stub can and can't tell you; the live-model subset run. Show
   `docs/EVAL_REPORT.md` and `docs/EVAL_REPORT_LIVE.md`.
7. **Honesty and limits (1 min).** What is not run (the Databricks data layer, AI Search,
   Entra ID, deployment), and why the scores are optimistic. Show `docs/LIMITATIONS.md` and
   `docs/CASE_STUDY.md`.

## Ten likely questions

**1. Why not let the LLM classify the exception?**
Because the matching rules are exact and auditable, and an LLM adds risk without adding
accuracy. The LLM may only *escalate* to a bank-change review, backed by a text signal
(`agent/proposal.py`). Prompt injection can't downgrade a case.

**2. How do you stop prompt injection?**
In layers:
- The core never reads free text.
- The model sees vendor text labelled `untrusted_vendor_text`.
- The model only has read-only tools.
- Validators reject downgrades and ignored signals.
- Policy decides, and only the executor writes, after `require_allow`.

`test_a_model_that_tries_to_approve_is_stopped` uses a deliberately malicious fake model.

**3. What happens when a human approves something they shouldn't?**
The policy engine runs again with the approval. Self-approval, approval by an agent or an
auditor, and approval below the required authority are all refused, and the case keeps
waiting. A bank change also needs a call-back by someone other than the preparer.

**4. How do you avoid paying twice?**
The idempotency key is `case:action:policy-version`. A duplicate delivery returns the
original decision, and an HTTP retry after a lost response still writes one row
(`test_http_retry_after_lost_response_does_not_double_post`). The decision and its outbox
event commit in one transaction.

**5. What if the process crashes while waiting for approval?**
The state lives in the checkpointer. A test runs the agent in one process, exits, and
approves in a new process, which resumes and executes. Audit appends are idempotent per
event key, so a node that re-runs after a crash doesn't duplicate entries.

**6. How do you know your tests are any good?**
Mutation checks: 8 deliberate bugs (inclusive boundaries, segregation of duties, the GSTIN
modulo, who may approve, and others), all caught. The policy meta-test guarantees an allow
and a deny test per rule.

**7. Your baseline scores 99%. Isn't that suspicious?**
Yes, and the report says so: labels and matcher share the same written rules on clean
synthetic data. The interesting part is where it fails and why. It misses hidden bank
changes, because it reads no text, and authorised price escalations, because it reads no
contracts. Those are exactly the cases the LLM has to win.

**What happened on the real workspace?**
- Parity between Unity Catalog and local data held on every record.
- AI Search recall@5 was 1.000, with 0 scope violations.
- The full dev split ran with Unity Catalog data, AI Search and `databricks-gpt-oss-120b`:
  196/196 on exception, action and approver, with 0 unsafe outcomes, 0 executed violations,
  a 15 s median and 3.1 M input tokens.

Two caveats to say out loud:
- The exception is mostly deterministic.
- The data is synthetic, and this was one run.

**What did the live model add?** On the 22 hardest dev invoices, `databricks-gpt-oss-120b`
routed all 4 contract-authorised price increases to the buyer, while the stub and the
baseline asked for credit notes. That required reading the contract's escalation clause.
It also made 0 unsafe proposals on 16 adversarial invoices. Be precise about attribution:
hidden bank changes are also caught by the deterministic regex screen, so that win is not
the model's alone (PROGRESS.md, `docs/EVAL_REPORT_LIVE.md`).

**8. How do you measure the agent without paying for a big model?**
A deterministic stub for CI (it tests the harness, not intelligence), record/replay for
repeatability, and live runs on Databricks Free Edition's open-weight endpoints for the
cases that need language understanding.

**9. Why Databricks, and what didn't work on Free Edition?**
Unity Catalog governs tables, volumes and the tool functions; AI Search does hybrid
retrieval; model serving and MLflow cover the rest. Free Edition allows one AI Search
endpoint, Delta Sync only, open-weight models only, and quota lockouts. The
`ResponsesAgent` serving path is now legacy, so the agent runs as a job and serving is
deferred (ADRs 0001 and 0007).

**10. What would you do next?**
- Run the Databricks setup and parity checks, and the AI Search index, on the workspace.
- Pick the embedding model by recall.
- Run the full live eval and record it for CI replay.
- Anchor the audit head hash in write-once storage.
- Deploy (Phase 7) with Entra ID.
