---
doc_id: SOP-IAM-01
title: "Joiner-mover-leaver account provisioning"
doc_type: sop
service: iam
status: active
updated_at: "2025-05-01"
synthetic: true
---

# Joiner-mover-leaver account provisioning

## Purpose

Process HR joiner, mover, and leaver events within one business day.

## Steps

1. Pull the daily HR feed at 07:00.
2. Create AD + mailbox for joiners.
3. Adjust groups for movers the same day.
4. Disable leavers within 1 hour of exit time.

## Escalation

If SAP roles are missing on day one, apply the KB0025 manual step, then inform IAM Ops.

---
*Synthetic data for Acme Retail Ltd. Fictional — no real customer or employee data.*
