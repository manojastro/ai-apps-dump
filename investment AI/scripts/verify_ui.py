from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOT = ROOT / "data" / "screenshots"
SHOT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto("http://127.0.0.1:3000", wait_until="networkidle")
        page.screenshot(path=str(SHOT / "landing.png"), full_page=True)
        assert "Aegis Plan India" in page.content()
        assert "SEBI-registered" in page.content()

        page.goto("http://127.0.0.1:3000/onboarding", wait_until="networkidle")
        page.get_by_role("button", name="Load demo household #2").click()
        page.wait_for_url("**/war-room", timeout=30000)
        page.wait_for_timeout(1500)
        page.screenshot(path=str(SHOT / "war-room.png"), full_page=True)

        page.wait_for_selector("text=Compare scenarios", timeout=30000)
        page.get_by_role("link", name="Compare scenarios").click()
        page.wait_for_url("**/compare", timeout=15000)
        page.wait_for_selector("text=Protect")
        page.wait_for_selector("text=Balance")
        page.wait_for_selector("text=Grow")
        page.screenshot(path=str(SHOT / "compare.png"), full_page=True)
        page.get_by_role("button", name="Select Balance").click()
        page.wait_for_url("**/plan/**", timeout=15000)
        page.wait_for_selector("text=Aegis Financial Action Plan")
        page.screenshot(path=str(SHOT / "plan.png"), full_page=True)

        page.goto("http://127.0.0.1:3000/research", wait_until="networkidle")
        page.screenshot(path=str(SHOT / "research.png"), full_page=True)
        page.goto("http://127.0.0.1:3000/sources", wait_until="networkidle")
        page.screenshot(path=str(SHOT / "sources.png"), full_page=True)
        page.goto("http://127.0.0.1:3000/holdings", wait_until="networkidle")
        page.screenshot(path=str(SHOT / "holdings.png"), full_page=True)

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.goto("http://127.0.0.1:3000", wait_until="networkidle")
        mobile.screenshot(path=str(SHOT / "landing-mobile.png"), full_page=True)
        mobile.close()

        browser.close()
        print("UI verification ok")


if __name__ == "__main__":
    main()
