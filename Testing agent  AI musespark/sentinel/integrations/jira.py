"""Minimal Jira Cloud client on the standard library (no new dependencies).

Why stdlib urllib instead of `jira`/`httpx`: the project stack forbids new
dependencies without approval, and three endpoints are all the Reporter
needs — search, create, comment. Every call carries a timeout; auth and HTTP
failures raise JiraError (never silent None).

Jira Cloud specifics handled here:
- Basic auth with email:api_token (Cloud), documented where Bearer fits.
- Description/comment bodies in Atlassian Document Format (ADF) — Cloud
  rejects plain-text description payloads.
- Search via POST /rest/api/3/search/jql (GET /search was removed on Cloud).

Verified against a local HTTP stub in tests/test_jira.py (payload shape,
auth header, timeout enforcement). Live instance verification is Phase 5.
"""

from __future__ import annotations

import base64
import json
import logging
import urllib.error
import urllib.request

from sentinel.models import BugReport

logger = logging.getLogger("sentinel.jira")

DEFAULT_TIMEOUT_SECS = 30


class JiraError(RuntimeError):
    pass


def _adf_paragraph(text: str) -> dict:
    return {"type": "paragraph", "content": [{"type": "text", "text": text[:2000]}]}


def report_to_adf(report: BugReport) -> dict:
    """Full bug report as an ADF document: steps, expected/actual, evidence."""
    content = [
        _adf_paragraph(f"Expected: {report.expected}"),
        _adf_paragraph(f"Actual: {report.actual}"),
        _adf_paragraph(f"Environment: {report.environment}"),
        _adf_paragraph(f"Test data: {report.test_data_used or '(not recorded)'}"),
        {"type": "bulletList", "content": [
            {"type": "listItem", "content": [_adf_paragraph(s)]} for s in report.steps_to_reproduce
        ]} if report.steps_to_reproduce else _adf_paragraph("Steps: (none recorded)"),
        _adf_paragraph("Console errors: " + (" | ".join(report.console_log[:10]) or "(none)")),
        _adf_paragraph("Failed network calls: " + (
            " | ".join(f"{c.method} {c.url} -> {c.status}" for c in report.network_log[:10]) or "(none)")),
    ]
    if report.video_path:
        content.append(_adf_paragraph(f"Video: {report.video_path}"))
    return {"type": "doc", "version": 1, "content": content}


def _escape_jql(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


class JiraClient:
    def __init__(self, base_url: str, email: str, api_token: str, timeout_secs: int = DEFAULT_TIMEOUT_SECS) -> None:
        if not base_url or not email or not api_token:
            raise JiraError("JiraClient needs base_url, email, and api_token (see .env.example JIRA_*).")
        self.base_url = base_url.rstrip("/")
        creds = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        self._auth = f"Basic {creds}"
        self.timeout_secs = timeout_secs

    def _call(self, method: str, path: str, payload: dict | None = None) -> dict:
        url = self.base_url + path
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            url, data=data, method=method,
            headers={"Authorization": self._auth, "Content-Type": "application/json",
                     "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_secs) as resp:
                body = resp.read().decode()
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode()[:500]
            raise JiraError(f"Jira {method} {path} -> HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise JiraError(f"Jira {method} {path} unreachable: {exc.reason}") from exc
        except TimeoutError as exc:
            raise JiraError(f"Jira {method} {path} timed out after {self.timeout_secs}s") from exc
        except json.JSONDecodeError as exc:
            raise JiraError(f"Jira {method} {path} returned non-JSON") from exc

    def search_issues(self, jql: str, max_results: int = 25) -> list[dict]:
        resp = self._call("POST", "/rest/api/3/search/jql",
                          {"jql": jql, "maxResults": max_results, "fields": ["summary"]})
        return [{"key": i.get("key", ""),
                 "title": (i.get("fields", {}) or {}).get("summary", ""),
                 "signature": ""} for i in resp.get("issues", [])]

    def search_by_title(self, project: str, title: str) -> list[dict]:
        jql = f'project = "{_escape_jql(project)}" AND text ~ "{_escape_jql(title)}" ORDER BY updated DESC'
        return self.search_issues(jql)

    def create_issue(self, project: str, report: BugReport, issue_type: str = "Bug") -> str:
        resp = self._call("POST", "/rest/api/3/issue", {
            "fields": {"project": {"key": project},
                       "summary": report.title[:255],
                       "description": report_to_adf(report),
                       "issuetype": {"name": issue_type}},
        })
        key = resp.get("key", "")
        if not key:
            raise JiraError(f"Jira create_issue returned no key: {resp}")
        logger.info("Created Jira issue %s", key)
        return key

    def add_comment(self, issue_key: str, text: str) -> None:
        adf = {"type": "doc", "version": 1, "content": [_adf_paragraph(text)]}
        self._call("POST", f"/rest/api/3/issue/{issue_key}/comment", {"body": adf})
        logger.info("Commented on Jira issue %s", issue_key)


def file_issue(*args, **kwargs):
    raise NotImplementedError(
        "Live filing runs in Phase 5 against a real instance (client above is "
        "stub-verified). Until then: assemble_bug_report + find_duplicate."
    )
