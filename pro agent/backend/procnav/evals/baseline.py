"""Fixed-selector automation baseline: hard-coded CSS selectors for the original portal layouts,
no semantic recovery, no landed-cost normalization, no policy engine. It never submits orders;
it reports which offer it *would* buy so its correctness can be scored safely."""

from __future__ import annotations

import re
import time
from decimal import Decimal
from typing import Any

from playwright.sync_api import sync_playwright

from ..suppliers.secrets import resolve

SELECTORS = {
    "alpha": {
        "url": "http://127.0.0.1:8301",
        "user": "#username",
        "password": "#password",
        "submit": "button.btn",
        "search": "#alpha-search",
        "result": "#results a",
        "price": "#unit-price",
    },
    "beta": {
        "url": "http://127.0.0.1:8302",
        "user": "input[name=username]",
        "password": "input[name=password]",
        "submit": "button.cta",
        "search": "input[name=term]",
        "result": ".grid .card h2 a",
        "price": ".row strong",
    },
    "gamma": {
        "url": "http://127.0.0.1:8303",
        "user": "#u",
        "password": "#p",
        "submit": "button.button",
        "search": "#kw",
        "result": "ol.hits a",
        "price": "table[aria-label='Commercial terms'] td",
    },
}


def _money(text: str) -> Decimal | None:
    m = re.search(r"\d[\d,]*\.\d{2}", text)
    return Decimal(m.group(0).replace(",", "")) if m else None


def run_baseline(quantity: int = 10, tenant: str = "acme", timeout_ms: int = 5000) -> dict[str, Any]:
    started = time.monotonic()
    offers: list[dict[str, Any]] = []
    errors: dict[str, str] = {}
    actions = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for key, sel in SELECTORS.items():
            ctx = browser.new_context()
            page = ctx.new_page()
            page.set_default_timeout(timeout_ms)
            try:
                cred = resolve(f"supplier/{tenant}/{key}")
                page.goto(sel["url"] + "/")
                page.fill(sel["user"], cred.username)
                page.fill(sel["password"], cred.password)
                page.click(sel["submit"])
                page.fill(sel["search"], "Northwind Pro 14")
                page.press(sel["search"], "Enter")
                page.wait_for_load_state()
                links = page.locator(sel["result"])
                texts = links.all_inner_texts()
                pick = next((i for i, t in enumerate(texts) if "16" in t), 0)  # naive spec matching
                links.nth(pick).click()
                page.wait_for_load_state()
                price = _money(page.locator(sel["price"]).first.inner_text())
                sku = re.search(r"/(?:item|p|products)/([A-Z0-9-]+)", page.url)
                actions += 6
                offers.append(
                    {
                        "supplier": key,
                        "sku": sku.group(1) if sku else None,
                        "unit_price": str(price),
                        "naive_total": str(price * quantity) if price else None,
                    }
                )
            except Exception as err:  # noqa: BLE001 - the baseline has no recovery by design
                errors[key] = type(err).__name__
            finally:
                ctx.close()
        browser.close()
    priced = [o for o in offers if o["naive_total"]]
    choice = min(priced, key=lambda o: Decimal(o["naive_total"])) if priced else None
    return {
        "would_buy": choice,
        "offers": offers,
        "errors": errors,
        "actions": actions,
        "active_ms": int((time.monotonic() - started) * 1000),
    }
