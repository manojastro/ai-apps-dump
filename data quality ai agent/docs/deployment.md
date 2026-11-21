# Deployment and operations

## Native local application

Use the root README commands with one Uvicorn worker. The root `uv.lock` owns backend, simulator
and evaluation dependencies. Alembic migrations run during API startup. The native SQLite files
are under `.runtime/`; preserve both application and checkpoint databases when backing up.

## Compose

`docker compose up --build -d` builds non-root backend and frontend images and starts PostgreSQL
with pgvector. Defaults are strictly local demo credentials. Stop with `docker compose down`;
the named volume is retained. Changing POSTGRES_PASSWORD after initialization does not rotate the
existing database role. Configure proper credentials before first initialization outside a demo.

`scripts/postgres_smoke.py`, run inside the backend container, verifies migrations, filtered vector
retrieval, closed/reopened checkpoints and approval resume. CI builds containers and executes this
test plus browser smoke. These container checks have not run locally because the engine is unavailable.

For traces, set this in `.env` before starting Compose:

```dotenv
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4318
```

Then run `docker compose --profile observability up --build -d` and open http://localhost:16686.
Graph nodes produce OpenTelemetry spans with incident, pipeline, attempt and duration attributes.
Structured workflow logs and persisted event records complement traces. Metrics are exposed through
`/api/v1/metrics/summary` and incident records; a Prometheus metrics exporter is not implemented.
For a native backend use `http://localhost:4318` as the OTLP endpoint instead.

## Optional Kubernetes / AKS

Manifests are in `deploy/kubernetes`. They provide Deployments, ClusterIP Services, configuration,
secret references, probes, resource budgets and non-root security contexts. They do not provision a
paid cluster, database or public ingress and have not been applied to a live cluster.

1. Provision a PostgreSQL database with the pgvector extension available. Permit the migration role
   to create required application/checkpoint tables; constrain runtime permissions before production.
2. Build both Dockerfiles, push to your registry (ACR for AKS), and replace image names in a Kustomize
   overlay with your registry paths and immutable tags/digests. Configure image pull access.
3. Create namespace `recoverygraph`. Create Secret `recoverygraph-secrets` there using your secret
   manager, containing `DATABASE_URL`, `CHECKPOINT_URL`, and `API_TOKEN`. The application URL uses
   `postgresql+psycopg://...`; the checkpoint URL uses `postgresql://...`. Use TLS connection settings
   supported by your database. Never commit the actual secret manifest.
4. Inspect the rendered manifests with `kubectl kustomize deploy/kubernetes`. Review your selected
   cluster/context and apply explicitly with `kubectl apply -k deploy/kubernetes`.
5. Use `kubectl -n recoverygraph port-forward service/frontend 8080:8080` for a private demo. Configure
   TLS ingress and ALLOWED_ORIGINS before external access. Enter API_TOKEN in Connection settings.

The backend deliberately has one replica and Recreate rollout strategy. Multiple replicas require
distributed execution ownership first. Approval checkpoints survive process restarts in PostgreSQL;
active work needs explicit resume after interruption. Run migrations as a dedicated deployment job
when introducing multiple workers rather than allowing concurrent startup migrations.

References: [GitHub setup-node](https://github.com/actions/setup-node),
[uv setup action](https://github.com/astral-sh/setup-uv),
[Kubernetes probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/).
