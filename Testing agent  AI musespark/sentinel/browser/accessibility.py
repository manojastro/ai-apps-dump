"""Intent-based browser observation: accessibility tree first, screenshots on failure only.

Why: Lightning Web Components hide internals behind Shadow DOM and rotate
dynamic IDs, so CSS/XPath locators rot. The accessibility tree exposes intent
(role + accessible name, e.g. button "Save"), which survives all three
Salesforce breakage modes. Screenshots cost tokens — capture them only when a
step fails, for the bug report.

Rules enforced here:
- No CSS selectors or XPath strings anywhere in this module.
- Never `sleep()` — every wait is `expect(...).to_be_visible(timeout=...)`.
- Every step records console errors + failed network calls, pass or fail
  (the Verifier and bug report need them either way).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("sentinel.browser")

DEFAULT_STEP_TIMEOUT_MS = 15_000


@dataclass
class PageErrorCollector:
    """Listener bundle attached to a Page; drained per step into StepResult."""

    console_errors: list[str] = field(default_factory=list)
    failed_requests: list[dict] = field(default_factory=list)

    def attach(self, page) -> "PageErrorCollector":
        page.on("console", self._on_console)
        page.on("response", self._on_response)
        page.on("requestfailed", self._on_request_failed)
        return self

    def _on_console(self, msg) -> None:
        try:
            if msg.type == "error":
                self.console_errors.append(msg.text[:1000])
        except Exception:  # listeners must never break the run
            logger.debug("console listener swallowed an error", exc_info=True)

    def _on_response(self, response) -> None:
        try:
            if response.status >= 400:
                self.failed_requests.append(
                    {"url": response.url[:500], "method": response.request.method, "status": response.status}
                )
        except Exception:
            logger.debug("response listener swallowed an error", exc_info=True)

    def _on_request_failed(self, request) -> None:
        try:
            self.failed_requests.append(
                {"url": request.url[:500], "method": request.method, "status": None,
                 "error": (request.failure or "")[:200]}
            )
        except Exception:
            logger.debug("requestfailed listener swallowed an error", exc_info=True)

    def drain(self) -> tuple[list[str], list[dict]]:
        errors, failed = self.console_errors, self.failed_requests
        self.console_errors, self.failed_requests = [], []
        return errors, failed


def _str_val(node: dict, key: str) -> str:
    val = node.get(key, {})
    if isinstance(val, dict):
        return str(val.get("value", "") or "")
    return str(val or "")


def _render_cdp_node(node_id: str, nodes: dict, depth: int, out: list[str]) -> None:
    node = nodes.get(node_id)
    if node is None:
        return
    if node.get("ignored"):
        for child_id in node.get("childIds", []) or []:
            _render_cdp_node(child_id, nodes, depth, out)
        return
    role, name = _str_val(node, "role"), _str_val(node, "name")
    if role in {"StaticText", "generic", "none"} and not name:
        for child_id in node.get("childIds", []) or []:
            _render_cdp_node(child_id, nodes, depth, out)
        return
    out.append("  " * depth + f"- {role} {name!r}".strip())
    for child_id in node.get("childIds", []) or []:
        _render_cdp_node(child_id, nodes, min(depth + 1, 8), out)


def snapshot_accessibility(page, max_chars: int = 6000) -> str:
    """Compact text snapshot of the a11y tree — the agent's primary observation.

    Python Playwright exposes no page.accessibility API, so we use the Chrome
    DevTools Protocol directly (Accessibility.getFullAXTree). Works in headless
    shell; no selectors involved.
    """
    cdp = page.context.new_cdp_session(page)
    try:
        tree = cdp.send("Accessibility.getFullAXTree", {"depth": 12})
    finally:
        try:
            cdp.detach()
        except Exception:
            pass
    nodes = {n["nodeId"]: n for n in tree.get("nodes", [])}
    if not nodes:
        return "(empty accessibility tree)"
    child_ids: set[str] = set()
    for n in nodes.values():
        child_ids.update(n.get("childIds", []) or [])
    roots = [nid for nid in nodes if nid not in child_ids] or list(nodes)[:1]
    lines: list[str] = []
    for root in roots:
        _render_cdp_node(root, nodes, 0, lines)
    text = "\n".join(lines) or "(empty accessibility tree)"
    if len(text) > max_chars:
        text = text[:max_chars] + "\n…(truncated)"
    return text


def locate(page, role: str, name: str):
    """Locate by intent (ARIA role + accessible name). No selectors, ever."""
    return page.get_by_role(role, name=name)  # type: ignore[arg-type]


def wait_visible(locator, timeout_ms: int = DEFAULT_STEP_TIMEOUT_MS) -> None:
    """Wait on a condition. Raises on timeout — callers record it as step failure."""
    from playwright.sync_api import expect

    expect(locator).to_be_visible(timeout=timeout_ms)
