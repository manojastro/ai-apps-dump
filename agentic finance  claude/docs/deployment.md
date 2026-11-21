# Optional deployment guide (not performed)

Nothing in this repository has been deployed. This is a plan for Google Cloud, following the project's defaults.
Every step that enables an API, creates a resource, changes IAM or deploys needs explicit approval and should
state the account and project first (`gcloud config list`).

## Target layout (one region, e.g. `asia-south1`)
| Piece | Service |
|---|---|
| engine API | Cloud Run service `spreadlens-engine` (`--min-instances=0`, `--max-instances=3`, 1 vCPU / 2 GiB for OCR) |
| worker | Cloud Run service `spreadlens-worker` running `python -m spreadlens.workflow.worker` (`--no-cpu-throttling`, min 1 only if you need continuous processing) or a Cloud Run job triggered on schedule |
| web | Cloud Run service `spreadlens-web` (Next.js standalone image) |
| eve agents (live mode) | one Cloud Run service per agent, or the five behind one service; Postgres workflow world (`@workflow/world-postgres`) for replicas |
| database | Cloud SQL for PostgreSQL 16, smallest tier, no HA for dev, connected with `--add-cloudsql-instances` (connector, no public IP) |
| files | Cloud Storage bucket, `SPREADLENS_STORAGE_BACKEND=gcs`, public access prevention on, ADC credentials |
| images | Artifact Registry (built by Cloud Build: `gcloud run deploy --source .` or `gcloud builds submit`) |
| secrets | Secret Manager: DB password, `SPREADLENS_EVE_SERVICE_TOKEN`, `SPREADLENS_AGENT_TOOL_TOKEN`, `AI_GATEWAY_API_KEY`, mounted with `--set-secrets` |

## Security
* One least-privilege service account per Cloud Run service (engine: Cloud SQL Client + bucket objectAdmin on its
  bucket + Secret Accessor on its secrets; web: none; agents: Secret Accessor on their secrets).
* Services private by default; only `spreadlens-web` would be public, and only after confirming that. The engine
  is called by web (service-to-service auth) and by agents.
* No service-account key files; use ADC / workload identity.
* Set `COOKIE_SECURE=true`, `SPREADLENS_CORS_ORIGINS` to the web origin, rotate the seed users out (do not run
  `spreadlens.seed` in production).

## Steps (outline)
1. Create the Artifact Registry repo, bucket, Cloud SQL instance and secrets (approval needed).
2. Run migrations as a Cloud Run job: `alembic upgrade head`.
3. Deploy engine, worker, web (and agents for live mode) from source with Cloud Build.
4. Configure `ENGINE_URL` for web, eve agent URLs and tokens for the engine, `SPREADLENS_ENGINE_URL` for agents.
5. Optional: OTLP endpoint for traces (`SPREADLENS_OTEL_EXPORTER_OTLP_ENDPOINT`), log-based metrics on
   `metric_events`.

Terraform (if wanted): `google` provider, GCS remote state, variables for project and region; no hard-coded IDs.
