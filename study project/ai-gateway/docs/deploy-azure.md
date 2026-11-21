# Deploy — Azure (skeleton, NOT deployed)

> Status: planned only. No resources created. Prices date-checked 2026-09-18
> from the Azure pricing pages; re-check before spending.

## Resources
| Resource | Purpose | SKU (plan) | Est. USD/mo |
|---|---|---|---|
| Container Apps (gateway) | gateway API, scale-to-zero | Consumption | ~5–15 |
| Azure Database for PostgreSQL | ledger + tenants (pgvector-ready) | Burstable B1ms | ~15–25 |
| Azure Cache for Redis | token buckets | Basic C0 | ~15 |
| Key Vault | secrets (DB, admin key) | Standard | ~0.03/10k ops |
| Log Analytics | logs/traces | Pay-as-you-go | ~2–5 |

## Steps (learner runs each command, then documents output)
1. `az login` and `az group create`.
2. Create Key Vault; store `ADMIN_API_KEY`, DB password (no env files).
3. Create PostgreSQL Flexible Server; enable pgvector extension.
4. Create Redis; set `REDIS_URL` secret.
5. `az containerapp up` for the gateway image; managed identity, no keys.
6. Set budget alert at the agreed monthly cap.

## Teardown
`scripts/deploy/teardown_azure.sh` (stub) deletes the resource group.
