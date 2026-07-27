from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ai_platform.research.liquidations.contracts import LiquidationEvent
from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import (
    BotMode,
    CandidateAction,
    CandidateScore,
    DataFreshnessEvidence,
    DcaPlan,
    LiquidationHistorySnapshot,
    LiquidationSourceState,
    MarketContextSnapshot,
    ShadowDecisionEvidence,
    ShadowStatus,
    StrategyHypothesis,
    WickHunterTradeIntent,
)
from ai_platform.wickhunter.features import build_liquidation_features
from ai_platform.wickhunter.parameters import (
    WickHunterParameterBounds,
    WickHunterParameters,
    validate_parameters,
)
from ai_platform.wickhunter.risk import (
    WickHunterRiskContext,
    WickHunterRiskLimits,
    evaluate_trade_intent,
)
from ai_platform.wickhunter.scoring import CandidateScorer
from ai_platform.wickhunter.strategy import STRATEGY_VERSION, SignalMemory, generate_candidate
from ai_platform.wickhunter.universe import DynamicUniverseSnapshot


SHADOW_EVIDENCE_SCHEMA = "wickhunter-shadow-decision-v1"
TRADE_INTENT_SCHEMA = "wickhunter-trade-intent-v1"


@dataclass(frozen=True, slots=True)
class ShadowDecisionRequest:
    bot_instance: str
    mode: BotMode
    events: tuple[LiquidationEvent, ...]
    market: MarketContextSnapshot
    history: LiquidationHistorySnapshot
    source_states: tuple[LiquidationSourceState, ...]
    universe: DynamicUniverseSnapshot
    parameters: WickHunterParameters
    parameter_bounds: WickHunterParameterBounds
    hypothesis: StrategyHypothesis
    scorer: CandidateScorer
    signal_memory: SignalMemory
    risk_limits: WickHunterRiskLimits
    risk_context: WickHunterRiskContext
    dataset_hash: str
    code_sha: str


def _freshness(
    *,
    market: MarketContextSnapshot,
    source_states: tuple[LiquidationSourceState, ...],
    latest_liquidation_received_at_ms: int,
) -> DataFreshnessEvidence:
    metric_by_name = {metric.name: metric for metric in market.metrics}
    open_interest = metric_by_name.get("open_interest_usd")
    funding = metric_by_name.get("funding_rate")
    return DataFreshnessEvidence(
        liquidation_age_ms=market.decision_timestamp_ms - latest_liquidation_received_at_ms,
        candle_age_ms=market.decision_timestamp_ms - market.completed_candle_close_ms,
        open_interest_age_ms=(
            None
            if open_interest is None
            else market.decision_timestamp_ms - open_interest.available_at_ms
        ),
        funding_age_ms=(
            None if funding is None else market.decision_timestamp_ms - funding.available_at_ms
        ),
        source_health=tuple(sorted((state.source, state.health) for state in source_states)),
    )


def _shadow_id(payload: object) -> str:
    return canonical_sha256({"schema_version": SHADOW_EVIDENCE_SCHEMA, "payload": payload})


