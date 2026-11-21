# Threat Model

## Assets and adversaries

Assets are cluster availability, remediation credentials, approval integrity, runbook integrity, audit history, and incident telemetry. Relevant adversaries include a malicious incident payload, prompt-injected log text, compromised viewer/operator account, misconfigured policy, and a faulty model or runbook.

| Threat | Control in the POC | Residual / production action |
|---|---|---|
| Model generates a destructive or shell action | Model returns structured hypotheses only; policy and typed executor are external; no shell interface | formally validate provider output and isolate model network egress |
| Namespace escape | policy equality check plus adapter hard-coded namespace | admission policy and separate cluster/account |
| Over-privileged Kubernetes identity | read-only and narrowly scoped executor Roles are separate | short-lived workload identity and admission tests |
| HIGH/destructive action executes | absent from allowlist and destructives disabled | external change platform integration |
| Approval forgery/replay | RBAC bearer dependency, CSRF header, incident must be pending, decision persisted/audited | OIDC/MFA, origin validation, signed sessions |
| Duplicate action | unique idempotency key, terminal guard, action cooldown | distributed lock and transactional outbox |
| Failed recovery leaves changed state | original state persisted before action; automatic typed rollback | per-tool compensating-action drills |
| Secrets leak to model/log | no secret fields enter model state; settings use environment | vault, DLP/redaction gateway, encrypted audit store |
| Prompt injection through evidence | deterministic model treats evidence as data and has no tools | instruction/data delimiters and adversarial provider evals |
| DoS | input bounds and in-process 120 request/minute limiter | gateway/WAF distributed limits |
| Audit tampering | append-only application behavior | immutable external audit sink and signatures |

Destructive data operations, namespace-wide actions, arbitrary commands, and security-sensitive mutation are disabled in the demo.

