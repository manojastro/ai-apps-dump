# Demo runbook

1. Run `docker compose up --build` and wait for API/web health checks.
2. Open <http://localhost:3003/incidents>. Six scenario seeds should be visible.
3. Open **Payment TLS failures hidden behind storefront CPU spike** and choose **Investigate now**.
4. Confirm four workers complete and every record in the evidence explorer has an `EV-` ID.
5. Inspect the timeline and dependency graph. The graph should show `storefront → checkout-api → payment-api` context.
6. Open hypothesis comparison. The critic should reject storefront CPU because failures continue after CPU recovery, then elevate the independent payment TLS evidence.
7. Open the RCA editor. Remove one `[EV-…]` token and save; the citation gate rejects the edit. Restore it and save successfully.
8. Open Evaluation and run 60 cases, or run `make eval`. Inspect both report formats in `evaluation/reports`.
9. Review API counters in Prometheus and admin audit entries at `GET /api/v1/audit` with `X-Role: admin`.

For a terminal-only path, run `make incident`; it injects the misleading case, investigates it, reports the critic decision, and prints the evidence-cited RCA.
