"""Milestone 1 gate: a person can browse products and complete one simulated order.

Requires the dev PostgreSQL (docker compose -f docker-compose.dev.yml up -d).
"""

from __future__ import annotations

import re
import threading

import pytest
from fastapi.testclient import TestClient

from mockportals import db
from mockportals.control import create_control_app
from mockportals.portal import ROUTES, create_portal_app

CTRL = {"X-Control-Token": "dev-control-token"}


@pytest.fixture(autouse=True)
def fresh():
    db.reset("happy_path")
    yield


def login(client: TestClient, supplier: str, user: str = "acme-buyer", pw: str = "demo-acme-supplier"):
    resp = client.post(ROUTES[supplier]["login"], data={"username": user, "password": pw}, follow_redirects=False)
    assert resp.status_code == 303, resp.text
    return resp


def quote_ref(html: str) -> str:
    return re.search(r'name="quote_ref" value="(QR-[0-9A-F]+)"', html).group(1)


@pytest.mark.parametrize(
    "supplier,sku,total",
    [("alpha", "A-NW14-16-512", "4,91,200.00"), ("beta", "B-77821", "4,74,000.00"), ("gamma", "G-PRO14-16", "5,09,720.00")],
)
def test_manual_order_flow(supplier, sku, total):
    r = ROUTES[supplier]
    c = TestClient(create_portal_app(supplier))
    assert c.get(r["search"], follow_redirects=False).status_code == 303  # requires login
    login(c, supplier)
    res = c.get(r["search"], params={r["search_param"]: "Northwind 14"})
    assert sku in res.text
    assert "Memory" in c.get(r["product"].format(sku=sku)).text or "RAM" in c.get(r["product"].format(sku=sku)).text
    c.post(r["cart_add"], data={"sku": sku, "qty": 10})
    preview = c.get(r["checkout"]).text
    assert total in preview
    confirm = c.get(r["confirm"], params={"address": "ADDR-BLR-01"}).text
    qref = quote_ref(confirm)
    placed = c.post(r["place"], data={"po_reference": "PO-TEST-0001", "quote_ref": qref, "address_ref": "ADDR-BLR-01"})
    assert placed.status_code == 200
    order_ref = re.search(r"([ABG]O-[0-9A-F]{8})", placed.text).group(1)
    history = c.get(r["orders"]).text
    assert order_ref in history and "PO-TEST-0001" in history
    receipt = c.get(r["receipt"].format(ref=order_ref))
    assert receipt.status_code == 200 and "Quantity: 10" in receipt.text
    state = TestClient(create_control_app()).get("/_control/state", headers=CTRL).json()
    start = {"alpha": 25, "beta": 12, "gamma": 40}[supplier]
    assert state["products"][f"{supplier}:{sku}"]["stock"] == start - 10


def _prepared_beta(c: TestClient) -> str:
    r = ROUTES["beta"]
    login(c, "beta")
    c.post(r["cart_add"], data={"sku": "B-77821", "qty": 10})
    return quote_ref(c.get(r["confirm"], params={"address": "ADDR-BLR-01"}).text)


def test_idempotent_replay_returns_same_order_and_conflicting_reuse_rejected():
    r = ROUTES["beta"]
    c = TestClient(create_portal_app("beta"))
    qref = _prepared_beta(c)
    form = {"po_reference": "PO-IDEMP-0001", "quote_ref": qref, "address_ref": "ADDR-BLR-01"}
    first = c.post(r["place"], data=form)
    second = c.post(r["place"], data=form)
    ref1 = re.search(r"BO-[0-9A-F]{8}", first.text).group(0)
    ref2 = re.search(r"BO-[0-9A-F]{8}", second.text).group(0)
    assert ref1 == ref2
    conflict = c.post(r["place"], data={**form, "quote_ref": "QR-000000000000"})
    assert conflict.status_code == 409 and "PO_REFERENCE_CONFLICT" in conflict.text
    orders = TestClient(create_control_app()).get("/_control/orders", headers=CTRL).json()
    assert orders["count"] == 1


def test_quote_change_is_rejected_atomically():
    r = ROUTES["beta"]
    c = TestClient(create_portal_app("beta"))
    qref = _prepared_beta(c)
    ctrl = TestClient(create_control_app())
    ctrl.post("/_control/mutate", headers=CTRL, json={"supplier": "beta", "products": {"B-77821": {"unit_price": "48900.00"}}})
    resp = c.post(r["place"], data={"po_reference": "PO-CHANGED-01", "quote_ref": qref, "address_ref": "ADDR-BLR-01"})
    assert resp.status_code == 409 and "QUOTE_CHANGED" in resp.text
    assert ctrl.get("/_control/orders", headers=CTRL).json()["count"] == 0


def test_concurrent_submissions_with_same_token_create_one_order():
    r = ROUTES["beta"]
    c = TestClient(create_portal_app("beta"))
    qref = _prepared_beta(c)
    form = {"po_reference": "PO-RACE-00001", "quote_ref": qref, "address_ref": "ADDR-BLR-01"}
    results: list[int] = []

    def go():
        results.append(c.post(r["place"], data=form).status_code)

    threads = [threading.Thread(target=go) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    ctrl = TestClient(create_control_app())
    assert ctrl.get("/_control/orders", headers=CTRL).json()["count"] == 1
    assert ctrl.get("/_control/state", headers=CTRL).json()["products"]["beta:B-77821"]["stock"] == 2


def test_control_api_requires_token():
    assert TestClient(create_control_app()).get("/_control/state").status_code == 401


def test_session_expiry_and_mfa():
    db.reset("session_expiry")
    r = ROUTES["beta"]
    c = TestClient(create_portal_app("beta"))
    login(c, "beta")
    for _ in range(3):
        assert c.get(r["search"]).status_code == 200
    expired = c.get(r["search"], follow_redirects=False)
    assert expired.status_code == 303 and "expired=1" in expired.headers["location"]
    login(c, "beta")
    for _ in range(5):
        assert c.get(r["search"]).status_code == 200
    db.reset("mfa_challenge")
    g = TestClient(create_portal_app("gamma"))
    resp = login(g, "gamma")
    assert resp.headers["location"] == ROUTES["gamma"]["otp"]
    assert g.get(ROUTES["gamma"]["search"], follow_redirects=False).headers["location"] == ROUTES["gamma"]["otp"]
