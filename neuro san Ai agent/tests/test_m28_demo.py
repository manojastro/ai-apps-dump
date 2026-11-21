"""M28 tests: demo determinism (same seed, twice) + reset behavior."""

from __future__ import annotations

import tests.conftest  # noqa: F401
from demo.demo import (knowledge_security, laptop_teams_memory, learning_loop,
                       vpn_stale_token)
from demo.reset_demo import reset


def test_laptop_deterministic(tmp_path) -> None:
    first = laptop_teams_memory(str(tmp_path / "a.db"), 42)
    second = laptop_teams_memory(str(tmp_path / "b.db"), 42)
    assert first["verdict"] == second["verdict"] == "PROCEED"
    assert first["action"] == second["action"] == "SCR-018"
    assert first["healed"] == second["healed"] == 26
    assert first["prevented"] == second["prevented"] == 26


def test_vpn_learning_knowledge(tmp_path) -> None:
    vpn = vpn_stale_token(str(tmp_path / "v.db"), 42)
    assert vpn["action"] == "SCR-VPN-RECONNECT" and "manager" in vpn["human"]
    learned = learning_loop(str(tmp_path / "l.db"), 42)
    assert learned["autonomy"] == "L3" and learned["human_intervention"] == "NONE"
    known = knowledge_security(str(tmp_path / "k.db"), 42)
    assert known["answer_doc"] == "internet_reimbursement" and known["payroll_denied"]


def test_reset_clears_only_runtime(tmp_path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    (data / "autopilot.db").write_text("x")
    (data / "other.db-wal").write_text("x")
    (data / "keep.txt").write_text("x")
    removed = reset(str(data))
    assert len(removed) == 2
    assert (data / "keep.txt").exists()
    assert reset(str(data / "missing")) == []
