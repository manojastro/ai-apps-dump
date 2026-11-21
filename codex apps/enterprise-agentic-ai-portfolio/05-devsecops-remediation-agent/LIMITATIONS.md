# Limitations

- The deterministic scanner recognizes only exact patterns in three authored fixtures;
  it is not a substitute for Semgrep, CodeQL, Trivy, SCA, container, or IaC scanning.
- Reachability facts are fixture metadata, not a call-graph or runtime trace.
- Fixes are exact reviewed transformations. This is deliberately safer than free-form
  generation but cannot remediate arbitrary code.
- Validation is static. It preserves a named function contract but does not run unit,
  integration, build, or behavioral tests because fixture/generated code is never
  executed in this safe POC.
- The local workspace is not a Git branch and no pull request is created.
- SQLite, process-local telemetry, and demo/API-key identity maps are not production
  control-plane infrastructure.
- Release risk values demonstrate an explainable policy, not calibrated enterprise
  risk probabilities.
- Mock reasoning does not exercise LLM latency, token use, malformed output, or provider
  failure behavior.

Future versions should add real scanner adapters, SBOM and dependency context, an
isolated network-denied build runner, test and scan attestations, signed commits and PR
integration, OIDC/RBAC, OpenTelemetry, broader benchmark cases, and post-release
verification.
