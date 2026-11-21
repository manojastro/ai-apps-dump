# CI guide

The reusable example at `.github/workflows/evaluation.yml` installs deterministic dependencies, runs tests, evaluates the included target, proves a deliberately bad candidate is rejected, applies the real gate, writes Markdown to the job summary, and uploads JSON/Markdown artifacts.

Quality gates enforce:

1. absolute floors for critical metrics;
2. candidate regression relative to the pinned baseline (default 3%);
3. p95 latency and per-request cost ceilings;
4. zero forbidden/unsafe tool calls.

`evalharness gate` prints machine-readable JSON and exits `1` on failure. Commit a reviewed gate configuration and store production baselines in durable PostgreSQL/object storage. Never silently replace a baseline from a pull request.

