"""TestWriter tests: guards + the fail-on-broken / pass-on-fixed proof.

The meta-proof (test_rendered_test_fails_broken_passes_fixed) renders a
regression script and actually executes it twice as a subprocess against two
local fixture pages. That is the Phase-4 acceptance mechanism, verified
offline; the live variant points the same renderer at a Salesforce URL.
"""

from __future__ import annotations

import ast
import subprocess
import sys

import pytest

from sentinel.agents.testwriter import (
    regression_filename,
    render_regression_test,
    write_regression_test,
)
from sentinel.models import RecordedAction

BROKEN_HTML = "<html><head><title>New Lead</title></head><body><button>Save</button></body></html>"
FIXED_HTML = """<html><head><title>New Lead</title></head><body><button>Save</button>
<script>document.querySelector('button').onclick = () => { document.title = 'saved'; };</script>
</body></html>"""


def _actions() -> list[RecordedAction]:
    return [RecordedAction(kind="click", role="button", name="Save"),
            RecordedAction(kind="expect_title", value="saved")]


def test_render_is_valid_python_with_intent_locators_only():
    code = render_regression_test(test_id="TC-1", title="Save lead", bug_key="SENT-42",
                                  target_url="https://example.com", actions=_actions())
    ast.parse(code)
    assert code.isascii(), "generated code must be ASCII-only (locale-proof execution)"
    assert "get_by_role" in code and "SENT-42" in code
    for forbidden in ("query_selector", "xpath", "css="):
        assert forbidden not in code.lower()


def test_render_rejects_empty_actions():
    with pytest.raises(ValueError, match="empty"):
        render_regression_test(test_id="TC-1", title="t", bug_key="SENT-1",
                               target_url="https://example.com", actions=[])


def test_render_rejects_unsafe_test_id():
    with pytest.raises(ValueError, match="Unsafe test_id"):
        render_regression_test(test_id="../../evil", title="t", bug_key="SENT-1",
                               target_url="https://example.com", actions=_actions())


def test_render_rejects_unknown_action_kind():
    with pytest.raises(Exception, match="Unknown action kind"):
        render_regression_test(test_id="TC-1", title="t", bug_key="SENT-1",
                               target_url="https://example.com",
                               actions=[RecordedAction(kind="click", role="button", name="x"),
                                        RecordedAction.model_construct(kind="nonsense")])


def test_filename_is_safe():
    assert regression_filename("TC-LEAD-001-HAPPY-1") == "test_regression_tc_lead_001_happy_1.py"


def test_live_path_still_raises():
    with pytest.raises(NotImplementedError):
        write_regression_test()


def test_rendered_test_fails_broken_passes_fixed(tmp_path):
    """End-to-end proof of the codegen mechanism (see module docstring)."""
    broken = tmp_path / "broken.html"
    fixed = tmp_path / "fixed.html"
    broken.write_text(BROKEN_HTML, encoding="utf-8")
    fixed.write_text(FIXED_HTML, encoding="utf-8")

    results = {}
    for label, page in (("broken", broken), ("fixed", fixed)):
        code = render_regression_test(test_id="TC-1", title="Save sets title", bug_key="SENT-42",
                                      target_url=page.as_uri(), actions=_actions())
        script = tmp_path / f"gen_{label}.py"
        script.write_text(code, encoding="utf-8")
        proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=120)
        results[label] = proc

    assert results["broken"].returncode == 1, results["broken"].stdout
    assert "FAIL" in results["broken"].stdout
    assert results["fixed"].returncode == 0, results["fixed"].stdout + results["fixed"].stderr
    assert "REGRESSION PASS" in results["fixed"].stdout
