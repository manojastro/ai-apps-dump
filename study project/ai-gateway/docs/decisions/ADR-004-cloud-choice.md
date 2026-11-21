# ADR-004 — Cloud choice still open (default Azure)

Date: 2026-09-18. Status: proposed (learner decides, default Azure).
Context: whole-stack deploy with managed Postgres + Redis + secrets + budget.
Options: Azure (Container Apps, Flexible Postgres, Key Vault) vs AWS
(App Runner/ECS, RDS, Secrets Manager). Both skeletons in docs/.
Decision rule: pick the cloud with the cheaper scale-to-zero path inside the
learner's monthly budget; document the date-checked prices in the deploy doc.
Mock-first slice runs fully offline either way.
