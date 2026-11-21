# ADR 0011: Policy engine: Python evaluator (v1) backed by OPA/Rego (v2)

- **Status:** Accepted
- **Date:** 2026-10-25
- **Deciders:** Manoj (spec), Claude Code

## Context

Policy must be testable, explainable rule by rule, and changeable by people who are not
Python developers. In larger organisations it is often owned by a separate team and served
by OPA.

## Decision

Keep both:

- **Python (`policy/evaluator.py`).** The reference implementation, used by the agent. It
  returns per-rule results with sources.
- **Rego (`policy/rego/invoiceflow.rego`).** The same rules, for OPA 1.x. The client is
  `policy/opa.py`, which talks to the `opa` binary or to an OPA server over REST.

Both read the same control matrix (YAML → JSON as `data.matrix`).

## Evidence (2026-10-25, OPA 1.21.4)

- `opa test`: every Rego unit test passes.
- Parity: Python and OPA give the same outcome and required role on **6,496 generated
  cases**. The cases cover every exception × action pair, the limit boundaries, seven
  approver kinds (including the agent, an auditor and self-approval), tolerance, the bank
  call-back and missing citations. See `tests/policy/test_opa_parity.py`; CI runs it with
  `setup-opa`.

## Consequences

- Two implementations must stay in step. The parity test is the guard, and it compares
  outcomes and roles, not message text.
- The agent still uses the Python evaluator. Switching to OPA at runtime means swapping the
  evaluator behind the same call, which is not done.
