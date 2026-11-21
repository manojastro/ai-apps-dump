"""Browser smoke tests against the running console and API. No stubbed network responses."""
import argparse
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:5173")
    args = parser.parse_args()
    screenshots = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1100}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(args.url)
        page.wait_for_load_state("networkidle")
        expect(page.get_by_role("heading", name="Pipeline incidents")).to_be_visible()
        page.get_by_role("button", name="Inject incident", exact=True).click()
        page.get_by_role("button", name="Start investigation", exact=True).click()
        expect(page.get_by_text("Verified artifact ready", exact=True)).to_be_visible(timeout=60000)
        expect(page.get_by_text("REJECTED", exact=True)).to_be_visible()
        expect(page.get_by_text("PASSED", exact=True)).to_be_visible()
        page.get_by_role("button", name="Schema: completed").click()
        expect(page.locator(".node-inspector")).to_be_visible()
        page.get_by_role("button", name="Close node details").click()
        page.evaluate("window.scrollTo(0, 0)")
        page.screenshot(path=str(screenshots / "investigation.png"), full_page=True)
        page.get_by_role("tab", name="Evidence").click()
        expect(page.get_by_text("EV-SCHEMA-001", exact=True)).to_be_visible()
        page.get_by_role("tab", name="Artifact", exact=True).click()
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Download diff").click()
        assert download_info.value.suggested_filename == "recovery-plan.diff"
        expect(page.locator(".diff-view")).to_contain_text("map_customer_id")
        page.get_by_role("tab", name="Audit", exact=True).click()
        expect(page.get_by_text("read_schema", exact=True)).to_be_visible()

        page.get_by_role("button", name="Inject incident", exact=True).click()
        page.get_by_label("Failure scenario").select_option("dependency_failure")
        page.get_by_role("button", name="Start investigation", exact=True).click()
        expect(page.get_by_role("heading", name="Human approval required")).to_be_visible(timeout=60000)
        page.get_by_label("Reviewer", exact=True).fill("Browser smoke reviewer")
        page.get_by_label("Decision note").fill("Reviewed bounded retries and all deterministic checks")
        page.evaluate("window.scrollTo(0, 0)")
        page.screenshot(path=str(screenshots / "approval.png"), full_page=True)
        page.get_by_role("button", name="Approve artifact", exact=True).click()
        expect(page.get_by_text("Verified artifact ready", exact=True)).to_be_visible(timeout=60000)
        expect(page.get_by_text("APPROVED", exact=True)).to_be_visible()
        page.set_viewport_size({"width": 390, "height": 844})
        page.evaluate("window.scrollTo(0, 0)")
        page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        assert not errors, errors
        browser.close()
    print("PASS: rejection/revision, graph inspection, evidence, audit, artifact download, approval, mobile")


if __name__ == "__main__":
    main()
