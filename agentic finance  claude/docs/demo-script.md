# Five-minute portfolio demo

Setup: [local-setup.md](local-setup.md) option A, then `uv run python -m spreadlens.seed --demo`.

1. **Sign in** as `analyst@demo.local`. Point out the header badge: *DEMO processing (deterministic, no model calls)*
   — the same flow runs with eve agents in live mode, and a live failure never silently becomes demo output.
2. **Dashboard → Aravalli Polymers Limited.** Two reports were processed (FY2025, FY2026 with restated comparatives).
   Open a document's *Workflow trace*: durable stages, the five agents' executions, the tools each used, artifacts,
   tokens and cost.
3. **Open the Standalone spread.** Three periods side by side; original and standardised labels; mapping confidence.
4. **Click "Total assets 2025".** The source page renders with the exact cell boxed. Show raw text `2,670.70`,
   parsed value, ×10,000,000 crore factor, normalized base units, mapping rationale, the FY2026 document's
   comparative and which value is preferred.
5. **Exception queue.** R10 shows revenue and other expenses were *restated* in the FY2026 report — both versions
   kept, restated preferred. Unmapped cash-flow detail rows are listed but still used in subtotal checks.
6. **Upload `10_arithmetic_mismatch.pdf`** to a new company. R04 fails by exactly −9.00 crore; the Reconciliation
   Agent suggests "transposed digits in Inventories: 421.80 vs 412.80" but does **not** change the figure.
7. **Correct the figure** in the evidence drawer with a reason → version increments, the failure auto-resolves,
   the adjustment history shows who/when/why/before/after.
8. **Submit for review**, sign out, sign in as `reviewer@demo.local`, **approve the version**. Try approving as the
   preparer first to show the four-eyes rule.
9. **Download Excel and PDF**: Read Me with snapshot hash, statements, ratios with special-interpretation flags,
   validation results with exact residuals, adjustments, source references. Make another correction and show the
   export is now marked *stale* and the approval *invalidated*.
10. **Security moments:** upload `12_malicious_instructions.pdf` (instructions treated as data, critical exception
    blocks approval) and `14_bank_unsupported.pdf` (refused as an unsupported entity type). Sign in as
    `other@demo.local` to show the other tenant sees nothing.
