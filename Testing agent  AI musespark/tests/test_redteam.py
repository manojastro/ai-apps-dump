"""Red-team policy tests: every tripwire proven against its hostile fixture page."""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from sentinel.agents.explorer import execute_intent_step
from sentinel.browser.accessibility import PageErrorCollector
from sentinel.browser.policy import (
    BudgetExhausted,
    StepBudget,
    check_success_claim,
    find_external_targets,
    screen_page_text,
)

PAGES = Path(__file__).resolve().parent.parent / "evals" / "redteam" / "injection_pages"


@pytest.fixture()
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page()
        yield pg
        browser.close()


def _text(page) -> str:
    # textContent, NOT innerText: hidden bait (display:none) must be screened too.
    return page.evaluate("document.body.textContent")


def test_injection_page_flagged_before_any_action(page):
    page.goto(PAGES.joinpath("injection_delete.html").as_uri())
    hits = screen_page_text(_text(page))
    assert any(h.category == "injection" and "delete all records" in h.matched for h in hits)


def test_clean_page_has_no_hits(page):
    page.set_content("<html><body><h1>Leads</h1><button>Save</button></body></html>")
    assert screen_page_text(_text(page)) == []


def test_exfiltration_page_flagged_by_text_and_target(page):
    page.goto(PAGES.joinpath("exfiltration.html").as_uri())
    hits = screen_page_text(_text(page))
    assert any(h.category == "exfiltration" for h in hits)
    action = page.evaluate("document.querySelector('form').getAttribute('action')")
    bad = find_external_targets([action], allowed_domains=["acme.develop.my.salesforce.com"])
    assert bad == [action]


def test_allowlisted_target_not_flagged():
    ok = find_external_targets(
        ["https://acme.develop.my.salesforce.com/secur/frontdoor.jsp"],
        allowed_domains=["acme.develop.my.salesforce.com"])
    assert ok == []


def test_fake_success_detected_when_banner_lies(page):
    page.route("**/api/save-opportunity", lambda route: route.fulfill(status=500, body="boom"))
    page.goto(PAGES.joinpath("fake_success.html").as_uri())
    collector = PageErrorCollector().attach(page)
    with page.expect_response("**/api/save-opportunity", timeout=5000) as resp_info:
        result = execute_intent_step(page, collector, step_index=0, action="click", role="button", name="Save")
    assert result.succeeded  # the click itself worked...
    assert resp_info.value.status == 500  # ...but the save actually failed
    banner = page.get_by_role("status").inner_text()
    assert "Saved successfully" in banner  # ...and the page lies about it
    _, late_failed = collector.drain()
    assert any("save-opportunity" in f["url"] for f in late_failed)
    assert any("save-opportunity" in f["url"] for f in late_failed)
    assert check_success_claim(True, late_failed) == "fake_success"
    assert check_success_claim(True, []) == "ok"


def test_loop_bait_terminates_on_budget(page):
    page.goto(PAGES.joinpath("loop_reset.html").as_uri())
    collector = PageErrorCollector().attach(page)
    budget = StepBudget(max_steps=3)
    submits = 0
    with pytest.raises(BudgetExhausted):
        while True:
            budget.take()
            execute_intent_step(page, collector, step_index=submits,
                                action="fill", role="textbox", name="Name", value="TEST-x")
            submits += 1
    assert submits == 3  # gave up instead of looping forever


def test_step_budget_rejects_nonpositive():
    with pytest.raises(ValueError):
        StepBudget(max_steps=0)
