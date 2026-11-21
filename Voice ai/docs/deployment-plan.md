# Deployment plan (NOT EXECUTED: awaiting your explicit approval)

Nothing has been deployed, pushed, or enabled. This is a plan only. Defaults follow your global GCP rules:
Cloud Run, Cloud Build + Artifact Registry, Secret Manager, least-privilege service accounts, min-instances 0,
private services, no service-account keys.

**Important limitation first:** the app uses a single SQLite file shared by the API, workers and console. Cloud Run
instances do not share a writable disk, so a real Cloud Run deployment needs the data layer changed (for example
Cloud SQL for PostgreSQL, smallest tier, no HA, via the Cloud SQL connector). The orchestrator and queue code use
SQLAlchemy Core/ORM, but `claim()` relies on `UPDATE ... RETURNING` with a sub-select, which needs
`FOR UPDATE SKIP LOCKED` on Postgres. That migration has not been done or tested.

Because the system is synthetic-data-only and not for real patient use, the lowest-risk option is to skip
cloud deployment and run `docker compose up` locally for demos.

## If you approve a cloud demo

Before running anything I will state the account and project and ask again for each gate:

1. Confirm account/project/region (`gcloud config list`; I will not change it without asking).
2. Enable APIs (approval needed): `run`, `cloudbuild`, `artifactregistry`, `secretmanager`, `sqladmin`.
3. Create (approval needed): Artifact Registry repo, one service account per Cloud Run service, secrets
   (session secret; `ANTHROPIC_API_KEY` only if REAL mode is approved), Cloud SQL instance (db-f1-micro).
4. Build with Cloud Build: `gcloud builds submit --tag REGION-docker.pkg.dev/PROJECT/eir/eir:TAG .`
5. Deploy three services from the same image, all in MOCK mode, private by default, `--min-instances=0`,
   `--max-instances=2`, secrets via `--set-secrets`, Cloud SQL via `--add-cloudsql-instances`:
   - `eir-api`    `uvicorn app.main:app`
   - `eir-console` `uvicorn app.console.app:app` (staff login is demo-grade, so keep it private/IAM-protected)
   - `eir-worker`  `python -m app.worker` as a Cloud Run worker pool (always-on), `EIR_WORKERS=2`
6. Tracing: a managed Phoenix is not part of this plan; Cloud Trace via the OTLP exporter is an option.
7. `--allow-unauthenticated` is **not** used unless you confirm a service is meant to be public.

Estimated cost: not measured. Cloud SQL micro and an always-on worker are the only non-zero-at-idle items.
