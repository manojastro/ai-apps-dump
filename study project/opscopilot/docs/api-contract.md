# API contract — stable for P2 / P3 / P4

Base URL (local): `http://localhost:8000`. All bodies are JSON. No auth in P1
(spend protection arrives with the deployed milestone).

## GET /health

Response `200`:

```json
{ "status": "ok", "docs": 38, "chunks": 190, "corpus_loaded": true }
```

- `status` is `"ok"` when chunks are loaded, `"empty"` otherwise.

## POST /v1/search — retrieval only (no answer)

Used by evals (P2) and the MCP server (P3). Request:

```json
{ "question": "VPN fails with ERR_VPN_809", "service": "vpn", "top_k": 5 }
```

- `question` (required, non-empty).
- `service` (optional): case-insensitive exact filter (`outlook`, `vpn`, `wifi`,
  `printer`, `iam`, `laptop`, `pos`, `sharepoint`).
- `top_k` (optional, 1–20, default 5 from `OPS_TOP_K_DEFAULT`).

Response `200`:

```json
{
  "hits": [
    {
      "chunk_id": "KB0002#symptoms:1", "doc_id": "KB0002",
      "title": "VPN client fails with error ERR_VPN_809 on home broadband",
      "section": "Symptoms", "service": "vpn", "status": "active",
      "score": 0.0328, "rank": 1, "snippet": "VPN client fails …"
    }
  ],
  "retrieval_debug": {
    "keyword_ranking": ["KB0002#symptoms:1"],
    "vector_ranking": ["KB0002#symptoms:1"],
    "fused_ranking": ["KB0002#symptoms:1"]
  }
}
```

Rankings list `chunk_id`s, best first. `fused_ranking` is the RRF order.

## POST /v1/ask — grounded answer with citations, or refusal

Request: same shape as `/v1/search`.

Response `200`:

```json
{
  "answer": "Based on [KB0002 §Symptoms]: … See [KB0002 §Symptoms] for the full steps.",
  "citations": [{ "doc_id": "KB0002", "section": "Symptoms" }],
  "confidence": "HIGH",
  "refused": false,
  "retrieval_debug": { "keyword_ranking": [], "vector_ranking": [], "fused_ranking": [] }
}
```

- `confidence`: `HIGH` / `MEDIUM` / `LOW`.
- `refused: true` answers look like:
  `"No matching article found in the Acme Retail Ltd knowledge base for: '…'. …"`,
  with `citations: []` and `confidence: "LOW"`.
- Citation markers in `answer` always use the form `[DOCID §Section]`
  (e.g. `[KB0001 §Workaround]`, `[SOP-VPN-01 §Steps]`). Every cited `doc_id`
  is guaranteed to be in the retrieved set (deterministic validator).
- Conflicting / near-duplicate pairs: when the top two hits are different
  active docs with near-equal fused scores, the answer cites **both** with a
  "closely related guidance" note and `MEDIUM` confidence.
- Retired docs are deprioritised: an active hit is always preferred; a
  retired-only answer is flagged in the text with `MEDIUM` confidence.

## GET /v1/sources/{doc_id}

Response `200` (example `KB0002`):

```json
{
  "doc_id": "KB0002", "doc_type": "kedb", "title": "…",
  "service": "vpn", "status": "active", "updated_at": "2025-06-20",
  "content": "# …\n\n## Symptoms\n\n…"
}
```

Unknown ids return `404` (`{"detail": "Unknown doc_id …"}`).

## GET /

Tiny HTML + vanilla JS demo page (question box, service filter, Ask / Search
buttons, clickable citations, retrieval-debug toggle).

## Errors

- Empty question → `422` (Pydantic validation).
- Unknown `doc_id` → `404`. All other failures are plain FastAPI JSON errors.
