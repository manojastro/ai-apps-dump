"""Default tool registry wiring agents and services into typed tools."""
from __future__ import annotations

from backend.app.agents.candidate_evaluation import CandidateEvaluationAgent
from backend.app.agents.candidate_training import CandidateTrainingAgent
from backend.app.agents.monitoring import ModelMonitoringAgent
from backend.app.agents.shadow_canary import ShadowCanaryAgent
from backend.app.services.approval import promotion_service
from backend.app.schemas.dto import (
    CanaryEvalInput,
    CanaryEvalOutput,
    EvaluateCandidateInput,
    EvaluateCandidateOutput,
    EvaluateWindowInput,
    EvaluateWindowOutput,
    PromoteModelInput,
    PromoteModelOutput,
    RollbackModelInput,
    RollbackModelOutput,
    ShadowCompareInput,
    ShadowCompareOutput,
    TrainCandidateInput,
    TrainCandidateOutput,
)
from backend.app.tools.base import Tool, ToolPermission, ToolRegistry


def _evaluate_window(session, payload: EvaluateWindowInput) -> EvaluateWindowOutput:
    return ModelMonitoringAgent().evaluate_window(session, payload.window_id)


def _train_candidate(session, payload: TrainCandidateInput) -> TrainCandidateOutput:
    return CandidateTrainingAgent().train(
        session,
        source_window_id=payload.source_window_id,
        seed=payload.seed,
        n_samples=payload.n_samples,
        inject_bad=payload.inject_bad,
        bad_n_samples=payload.bad_n_samples,
        bad_label_noise=payload.bad_label_noise,
    )


def _evaluate_candidate(session, payload: EvaluateCandidateInput) -> EvaluateCandidateOutput:
    return CandidateEvaluationAgent().evaluate(session, payload.version)


def _shadow_compare(session, payload: ShadowCompareInput) -> ShadowCompareOutput:
    result = ShadowCanaryAgent().shadow_compare(
        session, payload.version, payload.n_requests, payload.seed
    )
    return ShadowCompareOutput(**result)


def _canary_eval(session, payload: CanaryEvalInput) -> CanaryEvalOutput:
    result = ShadowCanaryAgent().canary_evaluate(
        session, payload.version, payload.n_requests, payload.seed
    )
    return CanaryEvalOutput(**result)


def _promote_model(session, payload: PromoteModelInput) -> PromoteModelOutput:
    from backend.app.repositories.registry_repo import RegistryRepository

    promotion = promotion_service.approve(
        session, payload.promotion_id, payload.approver, payload.comment
    )
    champion = RegistryRepository.current_champion(session)
    return PromoteModelOutput(
        promotion_id=promotion.id,
        state=promotion.state,
        champion_version=champion.version if champion else "",
    )


def _rollback_model(session, payload: RollbackModelInput) -> RollbackModelOutput:
    result = promotion_service.rollback(session, payload.target_version, payload.reason)
    return RollbackModelOutput(**result)


def build_default_registry() -> ToolRegistry:
    """Construct the standard seven-tool registry."""
    registry = ToolRegistry()
    registry.register(
        Tool(
            name="evaluate_window_tool",
            description="Run the full monitoring agent suite on a submitted window",
            permission=ToolPermission.SAFE,
            timeout_s=120.0,
            input_model=EvaluateWindowInput,
            output_model=EvaluateWindowOutput,
            handler=_evaluate_window,
            tags=["monitoring"],
        )
    )
    registry.register(
        Tool(
            name="train_candidate_tool",
            description="Train a challenger GradientBoosting candidate",
            permission=ToolPermission.MUTATING,
            timeout_s=300.0,
            input_model=TrainCandidateInput,
            output_model=TrainCandidateOutput,
            handler=_train_candidate,
            tags=["training"],
        )
    )
    registry.register(
        Tool(
            name="evaluate_candidate_tool",
            description="Score a candidate against deployment thresholds and the champion",
            permission=ToolPermission.SAFE,
            timeout_s=180.0,
            input_model=EvaluateCandidateInput,
            output_model=EvaluateCandidateOutput,
            handler=_evaluate_candidate,
            tags=["evaluation"],
        )
    )
    registry.register(
        Tool(
            name="shadow_compare_tool",
            description="Replay identical requests through champion and challenger",
            permission=ToolPermission.SAFE,
            timeout_s=120.0,
            input_model=ShadowCompareInput,
            output_model=ShadowCompareOutput,
            handler=_shadow_compare,
            tags=["shadow"],
        )
    )
    registry.register(
        Tool(
            name="canary_eval_tool",
            description="Evaluate candidate slices before promotion",
            permission=ToolPermission.SAFE,
            timeout_s=120.0,
            input_model=CanaryEvalInput,
            output_model=CanaryEvalOutput,
            handler=_canary_eval,
            tags=["canary"],
        )
    )
    registry.register(
        Tool(
            name="promote_model_tool",
            description="Execute an approval-gated promotion of a validated candidate",
            permission=ToolPermission.MUTATING,
            timeout_s=180.0,
            input_model=PromoteModelInput,
            output_model=PromoteModelOutput,
            handler=_promote_model,
            tags=["deployment", "approval-gated"],
        )
    )
    registry.register(
        Tool(
            name="rollback_model_tool",
            description="Restore a previous champion version",
            permission=ToolPermission.MUTATING,
            timeout_s=60.0,
            input_model=RollbackModelInput,
            output_model=RollbackModelOutput,
            handler=_rollback_model,
            tags=["deployment"],
        )
    )
    return registry


_default_registry: ToolRegistry | None = None


def get_default_registry() -> ToolRegistry:
    """Process-wide default tool registry singleton."""
    global _default_registry
    if _default_registry is None:
        _default_registry = build_default_registry()
    return _default_registry
