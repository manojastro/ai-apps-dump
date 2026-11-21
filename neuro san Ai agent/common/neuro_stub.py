"""Test-only neuro_san stub loader (M7/M28). Mirrors the REAL interface verified in
docs/FRAMEWORK_FACTS.md section 4 (neuro_san/interfaces/coded_tool.py:22-99).

Used ONLY when the real neuro-san package is absent (this environment). Under
``ns run`` the real package resolves and this is a no-op. If signatures drift,
``ns check-config`` (M28) is the arbiter - never this file.
"""

from __future__ import annotations

import sys
import types
from typing import Any


def ensure_stub() -> None:
    try:
        import neuro_san.interfaces.coded_tool  # noqa: F401
        return  # real package present - do nothing
    except ImportError:
        pass

    class CodedTool:
        def invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
            pass

        async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
            raise NotImplementedError

    interfaces = types.ModuleType("neuro_san.interfaces")
    coded_mod = types.ModuleType("neuro_san.interfaces.coded_tool")
    coded_mod.CodedTool = CodedTool
    pkg = types.ModuleType("neuro_san")
    pkg.__path__ = []  # type: ignore[attr-defined]
    interfaces.__path__ = []  # type: ignore[attr-defined]
    sys.modules["neuro_san"] = pkg
    sys.modules["neuro_san.interfaces"] = interfaces
    sys.modules["neuro_san.interfaces.coded_tool"] = coded_mod
