"""Failure-to-test loop: persist a failure as a fixed regression case (evals/regressions/*.json).

Sources:
  failed        - proposal FAILED after retries
  wrong_action  - proposal valid but action != ground-truth expected fix
  rejected      - a human rejected the proposal with a reason
  guard         - hand-built case from the debugging exercises (bad JSON, disallowed action...)

Each case stores the conflict (type + evidence), the recorded raw model responses, and what the
replay must produce in MOCK mode (`expect_mock`). tests/test_regressions.py replays every case.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def case_id(source: str, conflict_id: str, responses: list[str | None]) -> str:
    """Same conflict + same recorded responses -> same case, whatever prompt produced them."""
    h = hashlib.sha1(json.dumps([source, conflict_id, responses]).encode()).hexdigest()[:10]
    return f"rg_{source}_{h}"


def build_case(*, source: str, conflict: dict[str, Any], prompt_version: str, recorded_responses: list[str | None],
               expect_mock: dict[str, Any], expected_action: str | None, note: str = "") -> dict:
    return {
        "id": case_id(source, conflict["id"], recorded_responses),
        "source": source,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "prompt_version": prompt_version,
        "conflict": conflict,
        "recorded_responses": recorded_responses,
        "expected_action": expected_action,
        "expect_mock": expect_mock,
        "note": note,
    }


def save_case(directory: Path, case: dict) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{case['id']}.json"
    if not path.exists():  # cases are immutable once written
        path.write_text(json.dumps(case, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return path


def load_cases(directory: Path) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(directory).glob("rg_*.json"))]
