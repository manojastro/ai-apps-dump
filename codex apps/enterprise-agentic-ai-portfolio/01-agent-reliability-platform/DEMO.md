# Demo Runbook

## Goal

Demonstrate that the platform rejects an agent's unsupported success claim, explains the mismatch with evidence, prevents premature action execution, and blocks a regressed release.

## Start

```bash
python -m pip install -r requirements.txt
uvicorn backend.app.main:app --host 127.0.0.1 --port 8101
```

Open `http://127.0.0.1:8101`.

## Five-minute walkthrough

1. Point out `MOCK` mode and the empty/previous fleet state.
2. Choose **Hallucinated success** and run the investigation.
3. Show that `CLAIMED = SUCCESS`, while `VERIFIED = MISMATCH` because artifact, completeness, checksum, and creation-time checks failed.
4. Show the typed root cause, confidence, and persisted evidence IDs.
5. In Approval Queue, attempt execution before approval through the API; it returns HTTP 403.
6. Approve from the dashboard. Explain that approval does not itself execute.
7. Execute the safe simulation and show the persisted policy before/after state plus calculated post-action validation.
8. Compare `1.1.0-regressed`; both versions execute the same named benchmark and the release decision becomes `BLOCK` from derived failed dimensions.
9. Run **Benchmark evaluator** and show deterministic accuracy metrics.

## CLI evidence

With the server running:

```bash
python scripts/smoke_test.py http://127.0.0.1:8101
```

Expected final line resembles:

```text
SMOKE PASS: incident=inc_... detections=2 regression_gate=BLOCK
```

For a populated fleet:

```bash
python scripts/seed_demo.py
```

## Suggested follow-up scenarios

- **Agent loop:** show repeated tool steps and automatic eligibility of a low-risk step budget.
- **Cost + context spike:** show that outcome succeeds but reliability guardrails still open an incident.
- **Partial completion:** distinguish artifact existence from checksum verification.
- **Unsafe action attempt:** show inert command text, critical finding, and the fixed controller allow-list.
- **Reliable baseline:** show that validation persists without creating an incident.

## Reset local demo data

Stop the server and remove only `data/reliability.db` plus its optional `-wal` and `-shm` companions. The schema is recreated on next startup. With Docker, use `docker compose down -v` only when discarding the demo volume is intended.
