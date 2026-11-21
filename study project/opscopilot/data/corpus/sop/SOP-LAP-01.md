---
doc_id: SOP-LAP-01
title: "Reimage a store laptop from USB"
doc_type: sop
service: laptop
status: active
updated_at: "2025-05-01"
synthetic: true
---

# Reimage a store laptop from USB

## Purpose

Rebuild a faulty store laptop to the gold image.

## Steps

1. Back up `C:\Users` to the NAS.
2. Boot the gold USB and run the Acme image.
3. Join the domain, install the VPN client 5.4.
4. Return BitLocker key in the device portal (see KB0006).

## Escalation

If BitLocker recovery appears, fetch the key per KB0006; escalate to EUC if the TPM fails.

---
*Synthetic data for Acme Retail Ltd. Fictional — no real customer or employee data.*
