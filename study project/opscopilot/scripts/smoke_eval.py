"""Smoke eval: hit_rate@5, refusal accuracy, citation validity, p95 latency.

Offline: imports retrieval + answer code directly (no server, no LLM, cost 0).
Writes reports/smoke_<YYYYMMDD>.json and prints a one-line summary.

Usage: uv run python scripts/smoke_eval.py [--questions data/smoke_questions.jsonl]
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import date
from pathlib import Path

from opscopilot.answer import compose_answer
from opscopilot.chunk import chunk_corpus
from opscopilot.citations import validate_citations
from opscopilot.corpus import load_corpus
from opscopilot.retrieval import hybrid_search
from opscopilot.settings import get_settings


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = (len(ordered) - 1) * (pct / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(ordered) - 1)
    frac = k - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", default="data/smoke_questions.jsonl")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    settings = get_settings()
    docs = load_corpus(settings.corpus_dir)
    chunks = chunk_corpus(docs)
    if not chunks:
        raise SystemExit(f"No chunks loaded from {settings.corpus_dir}. Run generate_corpus first.")

    qpath = Path(args.questions)
    questions = [json.loads(line) for line in qpath.read_text(encoding="utf-8").splitlines() if line.strip()]

    latencies: list[float] = []
    hits = 0
    retrievable = 0
    refusal_correct = 0
    cite_ok = 0
    cite_total = 0
    details: list[dict[str, object]] = []

    for q in questions:
        qid = str(q["id"])
        question = str(q["question"])
        expected: list[str] = list(q.get("expected_docs") or [])
        qtype = str(q.get("type", "answerable"))
        service = q.get("service")
        svc = str(service) if service else None

        t0 = time.perf_counter()
        found, _debug = hybrid_search(
            question, chunks, top_k=args.top_k, rrf_k=settings.rrf_k,
            dim=settings.embedding_dim, service=svc,
        )
        answer, _cites, _conf, refused = compose_answer(
            question, found,
            refuse_threshold=settings.refuse_threshold,
            rerank_enabled=settings.rerank_enabled,
        )
        dt_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(dt_ms)

        retrieved_ids = [h.doc_id for h in found]
        retrieved_set = set(retrieved_ids)

        # hit@5: any expected doc in top-5 (unanswerable excluded)
        is_hit = False
        if expected:
            retrievable += 1
            is_hit = any(e in retrieved_set for e in expected)
            hits += int(is_hit)

        # refusal correctness
        should_refuse = qtype == "unanswerable"
        refusal_ok = (refused == should_refuse)
        refusal_correct += int(refusal_ok)

        # citation validity (only for non-refused answers)
        cite_valid: bool | None = None
        if not refused:
            cite_total += 1
            check = validate_citations(answer, retrieved_set)
            cite_valid = check.is_valid and ("§" in answer)
            cite_ok += int(bool(cite_valid))

        details.append({
            "id": qid, "type": qtype, "expected": expected,
            "retrieved": retrieved_ids, "hit@5": is_hit if expected else None,
            "refused": refused, "refusal_ok": refusal_ok,
            "citation_valid": cite_valid,
            "latency_ms": round(dt_ms, 2),
        })

    n = len(questions)
    report = {
        "date": date.today().isoformat(),
        "n_questions": n,
        "n_retrievable": retrievable,
        "hit_rate@5": round(hits / retrievable, 3) if retrievable else 0.0,
        "hits": hits,
        "refusal_accuracy": round(refusal_correct / n, 3) if n else 0.0,
        "refusal_correct": refusal_correct,
        "citation_validity": round(cite_ok / cite_total, 3) if cite_total else 1.0,
        "citations_ok": cite_ok,
        "citations_total": cite_total,
        "p50_ms": round(percentile(latencies, 50), 2),
        "p95_ms": round(percentile(latencies, 95), 2),
        "cost_usd_per_question": 0.0,
        "mode": "hybrid-tfidf+hashvec-rrf+mock-rerank",
        "refuse_threshold": settings.refuse_threshold,
        "details": details,
    }
    out_dir = Path("reports")
    out_dir.mkdir(exist_ok=True)
    stamp = date.today().strftime("%Y%m%d")
    out = out_dir / f"smoke_{stamp}.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"hit_rate@5={report['hit_rate@5']} ({hits}/{retrievable}) "
        f"refusal_acc={report['refusal_accuracy']} cite={report['citation_validity']} "
        f"p50={report['p50_ms']}ms p95={report['p95_ms']}ms -> {out}"
    )


if __name__ == "__main__":
    main()
