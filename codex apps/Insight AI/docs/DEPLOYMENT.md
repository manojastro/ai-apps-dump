# Deployment and operations

## Tested local profile

Use the README's Windows commands. Linux/WSL2 steps and the GitHub Actions workflow are prepared but are not claimed as executed merely because configuration exists. The web build and backend must use the same repository root so version and lock metadata resolve correctly.

Production web serving requires three processes: `uv run --locked uvicorn services.api.main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 65`, `uv run --locked python -m services.worker.runner`, and `npm start -- --hostname 127.0.0.1`. Run `npm run build` first. The development launcher starts the same API/worker plus Next dev.

## Prepared Compose profile — runtime unverified

On a host with a working Docker Linux engine:

```powershell
python scripts/docker_env.py
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs setup
```

Secrets are generated into a gitignored `.env` without printing values. Do not use unrestricted `docker compose config` output in shared logs because it expands secrets. Setup runs migrations and generates the local admin password into a named volume. Read it privately using `docker compose exec api cat /app/.productionlens/admin-password.txt`.

The UI is bound to loopback port 3000; Prometheus and Jaeger are loopback-only at 9090/16686. Databases and Redis have no host ports. Demo containers have a one-core CPU limit and 256 MiB memory cap. No Docker socket is mounted into the application. Use `docker compose down` to stop services while retaining volumes. Do not add `-v` unless deliberately discarding their data.

## Linux VM preparation

Before a public deployment, complete the outstanding integration/security checks in KNOWN_LIMITATIONS.md. On an approved Linux VM, install a supported Docker engine and Compose, use persistent encrypted storage, restrict SSH and firewall ingress, and put a TLS reverse proxy in front of the loopback web port. Set `SECURE_COOKIES=true` and `ALLOWED_ORIGINS` to the exact HTTPS origin. Keep model and database secrets in a server-controlled secret store or protected environment file. Never copy `.productionlens` credentials into frontend images or artifact bundles.

Monitor `/health/live`, `/health/ready`, worker heartbeat, failed jobs, database capacity and backup success. A database ping is not proof that all external sources are healthy. Separate API, worker and telemetry health alerts.

## Backup and restore

For the local SQLite profile, stop API and worker before copying `.productionlens/platform.db` and `.productionlens/checkpoints.db`. Copying an actively written SQLite file without its WAL is unsafe. Restore both together into a stopped instance with the same schema/runtime, then start and inspect resumed jobs. Protect backup credentials and data like the source files.

For PostgreSQL, use `pg_dump` in a protected maintenance context, retain encrypted copies off-host and periodically restore into an isolated verification database. Include graph checkpoint tables. Do not test restore against the active platform database. Preserve model/version and evaluation artifacts alongside the database backup. Named volumes alone are not backups.

## Troubleshooting

- API disconnected: check port 8000, server logs and that the API URL matches the frontend proxy.
- Worker disconnected: start `python -m services.worker.runner` from the repository root. Queued jobs remain persisted.
- Provider unavailable: configure model identifier, secret and allowed endpoint; run the capability test. Replay is never a fallback for a failed live run.
- Approval expired or revision changed: create a new investigation/proposal. An old approval cannot authorize changed parameters.
- Docker engine pipe unavailable: verify Docker Desktop's Linux engine/WSL2 prerequisites. Container verification is blocked until the engine responds to `docker info`.
- Slow benchmark: reports include process startup overhead. Timeouts are failures, and measured latency thresholds are not silently relaxed.
