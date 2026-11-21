# Cost and limitations

## Cost
* **Demo mode:** no model calls, no external services. OCR runs locally (RapidOCR/ONNX Runtime) at roughly
  30–40 s per scanned page on a laptop CPU; digital PDFs and XLSX take 2–10 s per document.
* **Live mode:** model calls only where they add value: one Document Understanding call per document, Table
  Extraction only for suspicious rows, Mapping only for non-high-confidence rows (batched), Reconciliation only
  when checks fail, Analyst Pack once per export. Per-document budgets (`SPREADLENS_BUDGET_MAX_MODEL_CALLS`,
  `…_MAX_COST_USD`, `…_MAX_OCR_PAGES`) stop a run that would exceed them. Cost is estimated from tokens reported by
  eve (`usage.recorded`) and the configured per-million-token prices, and shown per run and per workspace.
* Extraction is cached by (workspace, document hash, parser version, configuration), so re-processing an unchanged
  file costs nothing.

## Known limitations (honest list)
* **Layout parser scope.** The PDF table parser expects statement tables with period columns detected from header
  dates/years and right-aligned figures. Unusual layouts (multi-level column headers, side-by-side statements,
  rotated tables, columns for notes *and* multiple scopes) may need analyst correction or will be missed.
* **Real-world accuracy is unmeasured.** All benchmarks use synthetic, generated documents. Thresholds guard
  regressions only.
* **OCR.** The bundled RapidOCR model is Chinese+English and does not emit spaces; spacing is restored with a
  dictionary of financial vocabulary. Unusual words stay merged (the characters are never changed). Low-confidence
  cells are flagged; a targeted re-OCR at higher DPI is attempted once.
* **Live mode verified only up to the model call.** The eve agents build, start, authenticate and stream; without an
  AI Gateway key in this environment a turn ends without a result and the engine reports the failure. Live answer
  quality has not been evaluated.
* **R09** treats cash-definition differences as "requires review" unless a reconciling item is recorded; it does not
  parse cash notes for overdraft amounts automatically.
* **No currency conversion**; cross-currency comparison is shown as unavailable by design.
* **Quarterly / YTD** figures are stored but excluded from annual metrics; there are no interim-period rules.
* **Mapping** covers the 63-item taxonomy; industry-specific line items fall back to "unmapped" (visible).
* **Specialised financial institutions** (banks, insurers, NBFCs) are detected and refused, not spread.
* **Auth** is local username/password with opaque tokens; SSO/OIDC is not implemented. Retention purge is a manual
  admin action, not a scheduled job.
* **Worker timeouts** rely on leases; a stage stuck in native code is not forcibly killed.
* Compliance: the controls here (authorization, tenant isolation, audit logs, redaction) do **not** amount to any
  regulatory certification.
