"""UI verification against a running local stack; credentials are never printed."""

import json
import os
import re
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

OUTPUT = Path("docs/evidence")
OUTPUT.mkdir(parents=True, exist_ok=True)


with sync_playwright() as p:
    expect.set_options(timeout=30000)
    browser = p.chromium.launch(channel=os.environ.get("PLAYWRIGHT_CHANNEL", "chrome"), headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1050}, device_scale_factor=1)
    page.set_default_timeout(30000)
    failures = []
    page.on("pageerror", lambda error: failures.append(str(error)))
    page.goto("http://127.0.0.1:3000", timeout=120000)
    page.wait_for_load_state("networkidle")
    page.get_by_label("Username", exact=True).fill("admin")
    page.get_by_label("Password", exact=True).fill(
        Path(".productionlens/admin-password.txt").read_text().strip()
    )
    page.get_by_role("button", name="Sign in to workspace").click()
    expect(page.get_by_role("heading", name="Production overview")).to_be_visible()
    expect(page.get_by_text("Seeded incidents and telemetry", exact=False)).to_be_visible()
    expect(page.locator(".incident-row").first).to_be_visible()
    page.screenshot(path=str(OUTPUT / "overview.png"), full_page=True)
    print("PASS: authenticated overview and desktop render", flush=True)

    def nav(name):
        page.locator(".sidebar").get_by_role("button", name=re.compile("^" + name)).click()

    def investigate(label, fixture):
        nav("Overview")
        page.get_by_role("button", name="New investigation", exact=True).click()
        dialog = page.get_by_role("dialog", name="New investigation")
        dialog.get_by_label("Incident title").fill(label)
        dialog.get_by_label("Telemetry fixture").select_option(fixture)
        dialog.get_by_role("button", name="Create & investigate").click()
        expect(page.get_by_role("heading", name=label, exact=True)).to_be_visible()
        expect(page.get_by_role("heading", name="Most supported explanation")).to_be_visible(timeout=90000)

    investigate("Browser check: rejected payment recovery", "payment_delay")
    page.get_by_role("button", name=re.compile("^Evidence ")).click()
    page.get_by_role("button", name=re.compile("^metrics Current snapshot")).click()
    expect(page.get_by_role("dialog", name="metrics evidence")).to_be_visible()
    expect(page.get_by_text("Content hash", exact=True)).to_be_visible()
    page.get_by_role("button", name="Close dialog").click()
    page.get_by_role("button", name="Review exact action").click()
    page.get_by_role("button", name="Reject action").click()
    expect(page.locator(".panel-head").get_by_text("rejected", exact=True)).to_be_visible()
    expect(page.get_by_text("Replay recovery verified", exact=True)).to_have_count(0)
    print("PASS: evidence viewer and rejection remains unexecuted", flush=True)

    investigate("Browser check: approved payment recovery", "payment_delay")
    page.screenshot(path=str(OUTPUT / "investigation.png"), full_page=True)
    page.get_by_role("button", name="Review exact action").click()
    page.get_by_role("button", name="Approve exact action").click()
    expect(page.get_by_text("Replay recovery verified", exact=True)).to_be_visible(timeout=60000)
    with page.expect_download() as download:
        page.get_by_role("button", name="Back to investigation").click()
        page.get_by_role("link", name="Export report").click()
    download.value.save_as(str(OUTPUT / "incident-report.json"))
    print("PASS: approved recovery, fresh replay measurements, report export", flush=True)

    investigate("Browser check: insufficient evidence", "missing_evidence")
    expect(
        page.get_by_text("Current independent evidence is insufficient", exact=False).first
    ).to_be_visible()
    expect(page.get_by_role("button", name="Review exact action")).to_have_count(0)
    print("PASS: honest inconclusive result", flush=True)

    nav("Integrations")
    page.get_by_role("button", name="Test connection").click()
    expect(page.locator(".error[role='alert']")).to_contain_text("PROVIDER_NOT_CONFIGURED")
    page.get_by_role("button", name="Dismiss error").click()
    print("PASS: missing provider fails visibly", flush=True)

    nav("Evaluations")
    page.get_by_role("button", name="Run benchmark").click()
    expect(page.get_by_role("heading", name="Benchmark in progress")).to_be_visible()
    expect(page.get_by_text("Candidate does not meet release policy", exact=True)).to_be_visible(
        timeout=600000
    )
    expect(page.get_by_text("Regression", exact=True).first).to_be_visible()
    page.get_by_role("button", name="PL-009", exact=True).click()
    expect(page.get_by_role("dialog", name="Failure replay · PL-009")).to_be_visible()
    expect(page.get_by_text("Candidate regression", exact=True)).to_be_visible()
    page.get_by_role("button", name="Close dialog").click()
    nav("Version comparison")
    expect(page.get_by_role("heading", name="Paired diagnosis quality")).to_be_visible()
    page.screenshot(path=str(OUTPUT / "comparison.png"), full_page=True)
    with page.expect_download() as download:
        page.get_by_role("link", name="Export results").click()
    download.value.save_as(str(OUTPUT / "evaluation-report.json"))
    print("PASS: evaluation, regression inspection, version comparison and export", flush=True)

    nav("Overview")
    page.set_viewport_size({"width": 390, "height": 844})
    expect(page.get_by_role("heading", name="Production overview")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Mobile overflow"
    page.screenshot(path=str(OUTPUT / "mobile.png"), full_page=True)
    page.get_by_role("button", name="Toggle navigation").click()
    nav("Demo lab")
    expect(page.get_by_role("heading", name="Demo lab")).to_be_visible()
    print("PASS: mobile layout and navigation", flush=True)
    assert not failures, failures
    (OUTPUT / "browser-results.json").write_text(
        json.dumps(
            {
                "passed": True,
                "checks": 8,
                "page_errors": failures,
                "timestamp": time.time(),
                "browser": browser.version,
            },
            indent=2,
        )
    )
    browser.close()
