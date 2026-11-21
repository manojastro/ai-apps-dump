"""Offline tests for Salesforce session handling. No sf CLI, no org needed."""

from __future__ import annotations

import json

import pytest

from sentinel.browser.session import (
    SalesforceAuthError,
    build_storage_state,
    get_salesforce_session,
    parse_sf_display_json,
)


def _display_json(token="00Dxx!token", instance="https://acme.develop.my.salesforce.com") -> str:
    return json.dumps({"status": 0, "result": {"accessToken": token, "instanceUrl": instance}})


def test_parse_valid_display_output():
    s = parse_sf_display_json(_display_json())
    assert s.access_token == "00Dxx!token"
    assert s.frontdoor_url.startswith("https://acme.develop.my.salesforce.com/secur/frontdoor.jsp?sid=")


def test_parse_rejects_non_json():
    with pytest.raises(SalesforceAuthError, match="non-JSON"):
        parse_sf_display_json("not json")


def test_parse_rejects_missing_fields():
    with pytest.raises(SalesforceAuthError, match="accessToken"):
        parse_sf_display_json(json.dumps({"result": {}}))


def test_storage_state_derives_domain_from_url():
    s = parse_sf_display_json(_display_json(instance="https://acme.sandbox.my.salesforce.com"))
    state = build_storage_state(s)
    cookie = state["cookies"][0]
    assert cookie["name"] == "sid" and cookie["value"] == "00Dxx!token"
    assert cookie["domain"] == ".acme.sandbox.my.salesforce.com"


def test_get_session_refuses_production_org(monkeypatch, tmp_path):
    """Even with a valid token, a production instance URL must be refused."""
    import sentinel.browser.session as sess

    fake_sf = tmp_path / "sf.cmd"
    fake_sf.write_text("@echo off\r\necho PLACEHOLDER\r\n")
    monkeypatch.setattr(sess.shutil, "which", lambda _: str(fake_sf))

    class Proc:
        returncode = 0
        stdout = _display_json(instance="https://acme.my.salesforce.com")
        stderr = ""

    monkeypatch.setattr(sess.subprocess, "run", lambda *a, **k: Proc())
    with pytest.raises(SalesforceAuthError, match="production"):
        get_salesforce_session("sentinel-dev")


def test_get_session_clear_error_when_cli_missing(monkeypatch):
    import sentinel.browser.session as sess

    monkeypatch.setattr(sess.shutil, "which", lambda _: None)
    with pytest.raises(SalesforceAuthError, match="not found"):
        get_salesforce_session("sentinel-dev")
