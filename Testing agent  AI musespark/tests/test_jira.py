"""Jira client tests against a local HTTP stub (no real instance needed).

The stub records every request so we prove: correct endpoints, Basic auth
header, ADF description payload, JQL content — plus HTTP-error mapping and
timeout enforcement.
"""

from __future__ import annotations

import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from sentinel.agents.reporter import assemble_bug_report, deliver, error_signature
from sentinel.integrations.jira import JiraClient, JiraError, report_to_adf
from sentinel.models import RunTrace, StepResult, TestCase, Verdict


class _Stub(BaseHTTPRequestHandler):
    requests: list[dict] = []
    mode: str = "ok"  # ok | create400 | slow

    def log_message(self, *args):
        pass

    def _send(self, code: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        import time

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        type(self).requests.append(
            {"path": self.path, "auth": self.headers.get("Authorization"),
             "body": json.loads(raw.decode())})
        if type(self).mode == "slow":
            time.sleep(3)
            self._send(200, {})
            return
        if self.path == "/rest/api/3/search/jql":
            self._send(200, {"issues": [{"key": "SENT-1", "fields": {"summary": "Old save bug"}}]})
        elif self.path == "/rest/api/3/issue":
            if type(self).mode == "create400":
                self._send(400, {"errorMessages": ["project key XYZ unknown"]})
            else:
                self._send(201, {"key": "SENT-99"})
        elif self.path.endswith("/comment"):
            self._send(201, {"id": "100"})
        else:
            self._send(404, {})


@pytest.fixture()
def stub():
    _Stub.requests = []
    _Stub.mode = "ok"
    server = HTTPServer(("127.0.0.1", 0), _Stub)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def _client(base: str, **kw) -> JiraClient:
    return JiraClient(base_url=base, email="qa@example.com", api_token="tok", **kw)


def test_search_sends_jql_and_auth(stub):
    issues = _client(stub).search_by_title("SENT", "save button")
    assert [i["key"] for i in issues] == ["SENT-1"]
    req = _Stub.requests[0]
    assert req["path"] == "/rest/api/3/search/jql"
    assert req["auth"] == "Basic " + base64.b64encode(b"qa@example.com:tok").decode()
    assert "SENT" in req["body"]["jql"] and "save button" in req["body"]["jql"]


def test_create_sends_adf_description(stub):
    report = _sample_report()
    key = _client(stub).create_issue("SENT", report)
    assert key == "SENT-99"
    body = _Stub.requests[0]["body"]
    assert body["fields"]["project"] == {"key": "SENT"}
    assert body["fields"]["summary"].startswith("[TC-")
    assert body["fields"]["description"]["type"] == "doc"  # ADF, not plain text


def test_comment_hits_issue_endpoint(stub):
    _client(stub).add_comment("SENT-1", "re-observed")
    req = _Stub.requests[0]
    assert req["path"] == "/rest/api/3/issue/SENT-1/comment"
    assert "re-observed" in json.dumps(req["body"])


def test_http_error_mapped(stub):
    _Stub.mode = "create400"
    with pytest.raises(JiraError, match="HTTP 400.*XYZ unknown"):
        _client(stub).create_issue("XYZ", _sample_report())


def test_timeout_enforced(stub):
    _Stub.mode = "slow"
    with pytest.raises(JiraError, match="timed out"):
        _client(stub, timeout_secs=1).search_by_title("SENT", "x")


def test_missing_credentials_rejected():
    with pytest.raises(JiraError, match="needs base_url"):
        JiraClient(base_url="", email="", api_token="")


def test_deliver_creates_when_novel():
    calls: list[tuple] = []
    key, action = deliver(
        _sample_report(), signature="unmatched-signature", project="SENT",
        search_fn=lambda p, t: calls.append(("search", p)) or [],
        create_fn=lambda p, r: calls.append(("create", p)) or "SENT-5",
        comment_fn=lambda k, t: calls.append(("comment", k)),
    )
    assert (key, action) == ("SENT-5", "created")
    assert ("comment", "SENT-5") not in calls


def test_deliver_comments_on_duplicate():
    report = _sample_report()
    sig = "click button | save did nothing"
    key, action = deliver(
        report, signature=sig, project="SENT",
        search_fn=lambda p, t: [{"key": "SENT-3", "title": report.title, "signature": sig}],
        create_fn=lambda p, r: (_ for _ in ()).throw(AssertionError("must not create on duplicate")),
        comment_fn=lambda k, t: None,
    )
    assert (key, action) == ("SENT-3", "commented")
    assert report.suspected_duplicate_of == "SENT-3"


def _sample_report():
    case = TestCase(id="TC-LEAD-001-HAPPY-1", story_id="US-LEAD-001", title="Happy path",
                    type="happy", steps=["Create TEST- lead"], expected_result="Saved")
    trace = RunTrace(test_case_id=case.id, run_number=1, final_state="fail",
                     step_results=[StepResult(step_index=0, action="click",
                                             target_description='click button "Save"',
                                             succeeded=False, error="Save did nothing")])
    verdict = Verdict(test_case_id=case.id, classification="real_bug", confidence=0.95,
                      evidence_summary="3/3 failed.", runs_attempted=3, runs_failed=3)
    return assemble_bug_report(verdict=verdict, test_case=case, traces=[trace],
                               environment="dev", test_data_used="TEST-1")
