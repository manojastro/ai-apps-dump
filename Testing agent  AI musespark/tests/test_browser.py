"""Browser-helper tests on local fixture pages (headless Chromium, no org needed).

Proves: a11y snapshot as primary observation, intent-only location
(role+name, zero selectors), condition waits (no sleep), per-step error
capture, failure-only screenshots, blocked-action refusal.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.browser

from playwright.sync_api import sync_playwright

from sentinel.agents.explorer import execute_intent_step
from sentinel.browser.accessibility import (
    PageErrorCollector,
    snapshot_accessibility,
)

FORM_HTML = """
<html><body>
  <h1>New Lead</h1>
  <label>Last Name<input type="text" aria-label="Last Name"></label>
  <button>Save</button>
  <script>console.error("LC: widget failed to load");</script>
</body></html>
"""

DELAYED_HTML = """
<html><body>
  <div id="app">Loading…</div>
  <script>setTimeout(() => {
    const b = document.createElement('button'); b.textContent = 'Confirm';
    document.body.appendChild(b);
  }, 800);</script>
</body></html>
"""


@pytest.fixture()
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page()
        yield pg
        browser.close()


def test_snapshot_contains_intent_not_markup(page):
    page.set_content(FORM_HTML)
    snap = snapshot_accessibility(page)
    assert 'button \'Save\'' in snap or "button 'Save'" in snap
    assert "Last Name" in snap
    assert "<button>" not in snap  # observation is intent, not HTML


def test_click_by_intent_succeeds_with_no_selectors(page):
    page.set_content(FORM_HTML)
    page.evaluate("document.querySelector('button').onclick = () => document.title = 'saved'")
    collector = PageErrorCollector().attach(page)
    result = execute_intent_step(page, collector, step_index=0, action="click", role="button", name="Save")
    assert result.succeeded, result.error
    assert result.screenshot_path is None  # no screenshot on success
    assert page.title() == "saved"


def test_fill_by_intent(page):
    page.set_content(FORM_HTML)
    collector = PageErrorCollector().attach(page)
    result = execute_intent_step(
        page, collector, step_index=0, action="fill", role="textbox", name="Last Name", value="TEST-Asha"
    )
    assert result.succeeded, result.error
    assert page.get_by_role("textbox", name="Last Name").input_value() == "TEST-Asha"


def test_delayed_render_waits_on_condition_not_sleep(page):
    """Button appears after 800ms; condition-wait must catch it without sleep()."""
    page.set_content(DELAYED_HTML)
    collector = PageErrorCollector().attach(page)
    result = execute_intent_step(page, collector, step_index=0, action="click", role="button", name="Confirm")
    assert result.succeeded, result.error


def test_console_errors_captured_on_passing_step(page):
    collector = PageErrorCollector().attach(page)  # attach BEFORE load: errors fire at parse time
    page.set_content(FORM_HTML)
    result = execute_intent_step(page, collector, step_index=0, action="click", role="button", name="Save")
    assert result.succeeded
    assert any("widget failed to load" in e for e in result.console_errors)


def test_failed_network_call_captured(page):
    # Deterministic offline 500 via routing — no real network involved.
    page.route("**/api/save-lead", lambda route: route.fulfill(status=500, body="boom"))
    collector = PageErrorCollector().attach(page)
    page.set_content("<html><body><button>Go</button></body></html>")
    page.evaluate("fetch('https://example.com/api/save-lead').catch(() => {})")
    page.wait_for_timeout(500)
    errors, failed = collector.drain()
    assert any("api/save-lead" in f["url"] and f["status"] == 500 for f in failed)


def test_aborted_request_captured_without_response(page):
    page.route("**/api/flaky", lambda route: route.abort())
    collector = PageErrorCollector().attach(page)
    page.set_content("<html><body><button>Go</button></body></html>")
    page.evaluate("fetch('https://example.com/api/flaky').catch(() => {})")
    page.wait_for_timeout(500)
    errors, failed = collector.drain()
    assert any("api/flaky" in f["url"] for f in failed)


def test_missing_element_fails_with_screenshot(page, tmp_path):
    page.set_content(FORM_HTML)
    collector = PageErrorCollector().attach(page)
    result = execute_intent_step(
        page, collector, step_index=3, action="click", role="button", name="Nope",
        timeout_ms=1000, screenshot_dir=tmp_path,
    )
    assert not result.succeeded and result.error
    assert result.screenshot_path and result.screenshot_path.endswith("step_3.png")


def test_blocked_action_refused_without_touching_browser(page):
    page.set_content(FORM_HTML)
    collector = PageErrorCollector().attach(page)
    result = execute_intent_step(
        page, collector, step_index=0, action="click", role="button", name="mass delete all records"
    )
    assert not result.succeeded and "Refused blocked action" in result.error
