# GitHub Actions

The workflows live in `.github/workflows/` because GitHub only runs workflows from that folder
(this deviates from the layout in BUILD_PROMPT.md; see docs/DECISIONS.md, ADR-009).

- `ci.yml`: lint, type check, unit tests and the fake-LLM eval on every push.
- `deploy.yml`: `workflow_dispatch` only, gated by the `production` environment's required reviewers.
