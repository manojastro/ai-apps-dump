# Deployment plan (NOT executed)

Status: **pending your approval.** Nothing has been deployed or pushed. Every command below changes
cloud state or costs money, so each one waits for an explicit "yes" in chat, along with the gcloud
account and project it will run against.

## Target: Google Cloud Run (MOCK mode on by default)

Why Cloud Run: it runs the existing container as is, scales to zero (`--min-instances=0`) so an
idle demo costs about nothing, builds with Cloud Build, and stores images in Artifact Registry.
Render, Railway or Fly.io would also work; the same Dockerfile applies.

Demo constraints:
- `LLM_MODE=mock` by default, so a public demo never spends tokens. Real mode would need the key in
  Secret Manager and a decision about who may trigger runs.
- SQLite lives on the container's local disk, so state resets when an instance is replaced. That is
  fine for a demo (it re-seeds on start). Persistent state would need Cloud SQL or Firestore and is out
  of scope.
- `--max-instances=1`: SQLite and the sandbox are per-instance, so one instance keeps the demo
  consistent and caps spend.

## Commands (to run only after approval)

```bash
# 0. Confirm where this will run (read-only)
gcloud config list account project

# 1. Set variables (choose your existing region)
PROJECT_ID=<your-project>; REGION=<your-region>; REPO=truthkeeper; SA=truthkeeper-run

# 2. Enable APIs (approval gate)
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  --project "$PROJECT_ID"

# 3. Artifact Registry repo (approval gate)
gcloud artifacts repositories create "$REPO" --repository-format=docker --location="$REGION" --project "$PROJECT_ID"

# 4. Least-privilege runtime service account, no keys (approval gate)
gcloud iam service-accounts create "$SA" --display-name="TruthKeeper Cloud Run" --project "$PROJECT_ID"

# 5. Build with Cloud Build (approval gate)
gcloud builds submit --tag "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/app:v1" --project "$PROJECT_ID"

# 6. Deploy, private by default (approval gate)
gcloud run deploy truthkeeper \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/app:v1" \
  --region "$REGION" --project "$PROJECT_ID" \
  --service-account "$SA@$PROJECT_ID.iam.gserviceaccount.com" \
  --set-env-vars LLM_MODE=mock,TK_GENERATED_DIR=/app/var/generated,TK_SANDBOX_DIR=/app/var/sandbox,TK_STATE_DB=/app/var/state.db,TK_GROUND_TRUTH=/app/var/generated/ground_truth.json,TK_REGRESSIONS_DIR=/app/var/regressions \
  --cpu 1 --memory 512Mi --min-instances 0 --max-instances 1 \
  --no-allow-unauthenticated

# 7. Open it yourself through an authenticated proxy
gcloud run services proxy truthkeeper --region "$REGION" --project "$PROJECT_ID"
```

Optional, each a separate approval:
- Public URL: redeploy with `--allow-unauthenticated`, only if you confirm the demo is meant to be public.
- Real LLM mode: `gcloud secrets create anthropic-api-key ...`, grant the runtime SA
  `roles/secretmanager.secretAccessor` on that one secret only, then deploy with
  `--set-secrets ANTHROPIC_API_KEY=anthropic-api-key:latest --set-env-vars LLM_MODE=real`.
  Never use plain `--set-env-vars` for the key.

## Rollback / teardown (approval gate)

```bash
gcloud run services delete truthkeeper --region "$REGION" --project "$PROJECT_ID"
gcloud artifacts repositories delete "$REPO" --location "$REGION" --project "$PROJECT_ID"
gcloud iam service-accounts delete "$SA@$PROJECT_ID.iam.gserviceaccount.com" --project "$PROJECT_ID"
```

## Before deploying
- [ ] `docker compose up --build` verified on a machine with Docker (not verified yet: Docker is not
      installed on the build machine)
- [ ] Phoenix image tag pinned in `docker-compose.yml`
- [ ] Git repo pushed to GitHub (needs your approval) so CI runs
