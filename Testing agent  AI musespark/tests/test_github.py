"""GitHub client tests against a local HTTP stub (no token, no repo needed)."""

from __future__ import annotations

import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from sentinel.integrations.github import GitHubClient, GitHubError, open_pr


class _Stub(BaseHTTPRequestHandler):
    requests: list[dict] = []

    def log_message(self, *args):
        pass

    def _send(self, code: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        length = 0
        _Stub.requests.append({"method": "GET", "path": self.path,
                               "auth": self.headers.get("Authorization"), "body": {}})
        if self.path == "/repos/acme/sentinel":
            self._send(200, {"default_branch": "main"})
        elif self.path == "/repos/acme/sentinel/git/ref/heads/main":
            self._send(200, {"object": {"sha": "abc123"}})
        else:
            self._send(404, {"message": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        _Stub.requests.append({"method": "POST", "path": self.path,
                               "auth": self.headers.get("Authorization"),
                               "body": json.loads(raw.decode())})
        if self.path == "/repos/acme/sentinel/git/refs":
            self._send(201, {"ref": "refs/heads/sentinel/x"})
        elif self.path == "/repos/acme/sentinel/pulls":
            body = json.loads(raw.decode())
            if not body.get("head") or not body.get("base"):
                self._send(422, {"message": "validation failed: head and base required"})
            else:
                self._send(201, {"html_url": "https://github.com/acme/sentinel/pull/7"})
        else:
            self._send(422, {"message": "validation failed"})

    def do_PUT(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        _Stub.requests.append({"method": "PUT", "path": self.path,
                               "auth": self.headers.get("Authorization"),
                               "body": json.loads(raw.decode())})
        self._send(201, {"content": {"sha": "def456"}})


@pytest.fixture()
def stub():
    _Stub.requests = []
    server = HTTPServer(("127.0.0.1", 0), _Stub)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def _client(stub: str) -> GitHubClient:
    return GitHubClient(token="ghp_test", api_base=stub)


def test_full_proposal_flow(stub):
    url = _client(stub).propose_regression_test(
        repo="acme/sentinel", branch="sentinel/tc-1", path="tests/test_regression_tc_1.py",
        test_code="print('regression')", title="test: regression for SENT-42", bug_key="SENT-42")
    assert url == "https://github.com/acme/sentinel/pull/7"

    by_path = {(r["method"], r["path"]): r for r in _Stub.requests}
    # Branch created from resolved default-branch SHA, not a guessed "main".
    ref_req = by_path[("POST", "/repos/acme/sentinel/git/refs")]
    assert ref_req["body"] == {"ref": "refs/heads/sentinel/tc-1", "sha": "abc123"}
    # File content base64-encoded on the new branch.
    put_req = by_path[("PUT", "/repos/acme/sentinel/contents/tests/test_regression_tc_1.py")]
    assert base64.b64decode(put_req["body"]["content"]).decode() == "print('regression')"
    assert put_req["body"]["branch"] == "sentinel/tc-1"
    # PR targets the resolved default branch and carries the bug key.
    pr_req = by_path[("POST", "/repos/acme/sentinel/pulls")]
    assert pr_req["body"]["head"] == "sentinel/tc-1" and pr_req["body"]["base"] == "main"
    assert "SENT-42" in pr_req["body"]["body"]
    # Every request authenticated.
    assert all(r["auth"] == "Bearer ghp_test" for r in _Stub.requests)


def test_api_error_mapped(stub):
    with pytest.raises(GitHubError, match="HTTP 422"):
        _client(stub)._call("POST", "/repos/acme/sentinel/pulls", {"title": "x"})


def test_missing_token_rejected():
    with pytest.raises(GitHubError, match="needs a token"):
        GitHubClient(token="")


def test_live_path_still_raises():
    with pytest.raises(NotImplementedError):
        open_pr()
