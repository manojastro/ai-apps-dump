"""Typed agent boundaries for Sentinel.

Every agent input/output is a Pydantic v2 model defined here.
No agent may pass untyped dicts across boundaries — this is what makes
the LangGraph state machine debuggable and the eval harness measurable.

New to Pydantic? Each class below is a schema + validator: constructing
e.g. ``TestCase(...)`` with bad data raises ``ValidationError`` immediately,
so schema bugs surface at the agent that produced them, not downstream.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


TestType = Literal["happy", "negative", "boundary", "edge"]
Priority = Literal["high", "medium", "low"]
VerdictLabel = Literal["pass", "real_bug", "flaky", "blocked"]
RecordedActionKind = Literal["click", "fill", "expect_title", "expect_text"]


class RecordedAction(BaseModel):
    """One deterministic replay step: Explorer evidence -> TestWriter template.

    The prose-to-structure translation (TestCase steps -> these actions) is the
    LLM step and needs the model key. Everything downstream of this contract —
    rendering, validation, execution — is deterministic and tested offline.
    """

    kind: RecordedActionKind
    role: str = ""
    name: str = ""
    value: str = ""


class UserStory(BaseModel):
    """Plain-English requirement the Planner turns into test cases."""

    id: str = Field(..., min_length=1, description="Stable story identifier, e.g. US-LEAD-001")
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    acceptance_criteria: list[str] = Field(default_factory=list)


class TestCase(BaseModel):
    """One executable test derived from a UserStory."""

    id: str = Field(..., min_length=1, description="E.g. TC-LEAD-001-HAPPY-1")
    story_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    type: TestType
    steps: list[str] = Field(..., min_length=1, description="Ordered human-readable steps")
    expected_result: str = Field(..., min_length=1)
    priority: Priority = "medium"
    reasoning: str = Field(
        default="",
        description="Why this case was selected (required when risk-based diff filtering is used).",
    )


class FailedNetworkCall(BaseModel):
    url: str
    method: str = "GET"
    status: int | None = None
    error: str = ""


class StepResult(BaseModel):
    step_index: int = Field(..., ge=0)
    action: str = Field(..., min_length=1, description="What the agent tried, e.g. 'click Save opportunity'")
    target_description: str = Field(
        ..., min_length=1, description="Intent + ARIA role, never a CSS selector or XPath."
    )
    succeeded: bool
    error: str = ""
    screenshot_path: str | None = None
    console_errors: list[str] = Field(default_factory=list)
    failed_network_calls: list[FailedNetworkCall] = Field(default_factory=list)


class RunTrace(BaseModel):
    """Full record of one Explorer execution of one TestCase."""

    test_case_id: str
    run_number: int = Field(..., ge=1)
    step_results: list[StepResult] = Field(default_factory=list)
    final_state: str = Field(default="", description="pass | fail + short summary")
    duration_ms: int = Field(default=0, ge=0)
    tokens_used: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0.0)


class Verdict(BaseModel):
    """Verifier decision after up to 3 runs."""

    test_case_id: str
    classification: VerdictLabel
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_summary: str = Field(..., min_length=1, description="Logged reasoning for the verdict.")
    runs_attempted: int = Field(..., ge=1, le=3)
    runs_failed: int = Field(..., ge=0, le=3)


class BugReport(BaseModel):
    """Developer-ready report. Must answer every fix question with no follow-ups."""

    title: str = Field(..., min_length=1)
    steps_to_reproduce: list[str] = Field(..., min_length=1)
    expected: str = Field(..., min_length=1)
    actual: str = Field(..., min_length=1)
    environment: str = Field(..., min_length=1, description="Browser, viewport, org type, release.")
    video_path: str | None = None
    console_log: list[str] = Field(default_factory=list)
    network_log: list[FailedNetworkCall] = Field(default_factory=list)
    test_data_used: str = Field(default="", description="Exact prefixed disposable records used.")
    suspected_duplicate_of: str | None = Field(
        default=None, description="Existing Jira key if Reporter found a likely duplicate."
    )
