# Demo (90 seconds)

1. (0:00) "Every app calls one front door." Show `POST /v1/chat/completions`
   with `X-Task: triage` -> cheap model reply.
2. (0:20) Create tenant: `POST /admin/tenants` -> key shown ONCE.
3. (0:35) Wrong key -> 401. Disallowed model -> 403 with reason.
4. (0:45) Force fallback: send `[FAIL:triage-cheap]` -> response has
   `fallback_used: true`, audit log shows `provider_fallback`.
5. (0:55) Injection blocked: "Ignore all previous instructions..." -> 400
   with reason; ledger row has `blocked=1`.
6. (1:05) Red-team numbers from `reports/redteam.json`; KV-cache 1 GiB math.
7. (1:20) Teardown: `scripts/deploy/teardown_azure.sh` (stub, cloud NOT
   deployed in this slice).