def evaluate_shadow_decision(request: ShadowDecisionRequest) -> ShadowDecisionEvidence:
    if request.mode is BotMode.LIVE_BLOCKED:
        raise ValueError("live mode is not authorized by the WickHunter shadow runtime")
    validate_parameters(request.parameters, request.parameter_bounds)
    if not request.universe.includes_symbol(request.market.symbol):
        shadow_id = _shadow_id(
            {
                "status": ShadowStatus.NO_CANDIDATE.value,
                "symbol": request.market.symbol,
                "universe_snapshot_hash": request.universe.snapshot_hash,
                "decision_timestamp_ms": request.market.decision_timestamp_ms,
                "reason": "symbol_not_in_dynamic_universe",
            }
        )
        return ShadowDecisionEvidence(
            schema_version=SHADOW_EVIDENCE_SCHEMA,
            shadow_decision_id=shadow_id,
            status=ShadowStatus.NO_CANDIDATE,
            mode=request.mode,
            universe_snapshot_hash=request.universe.snapshot_hash,
            feature_hash=None,
            candidate=None,
            score=None,
            trade_intent=None,
            risk_decision=None,
            created_at_ms=request.market.decision_timestamp_ms,
        )

    features = build_liquidation_features(
        events=request.events,
        market=request.market,
        history=request.history,
        source_states=request.source_states,
        burst_window_ms=request.parameters.burst_window_ms,
    )
    candidate = generate_candidate(
        features=features,
        parameters=request.parameters,
        hypothesis=request.hypothesis,
        memory=request.signal_memory,
    )
    if candidate.action is CandidateAction.IGNORE:
        shadow_id = _shadow_id(
            {
                "status": ShadowStatus.NO_CANDIDATE.value,
                "candidate_id": candidate.candidate_id,
                "universe_snapshot_hash": request.universe.snapshot_hash,
            }
        )
        return ShadowDecisionEvidence(
            schema_version=SHADOW_EVIDENCE_SCHEMA,
            shadow_decision_id=shadow_id,
            status=ShadowStatus.NO_CANDIDATE,
            mode=request.mode,
            universe_snapshot_hash=request.universe.snapshot_hash,
            feature_hash=features.feature_hash,
            candidate=candidate,
            score=None,
            trade_intent=None,
            risk_decision=None,
            created_at_ms=request.market.decision_timestamp_ms,
        )

    score: CandidateScore = request.scorer.score(
        candidate=candidate,
        features=features,
        parameters=request.parameters,
    )
    if score.feature_hash != features.feature_hash or score.candidate_id != candidate.candidate_id:
        raise ValueError("score identity does not match candidate and feature evidence")
    requested_base_risk = (
        request.parameters.base_risk_ratio * score.bounded_risk_multiplier
    ).quantize(Decimal("0.00000001"))
    dca_total_risk = (
        request.parameters.dca_total_risk_ratio * score.bounded_risk_multiplier
    ).quantize(Decimal("0.00000001"))
    dca_plan = DcaPlan(
        enabled=request.parameters.dca_enabled,
        maximum_levels=request.parameters.dca_levels,
        spacing_ratio=request.parameters.dca_spacing_ratio,
        maximum_total_risk_ratio=dca_total_risk,
    )
    latest_received = max(
        aggregate.latest_received_at_ms for aggregate in features.source_aggregates
    )
    freshness = _freshness(
        market=request.market,
        source_states=request.source_states,
        latest_liquidation_received_at_ms=latest_received,
    )
    model_version = score.model_version
    model_hash = score.model_hash
    intent_payload = {
        "bot_instance": request.bot_instance,
        "strategy_version": STRATEGY_VERSION,
        "model_version": model_version,
        "parameter_version": request.parameters.parameter_version,
        "symbol": candidate.symbol,
        "side": candidate.side.value if candidate.side is not None else None,
        "decision_timestamp_ms": candidate.decision_timestamp_ms,
        "candidate_id": candidate.candidate_id,
        "score_id": score.score_id,
        "feature_hash": features.feature_hash,
        "dataset_hash": request.dataset_hash,
        "code_sha": request.code_sha,
        "parameter_hash": request.parameters.parameter_hash,
        "mode": request.mode.value,
    }
    intent_id = canonical_sha256(intent_payload)
    if candidate.side is None:
        raise RuntimeError("non-ignored candidate lost its side")
    intent = WickHunterTradeIntent(
        schema_version=TRADE_INTENT_SCHEMA,
        trade_intent_id=intent_id,
        candidate_id=candidate.candidate_id,
        score_id=score.score_id,
        bot_instance=request.bot_instance,
        strategy_version=STRATEGY_VERSION,
        model_version=model_version,
        parameter_version=request.parameters.parameter_version,
        symbol=candidate.symbol,
        side=candidate.side,
        decision_timestamp_ms=candidate.decision_timestamp_ms,
        decision_price=candidate.decision_price,
        candidate_reason=candidate.reason_codes,
        liquidation_evidence_ids=features.input_event_ids,
        feature_hash=features.feature_hash,
        confidence=score.confidence,
        requested_base_risk_ratio=requested_base_risk,
        requested_leverage=request.parameters.leverage,
        take_profit_ratio=request.parameters.take_profit_ratio,
        stop_loss_ratio=request.parameters.stop_loss_ratio,
        dca_plan=dca_plan,
        expiration_timestamp_ms=(
            candidate.decision_timestamp_ms + request.parameters.maximum_event_age_ms
        ),
        freshness=freshness,
        dataset_hash=request.dataset_hash,
        model_hash=model_hash,
        code_sha=request.code_sha,
        parameter_hash=request.parameters.parameter_hash,
        mode=request.mode,
    )
    risk_decision = evaluate_trade_intent(
        intent=intent,
        score=score,
        context=request.risk_context,
        limits=request.risk_limits,
    )
    status = (
        ShadowStatus.SIMULATED_ALLOWED
        if risk_decision.outcome.value == "allow"
        else ShadowStatus.SIMULATED_REJECTED
    )
    shadow_id = _shadow_id(
        {
            "status": status.value,
            "universe_snapshot_hash": request.universe.snapshot_hash,
            "feature_hash": features.feature_hash,
            "candidate_id": candidate.candidate_id,
            "score_id": score.score_id,
            "trade_intent_id": intent.trade_intent_id,
            "risk_decision_id": risk_decision.risk_decision_id,
        }
    )
    return ShadowDecisionEvidence(
        schema_version=SHADOW_EVIDENCE_SCHEMA,
        shadow_decision_id=shadow_id,
        status=status,
        mode=request.mode,
        universe_snapshot_hash=request.universe.snapshot_hash,
        feature_hash=features.feature_hash,
        candidate=candidate,
        score=score,
        trade_intent=intent,
        risk_decision=risk_decision,
        created_at_ms=request.market.decision_timestamp_ms,
    )
