#!/usr/bin/env python3
"""Synchronous hero-path investigation for Definition of Done checks."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from langgraph.types import Command  # noqa: E402

from app.database.models import Incident  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.graph.main import get_graph  # noqa: E402
from app.graph.runtime import GraphRuntime, bind_runtime, reset_runtime  # noqa: E402
from app.graph.state import initial_state  # noqa: E402
from app.llm.router import LLMRouter  # noqa: E402
from app.tools import ToolHub  # noqa: E402
from app.config import get_settings  # noqa: E402


def main():
    db = SessionLocal()
    inc = (
        db.query(Incident)
        .filter(Incident.scenario_id == "schema_drift")
        .order_by(Incident.detected_at.desc())
        .first()
    )
    if not inc:
        print("NO_HERO_INCIDENT")
        sys.exit(1)
    print("incident", inc.id, inc.error_message)
    state = initial_state(inc.id, inc.pipeline_id, error_message=inc.error_message, run_id=inc.run_id, scenario_id=inc.scenario_id)
    rt = GraphRuntime(inc.id, "gr_hero", LLMRouter(inc.id), ToolHub(inc.id), get_settings())
    token = bind_runtime(rt)
    graph = get_graph()
    config = {"configurable": {"thread_id": inc.id + "-hero"}}
    try:
        for ev in graph.stream(state, config, stream_mode="updates"):
            keys = list(ev.keys()) if isinstance(ev, dict) else [str(ev)]
            print("update", keys)
        snap = graph.get_state(config)
        interrupts = list(getattr(snap, "interrupts", None) or [])
        print("values_keys", list((snap.values or {}).keys())[:20])
        print("failure_class", (snap.values or {}).get("failure_class"))
        print("hypotheses", json.dumps((snap.values or {}).get("hypotheses"), indent=2)[:1500])
        print("root_cause", (snap.values or {}).get("root_cause"))
        print("risk", (snap.values or {}).get("risk_level"), (snap.values or {}).get("policy_action"))
        print("interrupts", interrupts)
        if interrupts:
            print("RESUMING approve")
            for ev in graph.stream(Command(resume={"decision": "approve"}), config, stream_mode="updates"):
                keys = list(ev.keys()) if isinstance(ev, dict) else [str(ev)]
                print("resume_update", keys)
            snap = graph.get_state(config)
            print("final_status", (snap.values or {}).get("final_status"))
            print("report", ((snap.values or {}).get("report") or {}).get("markdown", "")[:800])
    finally:
        reset_runtime(token)
        db.close()


if __name__ == "__main__":
    main()
