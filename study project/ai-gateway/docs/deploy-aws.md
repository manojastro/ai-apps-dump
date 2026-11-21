# Deploy — AWS (skeleton, NOT deployed)

> Status: planned only. No resources created. Prices date-checked 2026-09-18
> from the AWS pricing pages; re-check before spending.

## Resources
| Resource | Purpose | Option (plan) | Est. USD/mo |
|---|---|---|---|
| App Runner or ECS Fargate | gateway API | 0.25 vCPU / 0.5 GB, scale-to-zero | ~5–15 |
| RDS Postgres | ledger + tenants (pgvector via extension) | db.t4g.micro | ~15–20 |
| ElastiCache Serverless / MemoryDB | token buckets | smallest | ~10–15 |
| Secrets Manager | secrets (DB, admin key) | per secret + calls | ~1–2 |
| CloudWatch | logs/traces | Pay-as-you-go | ~2–5 |

## Steps (learner runs each command, then documents output)
1. `aws configure` with an IAM role (no long-lived keys where avoidable).
2. Store secrets in Secrets Manager.
3. Create RDS Postgres; confirm pgvector extension availability.
4. Create ElastiCache; set `REDIS_URL`.
5. Deploy the gateway container; attach IAM task role.
6. Set AWS Budget alert at the agreed monthly cap.

## Teardown
`scripts/deploy/teardown_aws.sh` (stub) destroys the stack.
