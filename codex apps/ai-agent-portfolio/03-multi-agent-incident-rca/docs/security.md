# Security and threat model

Trust boundaries are explicit: alert fields, logs, tickets, telemetry labels, and editor content are untrusted. Tool calls accept Pydantic schemas with scenario/service/time bounds and expose no arbitrary PromQL, Cypher, SQL, URL fetch, file, or shell execution. Adapters are read-only.

Before provider use, NUL bytes and excess length are removed, configured secret assignments are replaced with `[REDACTED]`, common prompt-injection instructions and role tags are neutralized, and the result is wrapped as an untrusted observation. This is defense in depth; production should add upstream log access controls and a dedicated DLP policy.

Write and investigation operations require `investigator` or `admin`; evaluation and audit access require `admin`. Every create, investigation, RCA edit, and evaluation action is recorded. The header-based demo identity is not authentication and must be replaced with signed identity assertions behind TLS.

The final-output boundary is the citation gate. A claim must contain at least one known immutable evidence ID, and its rendered Markdown must retain every reference. Unknown evidence, duplicate citation lists, or missing rendered citations cause rejection. This blocks unsupported factual text from the stored RCA structure; reviewers must still assess whether cited evidence logically entails the claim.

Residual risks include poisoned but plausible telemetry, compromised data-source credentials, false temporal correlation, and excessive access through an incorrectly configured reverse proxy. Apply least-privilege source credentials, network policies, signed change events, retention limits, rate limits, and human approval before external publication.

