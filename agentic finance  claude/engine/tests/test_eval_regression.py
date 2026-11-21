"""Numerical regression thresholds over the synthetic fixtures (runs the evaluation in a subprocess,
against its own database). Synthetic benchmark results are not real-world accuracy."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.integration
def test_eval_thresholds():
    r = subprocess.run([sys.executable, "-m", "eval.run_eval"], cwd=ROOT, capture_output=True, text=True, timeout=900)
    report = json.loads((ROOT / "eval" / "last_report.json").read_text())
    assert report["threshold_failures"] == [], report["threshold_failures"]
    assert r.returncode == 0
    assert report["metrics"]["unsupported_value_invention_rate"] == 0.0
