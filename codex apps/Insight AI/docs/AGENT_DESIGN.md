# Investigation agent

Replay is a fixed diagnostic program, not an LLM. It collects metrics, dependency topology, traces, logs, deployment history and configuration through the same restricted tool contract. Rules require corroborating observations and abstain on missing, stale, truncated or contradictory evidence. The `script-regression` version intentionally omits the pool-exhaustion rule to demonstrate a measurable regression.

Live mode uses an OpenAI-compatible provider. It starts with metrics and topology, then chooses tools dynamically from a bounded function schema. The model receives only incident context and collected evidence. It can submit a structured diagnosis; code checks its schema, evidence ownership, integrity and independent-source count. This does not automatically prove semantic claim support. The model cannot execute shell, SQL, arbitrary URLs or recovery actions.

Graph nodes separate initial context, investigation and findings preparation. Durable checkpoints and database events preserve progress. Model outputs are public findings/tool choices; the system never requests private chain-of-thought. Logs and runbooks are explicitly untrusted data.

Budgets: default 12 tools, 8 logical model calls, 24,000 tokens and 120 seconds. Tool reservation precedes I/O. Model usage is reconciled when the provider supplies it; unknown usage remains unknown and a conservative budget estimate is charged. Provider retries are bounded, but a timed-out provider may still bill an unknown amount. Cost remains null without reliable pricing. Real-provider spending and resume behavior still require live validation.

Recovery proposals are independent of model tool permissions. Implemented automatic execution is limited to the local replay lab. A supported diagnosis can produce a hash-bound, expiring proposal with target, parameters, evidence, risks, preconditions and reset instructions. A reviewer approves or rejects that exact action. Live recovery is not available in this version.
