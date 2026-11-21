"""Minimal GitHub client on the standard library (no new dependencies).

PR flow, exactly as the spec requires (agent proposes, human merges):
1. Resolve default branch + its SHA (agent never guesses "main").
2. Create branch sentinel/<test-id> from that SHA.
3. Commit the rendered regression test via Contents API (base64).
4. Open a PR with the bug key in the body. No merge endpoint is wrapped —
   merging stays a human click in the GitHub UI.

Every call carries a timeout; failures raise GitHubError. Verified against a
local HTTP stub in tests/test_github.py. Live delivery needs GITHUB_TOKEN +
GITHUB_REPO (Phase 5 wiring).
"""

from __future__ import annotations

import base64
import json
import logging
import urllib.error
import urllib.request

logger = logging.getLogger("sentinel.github")

DEFAULT_TIMEOUT_SECS = 30


class GitHubError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, token: str, api_base: str = "https://api.github.com",
                 timeout_secs: int = DEFAULT_TIMEOUT_SECS) -> None:
        if not token:
            raise GitHubError("GitHubClient needs a token (GITHUB_TOKEN in .env).")
        self._token = token
        self.api_base = api_base.rstrip("/")
        self.timeout_secs = timeout_secs

    def _call(self, method: str, path: str, payload: dict | None = None,
              expected: tuple[int, ...] = (200, 201)) -> dict:
        url = self.api_base + path
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            url, data=data, method=method,
            headers={"Authorization": f"Bearer {self._token}",
                     "Content-Type": "application/json",
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_secs) as resp:
                if resp.status not in expected:
                    raise GitHubError(f"GitHub {method} {path} -> HTTP {resp.status}")
                body = resp.read().decode()
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            raise GitHubError(f"GitHub {method} {path} -> HTTP {exc.code}: {exc.read().decode()[:500]}") from exc
        except urllib.error.URLError as exc:
            raise GitHubError(f"GitHub {method} {path} unreachable: {exc.reason}") from exc
        except TimeoutError as exc:
            raise GitHubError(f"GitHub {method} {path} timed out after {self.timeout_secs}s") from exc

    def _repo(self, repo: str) -> dict:
        return self._call("GET", f"/repos/{repo}")

    def create_branch(self, repo: str, branch: str) -> str:
        """Create branch from the repo's default-branch SHA. Returns the SHA."""
        info = self._repo(repo)
        default = info.get("default_branch", "")
        if not default:
            raise GitHubError(f"Could not determine default branch for {repo}")
        ref = self._call("GET", f"/repos/{repo}/git/ref/heads/{default}")
        sha = (ref.get("object", {}) or {}).get("sha", "")
        if not sha:
            raise GitHubError(f"Could not resolve SHA of {default} in {repo}")
        self._call("POST", f"/repos/{repo}/git/refs",
                   {"ref": f"refs/heads/{branch}", "sha": sha}, expected=(201,))
        logger.info("Created branch %s from %s@%s", branch, default, sha[:7])
        return sha

    def commit_file(self, repo: str, branch: str, path: str, content: str, message: str) -> str:
        resp = self._call("PUT", f"/repos/{repo}/contents/{path}", {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode(),
            "branch": branch,
        }, expected=(200, 201))
        sha = ((resp.get("content", {}) or {}).get("sha", ""))
        logger.info("Committed %s on %s", path, branch)
        return sha

    def open_pull_request(self, repo: str, branch: str, base: str, title: str, body: str) -> str:
        resp = self._call("POST", f"/repos/{repo}/pulls",
                          {"title": title, "head": branch, "base": base, "body": body,
                           "maintainer_can_modify": False}, expected=(201,))
        url = resp.get("html_url", "")
        if not url:
            raise GitHubError(f"GitHub PR creation returned no URL: {resp}")
        logger.info("Opened PR %s", url)
        return url

    def propose_regression_test(self, repo: str, branch: str, path: str,
                                test_code: str, title: str, bug_key: str) -> str:
        """Full proposal flow: branch -> commit -> PR. Returns the PR URL."""
        info = self._repo(repo)
        base = info.get("default_branch", "")
        self.create_branch(repo, branch)
        self.commit_file(repo, branch, path, test_code, f"test: add regression {path} for {bug_key}")
        return self.open_pull_request(
            repo, branch, base, title,
            f"Sentinel regression test for {bug_key}.\n\nHuman review required — do not auto-merge.\n")


def open_pr(*args, **kwargs):
    raise NotImplementedError(
        "Live PR delivery needs GITHUB_TOKEN + GITHUB_REPO (Phase 5 wiring). "
        "Use GitHubClient.propose_regression_test with the stub-verified client."
    )
