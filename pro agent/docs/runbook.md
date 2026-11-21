# Runbook

## Local setup

### Windows (PowerShell + Docker Desktop)

```powershell
./scripts/dev.ps1 setup     # .env, PostgreSQL container, uv/npm deps, Chromium, migrate, seed
./scripts/dev.ps1 start     # portals, API, worker, UI in separate windows
./scripts/dev.ps1 check     # lint, type-check, unit + API security tests, UI build
./scripts/dev.ps1 reset     # DESTRUCTIVE to demo data (asks for confirmation)
```

### Ubuntu (Docker Engine)

```bash
scripts/dev.sh setup && scripts/dev.sh start
scripts/dev.sh check
```

Prerequisites: Docker, [uv](https://docs.astral.sh/uv/) 0.11+, Node.js 22. Ports: UI 5273, API 8300,
portals 8301-8303, fixture control 8309 (localhost only), PostgreSQL 55433 (localhost only).

### Full stack in containers

```bash
cp .env.example .env            # set secrets
docker compose up -d --build    # db, migrate+seed, api (serves UI on 127.0.0.1:8300), worker, portals
docker compose -f docker-compose.yml -f docker-compose.ports.yml up -d   # also publish portals on 18301-18303
```

## Deploying to a single Ubuntu VM

Assumptions: Ubuntu 24.04, 4 vCPU / 8 GB RAM / 40 GB disk, a DNS record for `$DOMAIN` pointing at the VM,
ports 80/443 open. Measured on the development machine (Windows 11, one run at a time, fixture mode):
headless Chromium peaked at about 300 MB working set across 4 processes; all Python processes (API,
portals, worker) together used about 200 MB. CPU was not measured. These are not capacity claims;
re-measure on the target VM with `docker stats procnav-worker-1` under the intended concurrency.
With `MAX_CONCURRENT_RUNS=2` the worker container is capped at 2 CPUs / 2 GB.

```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-v2 git
git clone <repo> procnav && cd procnav
cp .env.example .env
# Edit .env: APP_ENV=production, COOKIE_SECURE=true, DOMAIN, ACME_EMAIL, strong SESSION_SECRET,
# CREDENTIALS_KEY (Fernet), FIXTURE_CONTROL_TOKEN, all *_PASSWORD values, APP_BASE_URL=https://$DOMAIN
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose logs migrate     # the generated demo password is printed once if DEMO_PASSWORD is unset
```

The config validator refuses to start in production with development secrets, missing
`CREDENTIALS_KEY`, insecure cookies, or `DRY_RUN=false`. PostgreSQL and the fixture control API are on the
internal network only; Caddy returns 404 for `/_control`. Scenario reset and approvals always require
an authenticated administrator/approver. A portfolio viewer can be given the `viewer` role (read-only).

### Deployment smoke checks

```bash
curl -fsS https://$DOMAIN/api/health                       # db ok, workers_alive >= 1
# then in the UI as requester: create the demo request -> run reaches awaiting approval
# as approver: approve -> run completes with outcome purchased
# orders page: ledger reconciled, receipt verified; download the redacted receipt
# comparison page: CSV and PDF exports download
```

## Operations

| Task | Procedure |
|---|---|
| **Database migration** | `docker compose run --rm migrate` (alembic upgrade + checkpoint tables + grants). Migrations are forward-only in production; take a backup first. |
| **Rollback** | Redeploy the previous image tag. If a migration must be reverted: restore the pre-migration backup (preferred) or `alembic downgrade -1` after reviewing the downgrade. |
| **Backup (database)** | `docker compose exec db pg_dump -U postgres -Fc procnav > procnav-$(date +%F).dump` (also `suppliers` for demo continuity). Schedule daily; keep 14 days off-host. |
| **Backup (artifacts)** | `docker run --rm -v procnav_evidence:/e -v $PWD:/b alpine tar czf /b/evidence-$(date +%F).tgz -C /e .` |
| **Restore** | Stop api/worker; `pg_restore -U postgres -d procnav --clean --if-exists < dump`; untar evidence into the volume; start; run smoke checks. Evidence integrity is checked by SHA-256 on download. |
| **Evidence retention** | `EVIDENCE_RETENTION_DAYS` (default 30). The worker purges expired artifacts hourly per tenant. Screenshots can contain sensitive business data; shorten retention for real data. |
| **Browser credential rotation** | Update the secret store entry (`SUPPLIER_CREDENTIALS_JSON` or vault) for the credential reference; delete `browser_session_states` rows for that supplier (`DELETE FROM browser_session_states WHERE supplier_id = ...` as owner) so old sessions are not reused; set `rotated_at`. Rotating `CREDENTIALS_KEY` invalidates stored session state (it is discarded and re-created at next login). |
| **Failed-run recovery** | Check `/runs/<id>` activity and `GET /api/runs/<id>/steps`. Worker exceptions retry with backoff up to 5 attempts, resuming from the last checkpoint (a `resumed_from_checkpoint` event is logged). Dead jobs mark the run `failed` with `WORKER_ERROR`; start a new run for the request. |
| **Paused run** | Status `paused_for_human`: resolve the cause (e.g. supplier MFA for the service account), then *Retry after resolving* or *Skip and continue* in the run page (`POST /api/runs/<id>/resume`). |
| **Unknown-order reconciliation** | Intent status `unknown` means a click may have reached the supplier. Never resubmit manually. The worker checks order history for the intent key three times over ~10 s. If still ambiguous, an approver uses *Re-check supplier order history* on the order page (`POST /api/orders/<id>/reconcile`), or checks the supplier account directly and records the outcome. Absence leads to a fresh approval, never an automatic retry. |
| **Worker health** | `GET /api/health` → `workers_alive`; `worker_heartbeats` table; restart policy `unless-stopped`. |
| **Reset demo data** | `scripts/dev.sh reset` (asks for confirmation; refuses in production without an explicit flag). |
