from __future__ import annotations

from collections import Counter

from .schemas import AgentTrace, Detection, Severity, StepKind, VerifiedOutcome


EXPECTED_TOOL_BY_TASK = {"backup": {"backup_create", "backup_verify", "backup_status"}}
SAFE_TOOLS = {"backup_create", "backup_verify", "backup_status", "retrieve_backup_policy", "retrieve_entire_archive_catalog"}
TOOL_REQUIRED_ARGUMENTS = {
    "backup_create": {"source", "destination"},
    "backup_verify": {"artifact"},
    "backup_status": {"job_id"},
    "retrieve_backup_policy": {"collection"},
}


class TraceDetector:
    def detect(self, trace: AgentTrace, verified: VerifiedOutcome) -> list[Detection]:
        findings: list[Detection] = []
        tool_steps = [s for s in trace.steps if s.kind == StepKind.TOOL_CALL]
        signatures = [(s.name, repr(sorted(s.arguments.items()))) for s in tool_steps]
        repeated = [signature for signature, count in Counter(signatures).items() if count >= 3]
        if repeated:
            sequences = [s.sequence for s in tool_steps if (s.name, repr(sorted(s.arguments.items()))) in repeated]
            findings += [self._finding("AGENT_LOOP", "Repeated agent loop", Severity.HIGH, .99, "The same tool and arguments repeated at least three times without progress.", sequences)]
        duplicates = [signature for signature, count in Counter(signatures).items() if count >= 2]
        if duplicates:
            findings += [self._finding("DUPLICATE_CALL", "Duplicate tool calls", Severity.MEDIUM, .98, "Equivalent tool calls were issued more than once.", [s.sequence for s in tool_steps if (s.name, repr(sorted(s.arguments.items()))) in duplicates])]
        wrong = [s for s in tool_steps if s.name not in EXPECTED_TOOL_BY_TASK["backup"]]
        if wrong:
            findings += [self._finding("WRONG_TOOL", "Wrong tool selected", Severity.HIGH, .97, "A tool outside the expected backup tool set was selected.", [s.sequence for s in wrong])]
        unsafe = [s for s in tool_steps if s.name not in SAFE_TOOLS]
        if unsafe:
            findings += [self._finding("UNSAFE_ACTION", "Unsafe action attempt", Severity.CRITICAL, 1.0, "The trace attempted a tool that is not on the execution allow-list.", [s.sequence for s in unsafe])]
        invalid = [s for s in tool_steps if s.name in TOOL_REQUIRED_ARGUMENTS and not TOOL_REQUIRED_ARGUMENTS[s.name].issubset(s.arguments)]
        invalid += [s for s in unsafe if "command" in s.arguments]
        if invalid:
            findings += [self._finding("INVALID_ARGUMENTS", "Invalid or prohibited arguments", Severity.HIGH, 1.0, "Tool arguments failed the registered contract or contained prohibited command input.", [s.sequence for s in invalid])]
        failures = [s for s in trace.steps if not s.success and s.name in SAFE_TOOLS and s.kind == StepKind.TOOL_CALL]
        if failures:
            findings += [self._finding("TOOL_FAILURE", "Tool execution failure", Severity.HIGH, .99, "An allow-listed tool returned an explicit failure.", [s.sequence for s in failures])]
        if trace.claimed_outcome.success and not verified.success:
            findings += [self._finding("HALLUCINATED_SUCCESS", "Hallucinated success", Severity.CRITICAL, 1.0, "The agent claimed success, but independent outcome checks failed.", self._final_sequences(trace))]
            findings += [self._finding("OUTCOME_MISMATCH", "Claimed and verified outcomes differ", Severity.HIGH, 1.0, "; ".join(verified.mismatch_reasons), self._final_sequences(trace))]
        elif not verified.success and not trace.claimed_outcome.success:
            findings += [self._finding("PARTIAL_COMPLETION", "Task was not completed", Severity.MEDIUM, .99, "Expected external outcome requirements were not satisfied.", self._final_sequences(trace))]
        elif not verified.success:
            findings += [self._finding("OUTCOME_MISMATCH", "Claimed and verified outcomes differ", Severity.HIGH, 1.0, "; ".join(verified.mismatch_reasons), self._final_sequences(trace))]
        required_checks = [verified.checks.get("artifact_exists"), verified.checks.get("complete"), verified.checks.get("checksum_verified")]
        if any(required_checks) and not all(required_checks):
            findings += [self._finding("PARTIAL_COMPLETION", "Only part of the outcome contract was satisfied", Severity.HIGH, .99, "At least one required artifact check passed while another failed.", self._final_sequences(trace))]
        if any(s.kind == StepKind.RETRIEVAL and (not s.success or not s.result.get("documents")) for s in trace.steps):
            findings += [self._finding("RETRIEVAL_FAILURE", "Retrieval returned no usable context", Severity.HIGH, .98, "A required retrieval step failed or returned an empty result.", [s.sequence for s in trace.steps if s.kind == StepKind.RETRIEVAL and (not s.success or not s.result.get("documents"))])]
        total_tokens = sum(s.prompt_tokens + s.completion_tokens for s in trace.steps)
        if total_tokens > 20_000 or trace.retry_count >= 4:
            findings += [self._finding("TOKEN_WASTE", "Excessive token or retry usage", Severity.MEDIUM, .96, f"The run consumed {total_tokens:,} tokens with {trace.retry_count} retries.", [])]
        if trace.total_cost_usd > .15:
            findings += [self._finding("COST_SPIKE", "Cost spike", Severity.HIGH, .99, f"Run cost ${trace.total_cost_usd:.4f} exceeded the $0.15 policy budget.", [])]
        if sum(s.latency_ms for s in trace.steps) > 12_000:
            findings += [self._finding("LATENCY_REGRESSION", "Latency regression", Severity.MEDIUM, .98, "End-to-end latency exceeded the 12 second SLO.", [])]
        if trace.context_tokens > 120_000:
            findings += [self._finding("CONTEXT_OVERFLOW", "Context window pressure", Severity.HIGH, .99, f"Context reached {trace.context_tokens:,} tokens and exceeded the 120k guardrail.", [])]
        return sorted(findings, key=lambda f: (self._rank(f.severity), f.code), reverse=True)

    @staticmethod
    def _finding(code: str, title: str, severity: Severity, confidence: float, explanation: str, sequences: list[int]) -> Detection:
        return Detection(code=code, title=title, severity=severity, confidence=confidence, explanation=explanation, evidence_sequences=sequences)

    @staticmethod
    def _final_sequences(trace: AgentTrace) -> list[int]:
        return [s.sequence for s in trace.steps if s.kind == StepKind.FINAL_OUTPUT]

    @staticmethod
    def _rank(severity: Severity) -> int:
        return {Severity.INFO: 0, Severity.LOW: 1, Severity.MEDIUM: 2, Severity.HIGH: 3, Severity.CRITICAL: 4}[severity]
