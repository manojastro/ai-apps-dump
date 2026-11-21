# SQLite migrations

`Repository.initialize()` applies `001_initial`, `002_bound_approval`, and
`003_require_fresh_bound_reapproval` idempotently. Version 002 adds evidence-comparison
fields plus immutable action, patch-preview, and fixed-source approval bindings. It
never infers missing legacy hashes. Version 003 moves every still-executable historical
approval to `REAPPROVAL_REQUIRED`, because the older workflow did not verify the exact
persisted preview bytes. The immutable legacy row is retained; a verified reviewer can
append a new fully bound attestation. Future changes must preserve existing evidence
and never weaken immutable audit or approval triggers.
