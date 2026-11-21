# Deployment plan (draft, nothing deployed)

Status: **planned**. No cloud resource has been created. Every step below needs your approval first.

## Blockers before any deployment

1. Get Docker working and verify both images build and `docker compose up` runs.
2. Push the repo and get CI green.
3. Run the live copilot eval and review failures.

## Target on Google Cloud

| Part | Choice | Notes |
|---|---|---|
| Frontend | Cloud Run | `--min-instances=0`, capped with `--max-instances` |
| Backend | Cloud Run | `--min-instances=0`, capped. ML libraries make cold starts slow, so measure them |
| Daily refresh | Cloud Run job with Cloud Scheduler | Replaces the in-process scheduler, so `ENABLE_SCHEDULER=false` |
| Database | Cloud SQL for PostgreSQL 16, smallest workable tier, no HA for dev | Supports pgvector. Connect through `--add-cloudsql-instances`, not a public IP |
| Model artifacts | Cloud Storage bucket | Today they sit on local disk, so this needs a small code change |
| Images | Artifact Registry, built by Cloud Build | Same region as everything else |
| Secrets | Secret Manager through `--set-secrets` | `JWT_SECRET`, `ANTHROPIC_API_KEY`, database password |
| Identity | One least-privilege service account per service | No key files |
| Access | Private by default | Public access only once you confirm it |

Cloud Run instances are stateless, which affects two things. The in-memory rate limiter counts per instance, so it needs Redis, or `--max-instances=1` for a demo. Model artifacts must also come from Cloud Storage.

## Cost

Not estimated yet, because the figures depend on region, Cloud SQL tier and usage, and I have not checked current pricing. To produce a real estimate:

- Enter the items above in the Google Cloud Pricing Calculator. Cloud SQL will likely be the main fixed cost, because it runs all the time.
- For the LLM, measure tokens per question in the live eval first. Cost per question is then input tokens and output tokens multiplied by the current model price, less any prompt-caching saving.

## Order of work, each step needing approval

1. Confirm the Google Cloud account, project and region.
2. Enable the required APIs.
3. Create Artifact Registry, Secret Manager entries and service accounts.
4. Create Cloud SQL and run migrations.
5. Deploy the backend, then the frontend, both private.
6. Load synthetic data and smoke-test.
7. Add the scheduled job.
