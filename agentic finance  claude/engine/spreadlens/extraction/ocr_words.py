"""Restore word boundaries in OCR text whose recognition model drops spaces.

Only spacing is changed; characters are never altered. The source label keeps the OCR characters
exactly, and the row carries an `ocr_spaces_restored` flag.
"""

from __future__ import annotations

import re
from functools import lru_cache

from spreadlens.taxonomy.loader import load_taxonomy

COMMON = """
a an and as at by for from in into of on or the to with without other others total net gross less add
year years ended ending period periods month months quarter half nine six three twelve march april june
september december january february may july august october november ended as at on beginning end
standalone consolidated balance sheet statement statements profit loss cash flow flows financial notes note
particulars amounts amount all unless otherwise stated inr rupees crores crore lakhs lakh millions million
thousands thousand rs usd assets asset liabilities liability equity share shares capital reserves surplus
current non noncurrent property plant equipment capital work progress intangible intangibles goodwill
investments investment deferred tax taxes income expense expenses revenue revenues operations operating
sales cost costs materials consumed employee employees benefits benefit finance depreciation amortisation
amortization impairment exceptional items item before after comprehensive earnings per basic diluted face
value each trade receivables receivable payables payable inventories inventory borrowings borrowing lease
leases provisions provision bank balances balance equivalents interest dividend dividends paid received
proceeds repayment purchase purchases sale disposal increase decrease decreases increases changes change
generated used provided activities investing financing working adjustments adjustment effect exchange rate
differences translation opening closing limited private company group subsidiaries subsidiary associates
joint ventures accompanying integral part form forms these this report annual cover page continued
restated original published previous figures regrouped reclassified wherever necessary loans advances
security deposits government grants contract contracts customers customer suppliers supplier related
parties party payments payment refund refunds short long term terms secured unsecured maturities maturity
repayable demand within more than months deposits original maturity excluded comprise comprises comprising
including includes include gain gains losses fair through attributable owners parent controlling minority
interests other's polymer polymers products product services service discounts discount related
""".split()


@lru_cache(maxsize=1)
def vocabulary() -> frozenset[str]:
    words = set(COMMON)
    for item in load_taxonomy().items:
        for syn in item.synonyms:
            words.update(syn.split())
    words.update({"a", "i"})
    return frozenset(w.lower() for w in words if w.isalpha())


def _segment_alpha(run: str) -> list[tuple[int, int]]:
    """Min-cost segmentation of an alphabetic run into known words (unknown chunks allowed)."""
    vocab = vocabulary()
    s = run.lower()
    n = len(s)
    inf = float("inf")
    best = [inf] * (n + 1)
    back = [0] * (n + 1)
    best[0] = 0.0
    for i in range(1, n + 1):
        for j in range(max(0, i - 24), i):
            w = s[j:i]
            if w in vocab and (len(w) > 1 or w in ("a",)):
                c = 1.0
            else:
                c = 3.0 + 0.6 * len(w)
            if best[j] + c < best[i]:
                best[i] = best[j] + c
                back[i] = j
    spans = []
    i = n
    while i > 0:
        spans.append((back[i], i))
        i = back[i]
    spans.reverse()
    # merge consecutive unknown chunks back together (keeps proper nouns intact)
    merged: list[tuple[int, int]] = []
    for a, b in spans:
        known = s[a:b] in vocab
        if merged and not known and s[merged[-1][0]:merged[-1][1]] not in vocab:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return merged


_BOUNDARY = re.compile(r"(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])|(?<=[,;:])(?=[A-Za-z(])|(?<=[)])(?=[A-Za-z])|(?<=[a-z])(?=\()")


def split_spaceless(text: str) -> list[tuple[int, int]]:
    """Return (start, end) character spans of words in `text` (spacing only; characters unchanged)."""
    cuts = {m.start() for m in _BOUNDARY.finditer(text)}
    for run in re.finditer(r"[A-Za-z]+", text):
        if len(run.group(0)) <= 3:
            continue
        for a, _b in _segment_alpha(run.group(0))[1:]:
            cuts.add(run.start() + a)
    cuts.discard(0)
    points = [0, *sorted(c for c in cuts if 0 < c < len(text)), len(text)]
    return [(a, b) for a, b in zip(points, points[1:]) if text[a:b].strip()]
