# Security model

## Implemented controls

- The API never accepts source code, patches, scanner rules, filesystem paths, or
  commands from users.
- Demonstration sources are nonfunctional, inert fixtures. Review copies use `.txt`
  extensions and the service never imports them.
- The exact patch executor recognizes only three authored scenarios and verifies the
  reviewed input, action ID, displayed patch hash, and exact fixed-source hash.
- A second hash check verifies the isolated workspace was unchanged after review.
- Approval requires a verified `approver` credential; remediation requires a distinct
  verified `executor` credential and identity. The same principal cannot perform both.
- Approval attestations are immutable database rows bound to the exact persisted patch
  preview bytes, action ID, and fixed-source bytes. Legacy approvals without this proof
  are `REAPPROVAL_REQUIRED` and remain non-executable until a new review.
- Validation uses deterministic rescanning and `ast.parse`; it does not call `eval`,
  `exec`, `compile`, imports, test runners, package managers, subprocesses, or shells.
- Regression policy compares the complete canonical scenario AST: exact module layout,
  public signature and body, imports, call count and arguments, constants, and return
  semantics. Extra `cursor.execute`/`subprocess.run` calls, aliases, environment
  exfiltration, top-level statements, and docstring/string spoofing fail closed.
- Any failed check or validator exception restores the before-source using an atomic
  workspace replacement, clears persisted after-state, and atomically records the
  failed validation, evaluation attempt, rollback evidence, and audit decision.
- Incident IDs are generated server-side. Resolved workspace targets must remain below
  the configured root.
- Structured audit payloads store hashes and decisions, not API keys or source text.
  SQLite triggers reject audit updates and deletes.
- Credential-derived role authentication, origin allow-listing, input validation, frame
  denial, no-sniff, referrer policy, and CSP are implemented.
- The Docker image runs as non-root UID `10001`.

## Credential fixture

The `demo_prod_token_123456789` string is deliberately nonfunctional and exists only to
exercise a scanner pattern. It must never be replaced with a real credential.

## Risk and approval

Every proposal includes risk, blast radius, reversibility, expected benefit,
confidence, required approval, and rollback plan. Rejection is terminal for that
incident. Approval does not bypass validation. Any failed check returns a release
`BLOCK` decision and leaves no patch applied.

## Production requirements

Open mode and its embedded credentials are local demonstration features only. A real
deployment requires `api_key` mode at minimum and ultimately TLS, OIDC identity,
centralized RBAC, managed secrets, a sandboxed build runner, signed
patch bundles, branch protection, repository permissions, WORM audit export, dependency
and container scanning, egress restrictions, and independent post-change monitoring.
