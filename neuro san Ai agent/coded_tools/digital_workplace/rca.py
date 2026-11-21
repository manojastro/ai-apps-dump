"""RCA coded tools (M10): thin LLM-facing wrappers over orchestration/rca.py.

One logic core for both paths — no duplicated scoring/trigger logic.
(SearchRunbooks/SearchPastIncidents keep their M7 store-backed behavior.)
"""

from __future__ import annotations

from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool
from orchestration.rca import (causal_graph, confidence_band, correlate,
                               propose_candidates, score_candidate)


class CorrelateEvidence(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        evidence = [e for e in args.get("evidence", []) if isinstance(e, dict)]
        return correlate(evidence)


class GenerateHypotheses(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        evidence = [e for e in args.get("evidence", []) if isinstance(e, dict)]
        candidates = propose_candidates(evidence)
        if not candidates:
            return {"hypotheses": [], "verdict": "INSUFFICIENT EVIDENCE"}
        return {"hypotheses": [
            {"id": f"HYPOTHESIS {i + 1}", "title": h["title"],
             "supporting": h["supporting"], "refuting": [], "status": "UNJUDGED"}
            for i, h in enumerate(candidates)]}


class ScoreHypothesis(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        return score_candidate(list(args.get("supporting", [])),
                               list(args.get("refuting", [])))


class SearchRunbooks(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        from pathlib import Path
        query = str(args.get("query", "")).lower()
        root = Path("knowledge") / "Runbooks"
        hits = []
        if root.is_dir():
            for doc in sorted(root.glob("*.md")):
                text = doc.read_text(encoding="utf-8", errors="replace")
                if not query or query in text.lower() or query in doc.stem.lower():
                    hits.append({"doc_id": doc.stem, "path": str(doc)})
        return {"runbooks": hits, "note": "seeded in M11" if not hits else ""}


class SearchPastIncidents(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        from common.config import load_settings
        from database.bootstrap import get_connection, init_db
        signature = str(args.get("signature", ""))
        db_path = load_settings(env_file=".env").db_path
        init_db(db_path)
        conn = get_connection(db_path)
        try:
            rows = conn.execute(
                "SELECT incident_id, case_id, short_description, state FROM incidents "
                "WHERE short_description LIKE ? LIMIT 10", (f"%{signature}%",)).fetchall()
            return {"matches": [dict(r) for r in rows]}
        finally:
            conn.close()


class CheckConfidenceThreshold(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        try:
            confidence = float(args.get("confidence", 0))
        except (TypeError, ValueError):
            confidence = 0.0
        return confidence_band(confidence)


class BuildCausalGraph(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        evidence = [e for e in args.get("evidence", []) if isinstance(e, dict)]
        return causal_graph(evidence, str(args.get("root_cause", "")))
