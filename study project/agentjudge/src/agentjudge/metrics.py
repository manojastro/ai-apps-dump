"""Retrieval metrics: pure code, no LLM.

One-liners:
- hit_rate@k: did we find at least one good doc in the top k?
- recall@k: of all the docs that could fix this, how many did we find?
- MRR: how far down the list was the first good doc (1st = 1.0, 2nd = 0.5)?
- context precision: of the docs we returned, how many were useful?
- context recall: of the useful docs, how many did we return?
- refusal accuracy: on 'should refuse' rows, did we refuse (and vice versa)?
- citation validity: of the docs cited in the answer, how many did we retrieve?
"""


def _top(retrieved: list[str], k: int) -> list[str]:
    return list(retrieved[:k])


def hit_rate_at_k(retrieved: list[str], expected: list[str], k: int = 5) -> float:
    """1.0 if any expected doc is in the top-k retrieved, else 0.0."""
    if not expected:
        return 1.0 if not retrieved else 0.0
    return 1.0 if any(d in _top(retrieved, k) for d in expected) else 0.0


def recall_at_k(retrieved: list[str], expected: list[str], k: int = 5) -> float:
    """Share of expected docs found in the top-k retrieved."""
    if not expected:
        return 1.0 if not retrieved else 0.0
    top = set(_top(retrieved, k))
    return len(top & set(expected)) / len(expected)


def reciprocal_rank(retrieved: list[str], expected: list[str]) -> float:
    """1/rank of the first expected doc in the retrieved list (0.0 if absent)."""
    want = set(expected)
    for i, doc_id in enumerate(retrieved, start=1):
        if doc_id in want:
            return 1.0 / i
    return 0.0


def mrr(rankings: list[list[str]], expected_list: list[list[str]]) -> float:
    """Mean reciprocal rank over many queries."""
    if not rankings:
        return 0.0
    scores = [reciprocal_rank(r, e) for r, e in zip(rankings, expected_list)]
    return sum(scores) / len(scores)


def context_precision(retrieved: list[str], relevant: list[str]) -> float:
    """Share of retrieved IDs that are relevant."""
    if not retrieved:
        return 1.0 if not relevant else 0.0
    return len(set(retrieved) & set(relevant)) / len(retrieved)


def context_recall(retrieved: list[str], relevant: list[str]) -> float:
    """Share of relevant IDs that were retrieved."""
    if not relevant:
        return 1.0 if not retrieved else 0.0
    return len(set(retrieved) & set(relevant)) / len(relevant)


def refusal_accuracy(predicted: list[bool], expected: list[bool]) -> float:
    """Share of rows where refused==must_refuse."""
    if not expected:
        return 0.0
    return sum(p == e for p, e in zip(predicted, expected)) / len(expected)


def citation_validity(cited: list[str], retrieved: list[str]) -> float:
    """Share of cited IDs that were actually retrieved (stub: no text check)."""
    if not cited:
        return 1.0
    got = set(retrieved)
    return sum(c in got for c in cited) / len(cited)


def mean(values: list[float]) -> float:
    """Safe mean (0.0 for empty)."""
    return sum(values) / len(values) if values else 0.0
