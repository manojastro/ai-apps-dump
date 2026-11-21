"""Pytest bootstrap: neuro_san stub when the real package is absent (see common.neuro_stub)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.neuro_stub import ensure_stub

ensure_stub()
