# RRF worked example (by hand)

Reciprocal Rank Fusion fuses ranked **lists by rank, not by score**:

> `RRF(d) = Σ over lists 1 / (k + rank(d))`, ranks start at 1. We use `k = 60`.

## Setup

Question: `"VPN fails with ERR_VPN_809"`.

- Keyword ranking (TF-IDF-ish): `["C2", "C1", "C3"]`
  (`C2` = the `KB0002` Symptoms chunk that literally contains `ERR_VPN_809`).
- Vector ranking (mock hash-embedding cosine): `["C1", "C2", "C4"]`.

## Hand computation (`k = 60`)

| chunk | keyword rank | vector rank | RRF |
|---|---|---|---|
| C2 | 1 → 1/61 ≈ 0.016393 | 2 → 1/62 ≈ 0.016129 | 0.016393 + 0.016129 = **0.032523** |
| C1 | 2 → 1/62 ≈ 0.016129 | 1 → 1/61 ≈ 0.016393 | 0.016129 + 0.016393 = **0.032523** |
| C3 | 3 → 1/63 ≈ 0.015873 | — | **0.015873** |
| C4 | — | 3 → 1/63 ≈ 0.015873 | **0.015873** |

Fused order: `C2, C1` tie at `0.032523` → tie-break by chunk id ascending
(`C1` before `C2`), then `C3, C4` tie at `0.015873` → `C3` before `C4`.

Result: `[C1, C2, C3, C4]` with scores `[0.032523, 0.032523, 0.015873, 0.015873]`.

## What this shows

1. **In both lists beats in one:** `C1`/`C2` (≈0.0325) score ~2× higher than
   `C3`/`C4` (≈0.0159), which appear in only one list.
2. **Ranks, not scores:** the raw TF-IDF score (e.g. 12.4) and the cosine
   (e.g. 0.31) live on different scales and are never mixed — only positions count.
3. **Exact codes:** keyword search puts the `ERR_VPN_809` chunk at rank 1 even
   when the vector mock ranks a paraphrase first; RRF keeps both near the top
   instead of letting one signal dominate.

Verify against code: `rrf_fuse([["C2","C1","C3"],["C1","C2","C4"]], k=60)`
returns exactly the table above (see `tests/test_rrf.py`).
