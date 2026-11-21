"""Guardrail helpers re-exported from config (single enforcement point)."""

from sentinel.config import assert_sandbox_or_dev, is_action_blocked, is_domain_allowed

__all__ = ["assert_sandbox_or_dev", "is_action_blocked", "is_domain_allowed"]
