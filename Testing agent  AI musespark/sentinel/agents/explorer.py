"""Explorer: TestCase -> RunTrace (drives the browser by intent).

Offline-verifiable slice (this file): `execute_intent_step` — one
role+name interaction recorded as a StepResult, with guardrails enforced in
code. The LLM-driven orchestration (deciding *which* intent to attempt from
an a11y snapshot) needs the model key and lands next; `run_test_case`
raises until then. No fake runs.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from sentinel.browser.accessibility import (
    DEFAULT_STEP_TIMEOUT_MS,
    PageErrorCollector,
    locate,
    wait_visible,
)
from sentinel.config import is_action_blocked
from sentinel.models import FailedNetworkCall, StepResult

logger = logging.getLogger("sentinel.explorer")


def execute_intent_step(
    page,
    collector: PageErrorCollector,
    *,
    step_index: int,
    action: str,
    role: str,
    name: str,
    value: str = "",
    timeout_ms: int = DEFAULT_STEP_TIMEOUT_MS,
    screenshot_dir: str | Path | None = None,
) -> StepResult:
    """Perform one click/fill located purely by ARIA role + accessible name.

    - Refuses blocked irreversible actions even if the test case asks.
    - Waits on visibility conditions, never sleep().
    - Screenshots only on failure. Console errors + failed network calls are
      recorded whether or not the step passed.
    """
    target = f'{action} {role} "{name}"'
    if is_action_blocked(f"{action} {name}"):
        return StepResult(
            step_index=step_index, action=action, target_description=target,
            succeeded=False, error=f"Refused blocked action: {target}",
        )
    try:
        locator = locate(page, role, name)
        wait_visible(locator.first, timeout_ms)
        if action == "click":
            locator.first.click(timeout=timeout_ms)
        elif action == "fill":
            locator.first.fill(value, timeout=timeout_ms)
        else:
            return StepResult(
                step_index=step_index, action=action, target_description=target,
                succeeded=False, error=f"Unknown action {action!r} (want click|fill)",
            )
        succeeded, error, shot = True, "", None
    except Exception as exc:
        succeeded, error = False, f"{type(exc).__name__}: {str(exc)[:500]}"
        shot = None
        if screenshot_dir is not None:
            try:
                path = Path(screenshot_dir) / f"step_{step_index}.png"
                path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(path))
                shot = str(path)
            except Exception as shot_exc:
                logger.warning("Screenshot failed: %s", shot_exc)
    console_errors, failed = collector.drain()
    return StepResult(
        step_index=step_index, action=action, target_description=target,
        succeeded=succeeded, error=error, screenshot_path=shot,
        console_errors=console_errors,
        failed_network_calls=[FailedNetworkCall(url=f["url"], method=f["method"], status=f["status"]) for f in failed],
    )


def run_test_case(*args, **kwargs):
    raise NotImplementedError(
        "Explorer orchestration needs the model key + live org (Phase 2 acceptance). "
        "Use execute_intent_step for single intent-driven steps."
    )
