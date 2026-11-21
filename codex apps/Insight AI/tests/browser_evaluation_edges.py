"""Verify saved-run rerun semantics and a simulated worker failure in the UI."""

import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel=os.environ.get("PLAYWRIGHT_CHANNEL", "chrome"), headless=True)
    page = browser.new_page()
    expect.set_options(timeout=30000)
    page.goto("http://127.0.0.1:3000")
    page.get_by_label("Username", exact=True).fill("admin")
    page.get_by_label("Password", exact=True).fill(
        Path(".productionlens/admin-password.txt").read_text().strip()
    )
    page.get_by_role("button", name="Sign in to workspace").click()
    page.locator(".sidebar").get_by_role("button", name="Evaluations", exact=True).click()
    page.get_by_role("button", name="Core benchmark · script-regression", exact=False).first.click()
    expect(page.get_by_role("heading", name="Paired diagnosis quality")).to_be_visible()
    page.get_by_label("Candidate version").select_option("script-v1")
    page.get_by_label("Repeated trials").select_option("3")
    page.get_by_role("button", name="PL-009", exact=True).click()
    with page.expect_request(lambda r: r.method == "POST" and r.url.endswith("/api/evaluations")) as request:
        page.get_by_role("dialog").get_by_role("button", name="Rerun", exact=False).click()
    payload = request.value.post_data_json
    assert payload == {"candidate": "script-regression", "trials": 1, "case_id": "PL-009"}, payload
    expect(page.get_by_role("heading", name="Benchmark in progress")).to_be_visible()
    expect(page.get_by_role("heading", name="Benchmark in progress")).to_have_count(0, timeout=90000)
    expect(page.get_by_role("button", name="PL-009", exact=True)).to_be_visible()

    def simulate_failure(route):
        if route.request.method != "POST":
            route.continue_()
            return
        route.fulfill(
            json={
                "id": "browser-simulated-failure",
                "mode": "replay",
                "status": "failed",
                "created_at": 0,
                "config": {"candidate": "script-v1", "trials": 1},
                "report": {"error": "Simulated worker failure for browser validation"},
                "results": [],
            }
        )

    page.route("**/api/evaluations", simulate_failure)
    page.get_by_role("button", name="Run benchmark").click()
    expect(page.get_by_role("alert").filter(has_text="Benchmark failed")).to_be_visible()
    expect(page.get_by_role("heading", name="Benchmark in progress")).to_have_count(0)
    Path("docs/evidence/browser-evaluation-edges.json").write_text(
        json.dumps(
            {
                "passed": True,
                "checks": [
                    "saved candidate and one trial on rerun",
                    "actual single-case completion",
                    "simulated failure is terminal and visible",
                ],
            },
            indent=2,
        )
    )
    browser.close()
    print("PASS: evaluation rerun and failure-state browser checks")
