# Evaluation

## Objective

Evaluation measures whether the reliability platform finds known faults and whether an observed agent candidate can pass a multi-dimensional release gate. It does not grade prose by visual inspection.

## Labelled dataset

The dataset is generated deterministically by `SyntheticBackupAgentAdapter`. Its nine cases cover:

- reliable success;
- loop and duplicate calls;
- excessive token, context, and cost usage;
- wrong/unsafe tool routing;
- claimed success with no artifact;
- incomplete artifact with checksum failure;
- latency SLO violation;
- prohibited command-style arguments;
- empty required retrieval.

Ground-truth labels live beside the generator in `backend/app/simulator.py`. Tests require predicted labels to match every label set exactly, making accidental detector drift visible.

## Detector benchmark metrics

| Metric | Calculation |
|---|---|
| Task-success detection accuracy | success/failure predicted from task-failure findings compared with scenario truth |
| Tool-call evaluation precision | true positive findings / all positive findings |
| Tool-call evaluation accuracy | exact equality of predicted and labelled tool-failure classes per scenario |
| Detection recall | true positive findings / all labelled findings |
| Outcome-verification accuracy | read-only artifact-provider result compared with scenario outcome truth |
| Loop detection accuracy | `AGENT_LOOP` present on the scenario named `looping` |
| Per-class recall | recall for every labelled fault class, each required to equal 1.0 |
| Mean cost | mean deterministic trace cost across the dataset |
| Scenario count | number of executed labelled cases |

The evaluator passes at precision and recall of at least 0.90 and requires correct outcome classification for every case.

## Release quality gate

Both versions are executed over the same versioned set of nine named scenarios. In this local POC, the release gate accepts only the exact `SyntheticVersionBenchmarkRunner` instance created and registered inside `Evaluator`; a constructor-injected runner, subclass, or separately instantiated built-in runner blocks before its `run` method is called. A server-owned registry maps each supported version to a deterministic version-artifact digest. The built-in executor runs the requested version behavior and binds that digest into the execution specification, top-level result, and every raw case.

For each version the server assigns a unique execution nonce plus per-case run IDs and server-observed verification windows. Returned raw traces must contain the requested `agent_version`, exact dataset case/run identities, unique run IDs, artifact snapshots, registry artifact digest, and matching version/run evidence digests. The gate reconstructs outcome verification and detector results from those raw inputs rather than trusting summary metrics. A candidate passes only if every check passes:

| Dimension | Threshold relative to current |
|---|---|
| Success rate | no more than 2 percentage-point drop |
| Quality | no more than 3 point drop |
| Cost/task | no more than 10% increase |
| P95 latency | no more than 15% increase |
| Tool accuracy | no more than 2 point drop |
| Safety | no regression allowed |
| Version-specific evidence | distinct valid nonce/digest bindings for baseline and candidate |
| Trusted executor | exact server-registered local executor identity |

`1.1.0-safe` is the positive control. `1.1.0-regressed` is the negative control and must return `BLOCK`. These are executions of deterministic synthetic version behaviors, not measurements from a real hosted model.

`BenchmarkRunner` remains an interface for a future production adapter, but the local gate intentionally rejects remote implementations. Production enablement requires a trust-store-backed verifier for a signed runner attestation that covers the candidate build/artifact digest, dataset version, execution nonce, case identities, and raw evidence digest. Recomputable public SHA-256 hashes provide integrity consistency only; they cannot establish who executed a workload or prevent a deep relabel/re-hash by an untrusted runner.

## Reproduce

```bash
python -m pytest tests/test_detectors.py tests/test_evaluation.py tests/test_adversarial_acceptance.py
python scripts/seed_demo.py
```

Over HTTP:

```bash
curl -X POST http://localhost:8101/api/v1/evaluations/run
curl -X POST http://localhost:8101/api/v1/regression/compare \
  -H "Content-Type: application/json" \
  -d '{"current_version":"1.0.0","candidate_version":"1.1.0-regressed"}'
```

Evaluation results are persisted in `evaluations` and the regression decision is also written to `audit_events`.

## Interpretation limits

Perfect benchmark scores show that deterministic rules match this small known dataset. They do not demonstrate generalization to novel agent frameworks or production distributions. The registry digests identify deterministic POC manifests, not signed container provenance. A production evaluation should add real anonymized traces, adversarial cases, confidence calibration, versioned dataset splits, temporal holdouts, statistical confidence intervals, and signed remote execution attestation.
